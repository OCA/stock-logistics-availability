# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from collections import defaultdict

from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends(
        "product_id",
        "customer_lead",
        "product_uom_qty",
        "product_uom",
        "order_id.commitment_date",
        "move_ids",
        "move_ids.forecast_expected_date",
        "move_ids.forecast_availability",
        "route_id.rule_ids",
    )
    def _compute_qty_at_date(self):
        # Override this method to add dependency on the route
        self = self.with_context(base_on_route_location=True)
        return super()._compute_qty_at_date()

    def _prepare_grouped_lines_at_date(self):
        # Override this method to get lines grouped by location and scheduled date
        if not self.env.context.get("base_on_route_location", False):
            return super()._prepare_grouped_lines_at_date()

        grouped_lines = defaultdict(lambda: self.env["sale.order.line"])
        for line in self.filtered(lambda l: l.state in ("draft", "sent")):
            if not (line.product_id and line.display_qty_widget):
                continue

            locations_to_consider = line._get_location_to_compute_forecasted_quantity()
            for location_id in locations_to_consider:
                grouped_lines[
                    (
                        location_id,
                        line.order_id.commitment_date or line._expected_date(),
                    )
                ] |= line
        return grouped_lines

    def _get_location_to_compute_forecasted_quantity(self):
        self.ensure_one()
        # Default to the stock location if not defined route
        locations_to_consider = [self.warehouse_id.lot_stock_id.id]
        if not self.route_id:
            return locations_to_consider
        # Get the locations to consider based on the route
        rules_to_consider = self.route_id.rule_ids.filtered(
            lambda loc: loc.action in ("pull", "pull_push")
            and loc.location_dest_id.usage == "customer"
        )
        if rules_to_consider:
            locations_to_consider = rules_to_consider.mapped("location_src_id.id")
        return locations_to_consider

    def _get_quantities_at_date_per_product(
        self, scheduled_date, loc_warehouse, from_location=False
    ):
        # Override this method to get quantities per product from location
        if self.env.context.get("base_on_route_location", False):
            from_location = True

        return super()._get_quantities_at_date_per_product(
            scheduled_date, loc_warehouse, from_location=from_location
        )
