# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestStockLocationDomain(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.stock_1 = cls.env["stock.location"].create(
            {
                "name": "Stock 1",
                "location_id": cls.warehouse.lot_stock_id.id,
            }
        )

        cls.stock_1_1 = cls.env["stock.location"].create(
            {
                "name": "Stock 1.1",
                "location_id": cls.stock_1.id,
            }
        )

        cls.warehouse_2 = cls.env["stock.warehouse"].create(
            {
                "name": "Warehouse 2",
                "code": "WH2",
            }
        )

        cls.stock_2 = cls.env["stock.location"].create(
            {
                "name": "Stock 2",
                "location_id": cls.warehouse_2.lot_stock_id.id,
            }
        )

        cls.stock_2_1 = cls.env["stock.location"].create(
            {
                "name": "Stock 2.1",
                "location_id": cls.stock_2.id,
            }
        )

    def test_domain(self):
        locations = self.env["stock.location"].search(
            self.env["product.product"]._get_domain_location_for_locations()
        )
        self.assertTrue(self.stock_1.id in locations.ids)
        self.assertTrue(self.stock_1_1.id in locations.ids)

        locations = self.env["stock.location"].search(
            self.env["product.product"]
            .with_context(location=self.stock_1_1.id)
            ._get_domain_location_for_locations()
        )

        self.assertEqual(self.stock_1_1, locations)

        locations = self.env["stock.location"].search(
            self.env["product.product"]
            .with_context(warehouse=self.warehouse_2.id)
            ._get_domain_location_for_locations()
        )

        self.assertTrue(self.stock_2.id in locations.ids)
        self.assertTrue(self.stock_2_1.id in locations.ids)

        self.assertFalse(self.stock_1.id in locations.ids)
        self.assertFalse(self.stock_1_1.id in locations.ids)
