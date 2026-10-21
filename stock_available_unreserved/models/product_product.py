# Copyright 2018 Camptocamp SA
# Copyright 2016-19 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models
from odoo.tools import float_is_zero


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

    def _search_free_qty(self, operator, value):
        # Odoo searches free_qty on stock.quant only and leaves out the
        # products at zero when the operator is "!=" (odoo/odoo#296371). The
        # equality is right, so the result is the products it does not match.
        # A "!" domain would not work here: the ORM turns it back into "!=".
        if operator == "!=" and not float_is_zero(value, precision_digits=8):
            equal_query = self._search(super()._search_free_qty("=", value))
            return [("id", "not in", equal_query)]
        return super()._search_free_qty(operator, value)
