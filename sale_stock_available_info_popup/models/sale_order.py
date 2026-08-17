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
        qty_processed_per_product = defaultdict(float)
        self.immediately_usable_qty_today = False
        for line in self.sorted(key=lambda r: r.sequence):
            if not line.display_qty_widget:
                continue
            # `warehouse` isn't a valid context key anymore since 19.0, the stock
            # quantities are only filtered by `warehouse_id`
            product = line.product_id.with_context(
                to_date=line.scheduled_date, warehouse_id=line.warehouse_id.id
            )
            qty_processed = qty_processed_per_product[product.id]
            qty = product.immediately_usable_qty - qty_processed
            # Quantities are expressed in the product UoM, but the popover shows the
            # line one, so we convert them as Odoo does with the other quantities
            product_uom = line.product_id.uom_id
            line_uom = line.product_uom_id
            product_uom_qty = line.product_uom_qty
            if line_uom and product_uom and line_uom != product_uom:
                qty = product_uom._compute_quantity(qty, line_uom)
                product_uom_qty = line_uom._compute_quantity(
                    line.product_uom_qty, product_uom
                )
            line.immediately_usable_qty_today = qty
            qty_processed_per_product[product.id] += product_uom_qty
