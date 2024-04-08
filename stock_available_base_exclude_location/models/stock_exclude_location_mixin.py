# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class StockExcludeLocationMixin(models.AbstractModel):

    _name = "stock.exclude.location.mixin"
    _description = (
        "technical base module to allow defining excluded locations on an Odoo model"
    )

    stock_excluded_location_ids = fields.Many2many(
        comodel_name="stock.location",
        string="Stock Excluded Locations",
        help="Fill in this field to exclude locations for product available"
        "quantities.",
    )
    stock_excluded_location_domain = fields.Binary(
        compute="_compute_stock_excluded_location_domain",
        help="Fill in this with the domain you want to exclude locations for "
        "product available quantities",
    )
    stock_excluded_location_domain_char = fields.Char(
        default="[]",
        string="Domain to filter locations",
        help="Fill in this with the domain you want to exclude locations for "
        "product available quantities",
    )

    @api.depends("stock_excluded_location_domain_char")
    def _compute_stock_excluded_location_domain(self):
        for record in self:
            record.stock_excluded_location_domain = safe_eval(
                record.stock_excluded_location_domain_char
            )
