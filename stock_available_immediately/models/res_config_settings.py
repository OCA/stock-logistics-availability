from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    compute_stock_available_immediately = fields.Boolean(
        string="Exclude incoming goods",
        help="This will subtract incoming quantities from the quantities "
        "available to promise.",
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        param_env = self.env["ir.config_parameter"].sudo()
        value = param_env.get_param(
            "stock_available_immediately.compute_stock_available_immediately", "True"
        )
        res.update(compute_stock_available_immediately=value == "True")
        return res

    def set_values(self):
        res = super().set_values()
        ir_config_sudo = self.env["ir.config_parameter"].sudo()
        ir_config_sudo.set_param(
            "stock_available_immediately.compute_stock_available_immediately",
            str(self.compute_stock_available_immediately),
        )
        return res
