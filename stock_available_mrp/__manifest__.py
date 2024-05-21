# Copyright 2014 Numérigraphe SARL, Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Consider the production potential is available to promise",
    "version": "17.0.1.0.0",
    "author": "Numérigraphe," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-availability",
    "category": "Hidden",
    "depends": ["stock_available", "mrp"],
    "demo": ["demo/mrp_data.xml"],
    "data": [
        "data/ir_config_parameter.xml",
        "views/res_config_settings_views.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
}
