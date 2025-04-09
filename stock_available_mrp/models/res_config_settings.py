from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    stock_available_potential_based = fields.Boolean(
        string="Consider potential stock for availability",
        help="This allow to add the quantities of goods that can be "
        "immediately manufactured, to the quantities available to "
        "promise.\n",
        default=True,
        config_parameter="stock_available_potential_based",
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        param_value = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("stock_available_potential_based")
        )
        if param_value is not None:
            res["stock_available_potential_based"] = param_value == "True"
        return res

    def set_values(self):
        potential_based = self.stock_available_potential_based
        res = super(ResConfigSettings, self).set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "stock_available_potential_based", "True" if potential_based else "False"
        )
        return res
