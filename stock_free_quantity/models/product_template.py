from odoo import fields, models
from odoo.fields import Domain


class ProductTemplate(models.Model):
    _inherit = "product.template"

    free_qty = fields.Float(search="_search_free_qty")

    def _search_free_qty(self, operator, value):
        if operator in Domain.NEGATIVE_OPERATORS:
            return NotImplemented
        return [("product_variant_ids.free_qty", operator, value)]
