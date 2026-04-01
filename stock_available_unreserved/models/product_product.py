# Copyright 2018 Camptocamp SA
# Copyright 2016-19 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    # Remove me after 18.0
    qty_available_not_res = fields.Float(
        related="free_qty",
        string="Qty Available Not Reserved",
        digits="Product Unit of Measure",
        help="Quantity of this product that is "
        "not currently reserved for a stock move",
    )
