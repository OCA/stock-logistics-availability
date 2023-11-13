# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.osv import expression


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
            domain_excluded_quant_loc = expression.AND(
                [
                    [("location_id", "not in", excluded_location_ids.ids)],
                    domain_excluded_quant_loc,
                ]
            )
            domain_excluded_move_in_loc = expression.AND(
                [
                    [("location_id", "not in", excluded_location_ids.ids)],
                    domain_excluded_move_in_loc,
                ]
            )
            domain_excluded_move_out_loc = expression.AND(
                [
                    [("location_id", "not in", excluded_location_ids.ids)],
                    domain_excluded_move_out_loc,
                ]
            )
        if excluded_location_domain:
            domain_excluded_quant_loc = expression.AND(
                [
                    excluded_location_domain,
                    domain_excluded_quant_loc,
                ]
            )
            domain_excluded_move_in_loc = expression.AND(
                [
                    excluded_location_domain,
                    domain_excluded_move_in_loc,
                ]
            )
            domain_excluded_move_out_loc = expression.AND(
                [
                    excluded_location_domain,
                    domain_excluded_move_out_loc,
                ]
            )
        domain_quant_loc = (
            expression.AND(
                [
                    domain_excluded_quant_loc,
                    domain_quant_loc,
                ]
            )
            if domain_excluded_quant_loc
            else domain_quant_loc
        )
        domain_move_in_loc = (
            expression.AND(
                [
                    domain_excluded_move_in_loc,
                    domain_move_in_loc,
                ]
            )
            if domain_excluded_move_in_loc
            else domain_move_in_loc
        )
        domain_move_out_loc = (
            expression.AND(
                [
                    domain_excluded_move_out_loc,
                    domain_move_out_loc,
                ]
            )
            if domain_excluded_move_in_loc
            else domain_move_out_loc
        )
        return domain_quant_loc, domain_move_in_loc, domain_move_out_loc
