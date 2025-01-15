# Copyright 2024 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _name = "res.company"
    _inherit = ["res.company", "stock.exclude.location.mixin"]

    stock_excluded_location_ids = fields.Many2many(
        comodel_name="stock.location",
        string="Stock Excluded Locations",
        help="Fill in this field to exclude locations for product available quantities.",
    )
