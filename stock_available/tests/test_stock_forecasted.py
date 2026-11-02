# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.stock.tests.common import TestStockCommon


class TestStockForecasted(TestStockCommon):
    def test_report_header(self):
        """The forecasted report shows the available to promise of the product.

        Scenario:
            1. Have 10 units in stock, and a delivery of 3 units waiting.
            2. Open the forecasted report of the product, for the warehouse.
        Expected:
            - The 7 units available to promise are in the report header.
        """
        product = self.ProductObj.create(
            {"name": "Product", "type": "consu", "is_storable": True}
        )
        self.StockQuantObj._update_available_quantity(product, self.stock_location, 10)
        delivery = self.MoveObj.create(
            {
                "product_id": product.id,
                "product_uom_qty": 3,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )
        delivery._action_confirm()
        report = self.env["stock.forecasted_product_product"].with_context(
            warehouse_id=self.warehouse_1.id
        )
        data = report.get_report_values(product.ids)["docs"]
        self.assertEqual(data["product"][product.id]["immediately_usable_qty"], 7)
