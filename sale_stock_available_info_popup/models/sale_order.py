# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    immediately_usable_qty_today = fields.Float(
        compute="_compute_immediately_usable_qty_today"
    )

    @api.depends(
        "product_id",
        "product_uom_qty",
        "product_uom_id",
        "scheduled_date",
        "order_id.date_order",
        "warehouse_id",
    )
    def _compute_immediately_usable_qty_today(self):
        self.immediately_usable_qty_today = False
        # Like the quantities of the sale_stock module: read once per warehouse
        # and scheduled date.
        lines = self.filtered(
            lambda line: line.product_id and line.display_qty_widget
        ).sorted(key=lambda r: r.sequence)
        grouped_lines = lines.grouped(
            lambda line: (line.warehouse_id, line.scheduled_date)
        )
        usable_qty_per_line = {}
        for (warehouse, scheduled_date), group_lines in grouped_lines.items():
            # `warehouse` isn't a valid context key anymore since 19.0, the stock
            # quantities are only filtered by `warehouse_id`
            products = group_lines.product_id.with_context(
                to_date=scheduled_date, warehouse_id=warehouse.id
            )
            usable_qties = {
                product.id: product.immediately_usable_qty for product in products
            }
            for line in group_lines:
                usable_qty_per_line[line] = usable_qties[line.product_id.id]
        qty_processed_per_product = defaultdict(float)
        for line in lines:
            product = line.product_id
            qty_processed = qty_processed_per_product[product.id]
            qty = usable_qty_per_line[line] - qty_processed
            # Quantities are expressed in the product UoM, but the popover shows the
            # line one, so we convert them as Odoo does with the other quantities
            product_uom = product.uom_id
            line_uom = line.product_uom_id
            product_uom_qty = line.product_uom_qty
            if line_uom and product_uom and line_uom != product_uom:
                qty = product_uom._compute_quantity(qty, line_uom)
                product_uom_qty = line_uom._compute_quantity(
                    line.product_uom_qty, product_uom
                )
            line.immediately_usable_qty_today = qty
            qty_processed_per_product[product.id] += product_uom_qty
