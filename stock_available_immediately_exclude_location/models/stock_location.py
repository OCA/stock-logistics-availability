# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockLocation(models.Model):

    _inherit = "stock.location"

    exclude_from_immediately_usable_qty = fields.Boolean(
        "Exclude from immediately usable quantity",
        default=False,
        index=True,
        help="This property is not inherited by children locations",
    )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        self._invalidate_location_ids_excluded_from_immediatley_usable_qty_cache()
        return res

    def write(self, vals):
        res = super().write(vals)
        if "exclude_from_immediately_usable_qty" in vals:
            self._invalidate_location_ids_excluded_from_immediatley_usable_qty_cache()
        return res

    def _invalidate_location_ids_excluded_from_immediatley_usable_qty_cache(self):
        product_model = self.env["product.product"]
        product_model._get_location_ids_excluded_from_immediately_usable_qty.clear_cache(
            product_model
        )
