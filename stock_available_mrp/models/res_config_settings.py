from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    @api.model
    def _get_stock_available_mrp_based_on(self):
        """Gets the available languages for the selection."""
        pdct_fields = self.env["ir.model.fields"].search(
            [("model", "=", "product.product"), ("ttype", "=", "float")]
        )
        return [
            (field.name, field.field_description)
            for field in sorted(pdct_fields, key=lambda f: f.field_description)
        ]

    stock_available_mrp_based_on = fields.Selection(
        _get_stock_available_mrp_based_on,
        string="based on",
        config_parameter="stock_available_mrp.stock_available_mrp_based_on",
        help="Choose the field of the product which will be used to compute "
        "potential.\nIf empty, Quantity On Hand is used.\n"
        "Only the quantity fields have meaning for computing stock",
    )
