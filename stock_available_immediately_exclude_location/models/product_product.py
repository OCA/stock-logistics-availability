# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools import ormcache_context


class ProductProduct(models.Model):

    _inherit = "product.product"

    def _compute_available_quantities_dict(self):
        """
        change the way immediately_usable_qty is computed by deducing the quants
        in excluded locations
        """
        res, stock_dict = super()._compute_available_quantities_dict()
        excluded_qty_dict = (
            self._get_qty_available_in_locations_excluded_from_immadiatly_usable_qty()
        )
        for product_id, qty in excluded_qty_dict.items():
            res[product_id]["immediately_usable_qty"] -= qty
        return res, stock_dict

    def _get_qty_available_in_locations_excluded_from_immadiatly_usable_qty(self):
        """Return a dict of qty available by product
        into excluded locations. If no location is excluded
        retrurn an empty dict
        """
        exclude_location_ids = (
            self._get_location_ids_excluded_from_immediately_usable_qty()
        )
        if not exclude_location_ids:
            return {}

        context = self.env.context
        to_date = context.get("to_date")
        to_date = fields.Datetime.to_datetime(to_date)
        dates_in_the_past = False
        if to_date and to_date < fields.Datetime.now():
            dates_in_the_past = True

        # we use strict=True to avoid time consuming query criteria on location
        # to get children locations of the excluded locations. The method
        # _get_location_ids_excluded_from_immediately_usable_qty has already
        # resolved the children locations of the excluded locations.
        products_with_excluded_loc = self.with_context(
            location=exclude_location_ids, strict=True
        )

        if dates_in_the_past:
            # we call the original _compute_quantities_dict since
            # the qty_available will be computed from quants and
            # moves
            excluded_qty_dict = products_with_excluded_loc._compute_quantities_dict(
                context.get("lot_id"),
                context.get("owner_id"),
                context.get("package_id"),
                context.get("from_date"),
                to_date,
            )
            return {p: q["qty_available"] for p, q in excluded_qty_dict.items()}
        # we are not in the past, the qty available is the sum of quant's qties
        # into the exluded locations. A simple read_group will do the job.
        # By avoiding the call to _compute_quantities_dict, we avoid 2 useless
        # queries to the database to retrieve the incoming and outgoing moves
        # that are not needed here and therefore improve the performance.
        (
            domain_quant_loc,
            _domain_move_in_loc,
            _domain_move_out_loc,
        ) = products_with_excluded_loc._get_domain_locations()
        domain_quant = [("product_id", "in", self.ids)] + domain_quant_loc
        quant = self.env["stock.quant"].with_context(active_test=False)
        return {
            item["product_id"][0]: item["quantity"]
            for item in quant._read_group(
                domain_quant,
                ["product_id", "quantity"],
                ["product_id"],
                orderby="id",
            )
        }

    @api.model
    @ormcache_context(
        "tuple(self.env.companies.ids)", keys=("tuple(location)", "tuple(warehouse)")
    )
    def _get_location_ids_excluded_from_immediately_usable_qty(self):
        """
        Return the ids of the locations that should be excluded from the
        immediately_usable_qty. This method return the ids of leaf locations
        that are excluded from the immediately_usable_qty and the children of
        the view locations that are excluded from the immediately_usable_qty.
        """
        locations = self._get_locations_excluded_from_immediately_usable_qty()
        view_locations = locations.filtered(lambda l: l.usage == "view")
        # we must exclude the children of the view locations
        locations |= self.env["stock.location"].search(
            [
                ("location_id", "child_of", view_locations.ids),
                ("usage", "in", ["internal", "transit"]),
            ]
        )
        return locations.ids

    @api.model
    def _get_locations_excluded_from_immediately_usable_qty(self):
        return self.env["stock.location"].search(
            self._get_domain_location_excluded_from_immediately_usable_qty()
        )

    @api.model
    def _get_domain_location_excluded_from_immediately_usable_qty(self):
        """
        Parses the context and returns a list of location_ids based on it that
        should be excluded from the immediately_usable_qty
        """
        location_domain = self.env[
            "product.product"
        ]._get_domain_location_for_locations()
        return expression.AND(
            [location_domain, [("exclude_from_immediately_usable_qty", "=", True)]]
        )

    def _get_domain_locations_new(self, location_ids):
        # We override this method to add the possibility to work with a strict
        # context parameter. This parameter is used to force the method to
        # restrict the domain to the location_ids passed as parameter in place
        # if considering all locations children of the location_ids.
        # Prior to Odoo 16, this behavior was possible by setting the context
        # parameter 'compute_child' to False. This parameter has been removed
        # in Odoo 16 in commit https://github.com/odoo/odoo/commit/
        # f054af31b098d8cb1ef64369e857a36c70918033 and reintroduced in Odoo >= 17
        # in commit https://github.com/odoo/odoo/commit/
        # add97b3c2dc1df70d22f87047cf012463f3e12c4 as 'strict' context parameter.
        # The original design of this addon developped for Odoo 10 has always
        # been to consider only the locations passed as parameter and not their
        # children to avoid performance issues. This is why we reintroduce this
        # behavior.
        if not self.env.context.get("strict"):
            return super()._get_domain_locations_new(location_ids)

        location_ids = list(location_ids)
        loc_domain = [("location_id", "in", location_ids)]
        dest_loc_domain = [("location_dest_id", "in", location_ids)]
        return (
            loc_domain,
            dest_loc_domain + ["!"] + loc_domain if loc_domain else dest_loc_domain,
            loc_domain + ["!"] + dest_loc_domain if dest_loc_domain else loc_domain,
        )
