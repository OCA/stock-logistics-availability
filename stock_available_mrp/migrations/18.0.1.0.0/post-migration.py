from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Migrate value from old parameter key to new parameter key.

    New parameter key was introduced in 17.0 in res.config.parameter but not
    actually used.
    """
    new_key = "stock_available_mrp.stock_available_mrp_based_on"
    old_key = "stock_available_mrp_based_on"
    env = api.Environment(cr, SUPERUSER_ID, {})
    value = env["ir.config_parameter"].get_param(old_key, None)
    if value:
        env["ir.config_parameter"].set_param(new_key, value)
        # Clean up old key to avoid any future confusion
        env["ir.config_parameter"].search([("key", "=", old_key)]).unlink()
