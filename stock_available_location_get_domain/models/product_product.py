# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.osv import expression


class ProductProduct(models.Model):

    _inherit = "product.product"

    def _get_domain_location_for_locations(self):
        """
        Adapt the domain computed for stock.quant for stock.location
        """
        quant_domain = self._get_domain_locations()[0]
        # Adapt the domain on quants by replacing location_id by ""
        # Be sure to exclude potential fields that couldn't belong to stock.location
        # and replace by nothing
        location_domain = []
        location_fields = self.env["stock.location"].fields_get()
        for element in quant_domain:
            leaf = expression.is_leaf(element)
            if leaf:
                field = leaf.split(".")[0]
                if field in location_fields and field != "location_id":
                    location_domain.append(element)
                elif field == "location_id":
                    location_domain.append(
                        (element[0].replace("location_id.", ""), element[1], element[2])
                    )
            else:
                location_domain.append(element)
        return location_domain
