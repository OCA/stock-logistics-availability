# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from collections import defaultdict

from odoo import api, fields, models
from odoo.tools import float_compare
from odoo.tools.safe_eval import safe_eval

from odoo.addons.stock.models.product import OPERATORS


class ProductProduct(models.Model):
    _inherit = "product.product"

    quantity_to_replenish = fields.Float(
        compute="_compute_replenishment_quantities",
        search="_search_quantity_to_replenish",
        prefetch=False,
        help="This is the quantity to replenish following the location orderpoints.",
    )
    quantity_in_replenishments = fields.Float(
        compute="_compute_replenishment_quantities",
        search="_search_quantity_in_replenishments",
        prefetch=False,
        help="This is the quantity currently in replenishments following the "
        "location orderpoints.",
    )

    @api.depends_context("location")
    def _compute_replenishment_quantities(self):
        orderpoint_obj = self.env["stock.location.orderpoint"]
        if orderpoint_obj.check_access_rights("read", raise_exception=False):
            orderpoint_obj = self.env["stock.location.orderpoint"]
            location_domain = self._get_domain_location_for_locations()
            locations = self.env["stock.location"].search(location_domain)
            orderpoint_domain = orderpoint_obj._prepare_orderpoint_domain_location(
                locations.ids
            )
            orderpoints = orderpoint_obj.search(orderpoint_domain)
        else:
            self.update(
                {
                    "quantity_to_replenish": 0.0,
                    "quantity_in_replenishments": 0.0,
                }
            )
            return

        # Get current replenishments
        current_moves = self.env["stock.move"].read_group(
            [
                ("location_orderpoint_id", "in", orderpoints.ids),
                ("state", "not in", ("done", "cancel")),
                ("product_id", "in", self.ids),
            ],
            ["product_id", "product_uom_qty:sum"],
            ["product_id"],
        )
        quantities_in_replenishments = defaultdict(lambda: defaultdict(lambda: 0))
        for current_move in current_moves:
            quantities_in_replenishments[current_move["product_id"][0]] = current_move[
                "product_uom_qty"
            ]

        # Compute quantities to replenish
        qties_replenished_for_location = defaultdict(lambda: 0.0)
        for orderpoint in orderpoints:
            replenishment_qty_computer = orderpoint._get_replenishment_computer()
            procurement_qty = replenishment_qty_computer.compute(
                products=self, demand_only=False
            )
            for product_id, qty_to_replenish in procurement_qty.items():
                if (
                    float_compare(
                        qty_to_replenish,
                        0,
                        precision_rounding=self.env["product.product"]
                        .browse(product_id)
                        .uom_id.rounding,
                    )
                    > 0
                ):
                    qties_replenished_for_location[product_id] += qty_to_replenish
        for product in self:
            product.update(
                {
                    "quantity_in_replenishments": quantities_in_replenishments[
                        product.id
                    ],
                    "quantity_to_replenish": qties_replenished_for_location[product.id],
                }
            )
        return

    def _get_search_quantity_to_replenish_domain(self):
        return [("type", "=", "product")]

    def _search_quantity_to_replenish(self, operator, value):
        product_domain = self._get_search_quantity_to_replenish_domain()
        products = self.with_context(prefetch_fields=False).search(
            product_domain, order="id"
        )
        product_ids = []
        for product in products:
            if OPERATORS[operator](product.quantity_to_replenish, value):
                product_ids.append(product.id)
        return [("id", "in", product_ids)]

    def _get_search_quantity_in_replenishments_domain(self):
        return [("type", "=", "product")]

    def _search_quantity_in_replenishments(self, operator, value):
        product_domain = self._get_search_quantity_in_replenishments_domain()
        products = self.with_context(prefetch_fields=False).search(
            product_domain, order="id"
        )
        product_ids = []
        for product in products:
            if OPERATORS[operator](product.quantity_in_replenishments, value):
                product_ids.append(product.id)
        return [("id", "in", product_ids)]

    def action_open_replenishments(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "stock.stock_move_action"
        )
        action["domain"] = [
            ("location_orderpoint_id", "!=", False),
            ("product_id", "=", self.id),
        ]
        action["context"] = dict(safe_eval(action["context"]), search_default_future=1)
        action["context"].pop("search_default_last_month", None)
        return action
