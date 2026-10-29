# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo.fields import Domain
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
            self.assertEqual(domain, Domain(expected))

    def test_domain(self):
        """The locations are those of the context.

        Scenario:
            1. Have a sub-location of the stock in the main warehouse, and another
               one in a second warehouse, each with its own sub-location.
            2. Get the locations without context, then for one location, then for
               the second warehouse.
        Expected:
            - Without context, the locations of the main warehouse are taken.
            - For one location, only that location is taken.
            - For the second warehouse, only its locations are taken.
        """
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
            .with_context(warehouse_id=self.warehouse_2.id)
            ._get_domain_location_for_locations()
        )

        self.assertTrue(self.stock_2.id in locations.ids)
        self.assertTrue(self.stock_2_1.id in locations.ids)

        self.assertFalse(self.stock_1.id in locations.ids)
        self.assertFalse(self.stock_1_1.id in locations.ids)

    def test_quant_domain_parsing_1(self):
        """A condition on the location of the quants applies to the locations."""
        self.assertLocationDomain([("location_id", "=", 1)], [("id", "=", 1)])

    def test_quant_domain_parsing_2(self):
        """A condition on a field of the location applies to that field."""
        self.assertLocationDomain([("location_id.name", "=", 1)], [("name", "=", 1)])

    def test_quant_domain_parsing_3(self):
        """A condition on the quant alone is ignored: all locations are taken."""
        self.assertLocationDomain([("id", "=", 1)], [])

    def test_quant_domain_parsing_4(self):
        """A condition on the quant is ignored in an alternative.

        Scenario:
            1. Look for the quants that are quant 1 or in a location named
               "test", and in a location named "test2".
        Expected:
            - The locations named "test" and "test2" are taken: the condition on
              the quant is ignored.
        """
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
        """A condition on the quant is ignored, next to alternatives on the location.

        Scenario:
            1. Look for the quants that are quant 1 or in a location named
               "test", and in a location named "test2" or "test3".
        Expected:
            - The locations named "test", and "test2" or "test3", are taken: the
              condition on the quant is ignored.
        """
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
        """Conditions on the quant are ignored in several alternatives.

        Scenario:
            1. Look for the quants that are quant 1 or in a location named
               "test", and named "test2" themselves or in a location named
               "test3".
        Expected:
            - The locations named "test" and "test3" are taken: the conditions on
              the quant are ignored.
        """
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
        """Alternatives on the locations all apply to them.

        Scenario:
            1. Look for the quants in a location named "test", "test2" or
               "test3".
        Expected:
            - The locations named "test", "test2" or "test3" are taken.
        """
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
        """A condition on the quant is ignored among alternatives on the location.

        Scenario:
            1. Look for the quants named "test" themselves, or in a location
               named "test2" or "test3".
        Expected:
            - The locations named "test2" or "test3" are taken: the condition on
              the quant is ignored.
        """
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
        """The location itself and its fields can be mixed in alternatives.

        Scenario:
            1. Look for the quants that are quant 1 or in a location named
               "test", and in location 1 or in a location named "test3".
        Expected:
            - The locations named "test", that are location 1 or named "test3",
              are taken: the condition on the quant is ignored.
        """
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

    def test_quant_domain_parsing_10(self):
        """A condition on the quant is ignored in nested alternatives.

        Scenario:
            1. Look for the quants that are quant 1, or in a location named
               "test", "test2" or "test3".
        Expected:
            - The locations named "test", "test2" or "test3" are taken: the
              condition on the quant is ignored.
        """
        quant_domain = [
            "|",
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
                "|",
                "|",
                ("name", "=", "test"),
                ("name", "=", "test2"),
                ("name", "=", "test3"),
            ],
        )

    def test_quant_domain_parsing_11(self):
        """A condition on the quant is ignored next to one on the location.

        Scenario:
            1. Look for the quants that are quant 1 and in a location named
               "test".
        Expected:
            - The locations named "test" are taken: the condition on the quant
              is ignored.
        """
        quant_domain = [
            "&",
            ("id", "=", 1),
            ("location_id.name", "=", "test"),
        ]

        self.assertLocationDomain(quant_domain, [("name", "=", "test")])

    def test_quant_domain_parsing_12(self):
        """A negated condition on the quant alone is ignored."""
        self.assertLocationDomain(["!", ("id", "=", 1)], [])

    def test_quant_domain_parsing_13(self):
        """A negated condition on the location applies to the locations.

        Scenario:
            1. Look for the quants that are not in a location named "test".
        Expected:
            - The locations not named "test" are taken.
        """
        self.assertLocationDomain(
            ["!", ("location_id.name", "=", "test")], [("name", "!=", "test")]
        )

    def test_quant_domain_parsing_14(self):
        """A condition on the quant is ignored in a negated alternative.

        Scenario:
            1. Look for the quants that are neither quant 1, nor in a location
               named "test".
        Expected:
            - The locations not named "test" are taken: the condition on the
              quant is ignored.
        """
        quant_domain = [
            "!",
            "|",
            ("id", "=", 1),
            ("location_id.name", "=", "test"),
        ]

        self.assertLocationDomain(quant_domain, [("name", "!=", "test")])

    def test_quant_domain_parsing_15(self):
        """A condition on the quant is ignored in a negated requirement.

        Scenario:
            1. Look for the quants that are not both quant 1 and in a location
               named "test".
        Expected:
            - The locations not named "test" are taken: the condition on the
              quant is ignored.
        """
        quant_domain = [
            "!",
            "&",
            ("id", "=", 1),
            ("location_id.name", "=", "test"),
        ]

        self.assertLocationDomain(quant_domain, [("name", "!=", "test")])

    def test_quant_domain_parsing_no_location(self):
        """A context without locations takes no location."""
        self.assertLocationDomain(Domain.FALSE, Domain.FALSE)

    def test_quant_domain_parsing_any(self):
        """A condition on any location of the quants applies to the locations."""
        self.assertLocationDomain(
            [("location_id", "any", [("name", "=", "test")])],
            [("name", "=", "test")],
        )

    def test_quant_domain_parsing_not_any(self):
        """A condition on no location of the quants excludes the locations."""
        self.assertLocationDomain(
            [("location_id", "not any", [("name", "=", "test")])],
            ["!", ("name", "=", "test")],
        )
