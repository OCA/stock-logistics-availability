# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.fields import Domain


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_domain_locations_new(self, location_ids):
        """
        This is used to exclude locations if needed
        :param location_ids:
        :param company_id:
        :param compute_child:
        :return:
        """
        (
            domain_quant_loc,
            domain_move_in_loc,
            domain_move_out_loc,
        ) = super()._get_domain_locations_new(
            location_ids=location_ids,
        )
        excluded_location_ids = self.env.context.get("excluded_location_ids", [])
        excluded_location_domain = self.env.context.get("excluded_location_domain", [])
        domain_excluded_quant_loc = []
        domain_excluded_move_in_loc = []
        domain_excluded_move_out_loc = []
        if excluded_location_ids:
            domain_excluded_quant_loc = list(
                Domain([("location_id", "not in", excluded_location_ids.ids)])
                & Domain(domain_excluded_quant_loc)
            )
            domain_excluded_move_in_loc = list(
                Domain([("location_id", "not in", excluded_location_ids.ids)])
                & Domain(domain_excluded_move_in_loc)
            )
            domain_excluded_move_out_loc = list(
                Domain([("location_id", "not in", excluded_location_ids.ids)])
                & Domain(domain_excluded_move_out_loc)
            )
        if excluded_location_domain:
            domain_excluded_quant_loc = list(
                Domain(excluded_location_domain) & Domain(domain_excluded_quant_loc)
            )
            domain_excluded_move_in_loc = list(
                Domain(excluded_location_domain) & Domain(domain_excluded_move_in_loc)
            )
            domain_excluded_move_out_loc = list(
                Domain(excluded_location_domain) & Domain(domain_excluded_move_out_loc)
            )
        domain_quant_loc = (
            list(Domain(domain_excluded_quant_loc) & Domain(domain_quant_loc))
            if domain_excluded_quant_loc
            else domain_quant_loc
        )
        domain_move_in_loc = (
            list(Domain(domain_excluded_move_in_loc) & Domain(domain_move_in_loc))
            if domain_excluded_move_in_loc
            else domain_move_in_loc
        )
        domain_move_out_loc = (
            list(Domain(domain_excluded_move_out_loc) & Domain(domain_move_out_loc))
            if domain_excluded_move_in_loc
            else domain_move_out_loc
        )
        return domain_quant_loc, domain_move_in_loc, domain_move_out_loc
