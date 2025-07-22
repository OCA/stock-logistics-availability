from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    compute_stock_available_immediately = fields.Boolean(
        string="Exclude incoming goods",
        help="This will subtract incoming quantities from the quantities "
        "available to promise.",
        default=True,
        config_parameter="compute_stock_available_immediately",
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        param_env = self.env["ir.config_parameter"].sudo()
        value = param_env.get_param("compute_stock_available_immediately")
        if value is None:
            value = param_env.get_param(
                "module_stock_available_immediately", default="False"
            )
        res["compute_stock_available_immediately"] = value == "True"
        return res
