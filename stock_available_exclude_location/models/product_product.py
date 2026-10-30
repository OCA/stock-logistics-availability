# Copyright 2024 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.fields import Domain


class ProductProduct(models.Model):
    _inherit = "product.product"

    excluded_location_ids = fields.Many2many(
        comodel_name="stock.location",
        string="Locations to Exclude as Available",
        compute="_compute_excluded_location_ids",
    )

    @api.depends()
    def _compute_excluded_location_ids(self):
        self.excluded_location_ids = False
        stock_quants = self.env["stock.quant"].search(
            Domain("product_id", "in", self.ids) & Domain("on_hand", "=", True)
        )
        for product in self:
            product_quants = stock_quants.filtered(
                lambda quant, product=product: quant.product_id == product
            )
            excluded_ids = product_quants.company_id.stock_excluded_location_ids
            if excluded_ids:
                product.excluded_location_ids = excluded_ids | excluded_ids.children_ids

    def _compute_quantities_dict(
        self, lot_id, owner_id, package_id, from_date=False, to_date=False
    ):
        self_ctx = self.with_context(excluded_location_ids=self.excluded_location_ids)
        return super(ProductProduct, self_ctx)._compute_quantities_dict(
            lot_id, owner_id, package_id, from_date, to_date
        )
