# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class TestExcludeLocationOwner(models.Model):
    _name = "test.exclude.location.owner"
    _inherit = ["stock.exclude.location.mixin"]
    _description = "Test model for stock exclude location mixin"
