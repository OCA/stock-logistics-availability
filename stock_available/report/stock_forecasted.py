# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockForecastedProductProduct(models.AbstractModel):
    _inherit = "stock.forecasted_product_product"

    def _get_product_quantities(self, res, product_template_ids, product_ids):
        # OVERRIDE: add the available to promise to the report header.
        result = super()._get_product_quantities(res, product_template_ids, product_ids)
        for product in self._get_products(product_template_ids, product_ids):
            res["product"][product.id]["immediately_usable_qty"] = (
                product.immediately_usable_qty
            )
        return result
