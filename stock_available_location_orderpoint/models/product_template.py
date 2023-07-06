# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

from odoo.addons.stock.models.product import OPERATORS


class ProductTemplate(models.Model):

    _inherit = "product.template"

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

    @api.depends(
        "product_variant_ids.quantity_to_replenish",
        "product_variant_ids.quantity_in_replenishments",
    )
    def _compute_available_quantities(self):
        return super()._compute_available_quantities()

    def _compute_available_quantities_dict(self):
        """
        Sum all quantities to replenish from variants
        """
        res = super()._compute_available_quantities_dict()
        for template in self:
            res[template.id]["quantity_to_replenish"] = sum(
                p.quantity_to_replenish for p in template.product_variant_ids
            )
            res[template.id]["quantity_in_replenishments"] = sum(
                p.quantity_in_replenishments for p in template.product_variant_ids
            )
        return res

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
            ("product_id", "in", self.product_variant_ids.ids),
        ]
        action["context"] = dict(safe_eval(action["context"]), search_default_future=1)
        return action
