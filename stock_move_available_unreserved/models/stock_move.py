# Copyright 2026 Dealtech Srl - Alessandro Boldrini
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    available_unreserved_quantity = fields.Float(
        string="Available quantity",
        compute="_compute_available_unreserved_quantity",
        digits="Product Unit of Measure",
        help="Unreserved quantity available for this product in the source location.",
    )

    @api.depends("product_id", "location_id")
    def _compute_available_unreserved_quantity(self):
        Quant = self.env["stock.quant"]
        for move in self:
            move.available_unreserved_quantity = (
                Quant._get_available_quantity(move.product_id, move.location_id)
                if move.product_id.is_storable and move.location_id
                else 0.0
            )
