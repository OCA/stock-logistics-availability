# Copyright 2018 Camptocamp SA
# Copyright 2016-19 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Remove me after 18.0
    qty_available_not_res = fields.Float(
        related="free_qty",
        string="Quantity On Hand Unreserved",
        digits="Product Unit of Measure",
        help="Quantity of this product that is "
        "not currently reserved for a stock move",
    )
    free_qty = fields.Float(
        "Free to Use Quantity",
        compute="_compute_quantities",
        search="_search_free_qty",
        compute_sudo=False,
        digits="Product Unit of Measure",
    )

    def _compute_quantities(self):
        res = super()._compute_quantities()
        variants_available = {
            p["id"]: p for p in self.product_variant_ids._origin.read(["free_qty"])
        }
        for template in self:
            free_qty = 0
            for p in template.product_variant_ids._origin:
                free_qty += variants_available[p.id]["free_qty"]
            template.free_qty = free_qty
        return res

    def _search_free_qty(self, operator, value):
        domain = [("free_qty", operator, value)]
        product_variant_query = self.env["product.product"]._search(domain)
        return [("product_variant_ids", "in", product_variant_query)]

    def action_open_quants_unreserved(self):
        products_ids = self.mapped("product_variant_ids").ids
        quants = self.env["stock.quant"].search([("product_id", "in", products_ids)])
        quant_ids = quants.filtered(lambda x: x.product_id.free_qty > 0).ids
        result = self.env["ir.actions.actions"]._for_xml_id(
            "stock.dashboard_open_quants"
        )
        result["display_name"] = self.env._("Free to Use Quantity")
        result["domain"] = [("id", "in", quant_ids)]
        result["context"] = {
            "search_default_locationgroup": 1,
            "search_default_internal_loc": 1,
        }
        return result
