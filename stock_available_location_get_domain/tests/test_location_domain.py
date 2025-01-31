# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest import mock

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

    def assertLocationDomain(self, quant_domain, expected):
        product_product = self.env["product.product"]
        with mock.patch.object(
            product_product.__class__,
            "_get_domain_locations",
            return_value=[quant_domain],
        ):
            domain = product_product._get_domain_location_for_locations()
            self.assertEqual(domain, expected)

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

    def test_quant_domain_parsing_1(self):
        self.assertLocationDomain([("location_id", "=", 1)], [("id", "=", 1)])

    def test_quant_domain_parsing_2(self):
        self.assertLocationDomain([("location_id.name", "=", 1)], [("name", "=", 1)])

    def test_quant_domain_parsing_3(self):
        self.assertLocationDomain([("id", "=", 1)], [])

    def test_quant_domain_parsing_4(self):
        quant_domain = [
            "&",
            "|",
            ("id", "=", 1),
            ("location_id.name", "=", "test"),
            ("location_id.name", "=", "test2"),
        ]

        self.assertLocationDomain(
            quant_domain, ["&", ("name", "=", "test"), ("name", "=", "test2")]
        )

    def test_quant_domain_parsing_5(self):
        quant_domain = [
            "&",
            "|",
            ("id", "=", 1),
            ("location_id.name", "=", "test"),
            "|",
            ("location_id.name", "=", "test2"),
            ("location_id.name", "=", "test3"),
        ]

        self.assertLocationDomain(
            quant_domain,
            [
                "&",
                ("name", "=", "test"),
                "|",
                ("name", "=", "test2"),
                ("name", "=", "test3"),
            ],
        )

    def test_quant_domain_parsing_6(self):
        quant_domain = [
            "&",
            "|",
            ("id", "=", 1),
            ("location_id.name", "=", "test"),
            "|",
            ("name", "=", "test2"),
            ("location_id.name", "=", "test3"),
        ]

        self.assertLocationDomain(
            quant_domain, ["&", ("name", "=", "test"), ("name", "=", "test3")]
        )

    def test_quant_domain_parsing_7(self):
        quant_domain = [
            "|",
            "|",
            ("location_id.name", "=", "test"),
            ("location_id.name", "=", "test2"),
            ("location_id.name", "=", "test3"),
        ]

        self.assertLocationDomain(
            quant_domain,
            [
                "|",
                "|",
                ("name", "=", "test"),
                ("name", "=", "test2"),
                ("name", "=", "test3"),
            ],
        )

    def test_quant_domain_parsing_8(self):
        quant_domain = [
            "|",
            "|",
            ("name", "=", "test"),
            ("location_id.name", "=", "test2"),
            ("location_id.name", "=", "test3"),
        ]

        self.assertLocationDomain(
            quant_domain, ["|", ("name", "=", "test2"), ("name", "=", "test3")]
        )

    def test_quant_domain_parsing_9(self):
        quant_domain = [
            "&",
            "|",
            ("id", "=", 1),
            ("location_id.name", "=", "test"),
            "|",
            ("location_id", "=", 1),
            ("location_id.name", "=", "test3"),
        ]

        self.assertLocationDomain(
            quant_domain,
            ["&", ("name", "=", "test"), "|", ("id", "=", 1), ("name", "=", "test3")],
        )
