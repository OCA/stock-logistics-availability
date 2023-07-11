# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from collections import defaultdict

from odoo import fields, models
from odoo.tools import float_compare
from odoo.tools.safe_eval import safe_eval

from odoo.addons.stock.models.product import OPERATORS


class ProductProduct(models.Model):

    _inherit = "product.product"

    quantity_to_replenish = fields.Float(
        compute="_compute_available_quantities",
        search="_search_quantity_to_replenish",
        help="This is the quantity to replenish following the location orderpoints.",
    )
    quantity_in_replenishments = fields.Float(
        compute="_compute_available_quantities",
        search="_search_quantity_in_replenishments",
        help="This is the quantity currently in replenishments following the "
        "location orderpoints.",
    )

    def _compute_available_quantities_dict(self):
        """
        Retrieve all replenishment quantities for the selected products
        and locations.
        """
        res, stock_dict = super()._compute_available_quantities_dict()
        location_domain = self._get_domain_location_for_locations()
        locations = self.env["stock.location"].search(location_domain)
        orderpoint_obj = self.env["stock.location.orderpoint"]
        if orderpoint_obj.check_access_rights("read", raise_exception=False):
            orderpoint_domain = orderpoint_obj._prepare_orderpoint_domain_location(
                locations.ids
            )
            orderpoints = orderpoint_obj.search(orderpoint_domain)
        else:
            for product in self:
                res[product.id]["quantity_to_replenish"] = 0
                res[product.id]["quantity_in_replenishments"] = 0
                return res, stock_dict

        # Merge both source locations and destination locations
        location_ids = set(
            orderpoints.location_id.ids + orderpoints.location_src_id.ids
        )
        qties_on_locations = orderpoints._compute_quantities_dict(
            self.env["stock.location"].browse(location_ids),
            self,
        )
        # Get current replenishments
        current_moves = self.env["stock.move"].read_group(
            [
                ("location_id", "in", orderpoints.location_src_id.ids),
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
        for product in self:
            qties_replenished_for_location = {product: 0.0}
            for orderpoint in orderpoints:
                # As we compute global quantities for the product, pass
                # always 0 to the already replenished quantity
                qty_to_replenish = orderpoint._get_qty_to_replenish(
                    product,
                    qties_on_locations,
                    0,
                )
                if (
                    float_compare(
                        qty_to_replenish, 0, precision_rounding=product.uom_id.rounding
                    )
                    > 0
                ):
                    qties_replenished_for_location[product] += qty_to_replenish
            res[product.id][
                "quantity_in_replenishments"
            ] = quantities_in_replenishments[product.id]
            res[product.id]["quantity_to_replenish"] = qties_replenished_for_location[
                product
            ]
        return res, stock_dict

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
        return action
