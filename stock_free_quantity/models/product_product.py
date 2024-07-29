from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.stock.models.product import OPERATORS


class ProductProduct(models.Model):
    _inherit = "product.product"

    
    def _prepare_domain_available_not_reserved(self):
        domain_quant = [("product_id", "in", self.ids)]
        domain_quant_locations = self._get_domain_locations()[0]
        domain_quant.extend(domain_quant_locations)
        return domain_quant
