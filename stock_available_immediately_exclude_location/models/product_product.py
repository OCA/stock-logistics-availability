# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models
from odoo.fields import Domain
from odoo.tools import ormcache


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _compute_available_quantities_dict(self):
        # OVERRIDE: compute the immediately usable quantity on the locations of
        # the context that are not excluded.
        res, stock_dict = super()._compute_available_quantities_dict()
        excluded_location_ids = (
            self._get_location_ids_excluded_from_immediately_usable_qty()
        )
        if not excluded_location_ids:
            return res, stock_dict
        usable_qty_dict = self._get_immediately_usable_qty_out_of_excluded_locations(
            excluded_location_ids
        )
        for product_id, quantities in res.items():
            quantities["immediately_usable_qty"] = usable_qty_dict.get(product_id, 0.0)
        return res, stock_dict

    def _get_immediately_usable_qty_out_of_excluded_locations(
        self, excluded_location_ids
    ):
        """Return the immediately usable quantity out of the excluded locations.

        It is computed by the same methods as the immediately usable quantity
        itself, on the locations of the context that are not excluded, so that
        the date, lot, owner, package and expired quantities of the context are
        taken into account the same way. A move from an excluded location to
        another location of the context is then incoming, and a move from an
        excluded location out of the context is not outgoing.
        """
        locations = (
            self.env["stock.location"]
            .with_context(active_test=False)
            .search(
                self._get_domain_location_for_locations()
                & Domain("id", "not in", excluded_location_ids)
            )
        )
        if not locations:
            return {}
        # ``strict``: the children of the locations are already among them.
        products = self.with_context(location=locations.ids, strict=True)
        usable_res, _stock_dict = super(
            ProductProduct, products
        )._compute_available_quantities_dict()
        return {
            product_id: quantities["immediately_usable_qty"]
            for product_id, quantities in usable_res.items()
        }

    @api.model
    @ormcache(
        "tuple(self.env.companies.ids)",
        "str(self.env.context.get('location'))",
        "str(self.env.context.get('search_location'))",
        "str(self.env.context.get('warehouse_id'))",
        "str(self.env.context.get('search_warehouse'))",
        "bool(self.env.context.get('strict'))",
    )
    def _get_location_ids_excluded_from_immediately_usable_qty(self):
        """
        Return the ids of the locations that should be excluded from the
        immediately_usable_qty. This method return the ids of leaf locations
        that are excluded from the immediately_usable_qty and the children of
        the view locations that are excluded from the immediately_usable_qty.
        """
        locations = self._get_locations_excluded_from_immediately_usable_qty()
        view_locations = locations.filtered(lambda location: location.usage == "view")
        # we must exclude the children of the view locations
        locations |= (
            self.env["stock.location"]
            .with_context(active_test=False)
            .search(
                [
                    ("location_id", "child_of", view_locations.ids),
                    ("usage", "in", ["internal", "transit"]),
                ]
            )
        )
        return tuple(locations.ids)

    @api.model
    def _get_locations_excluded_from_immediately_usable_qty(self):
        # The archived locations can still hold goods, which are counted in the
        # quantities: they must be excluded too.
        return (
            self.env["stock.location"]
            .with_context(active_test=False)
            .search(self._get_domain_location_excluded_from_immediately_usable_qty())
        )

    @api.model
    def _get_domain_location_excluded_from_immediately_usable_qty(self):
        """
        Parses the context and returns a list of location_ids based on it that
        should be excluded from the immediately_usable_qty
        """
        return self._get_domain_location_for_locations() & Domain(
            "exclude_from_immediately_usable_qty", "=", True
        )
