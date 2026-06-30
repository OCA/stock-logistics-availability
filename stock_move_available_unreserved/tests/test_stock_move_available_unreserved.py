# Copyright 2026 Dealtech Srl - Alessandro Boldrini
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestStockMoveAvailableUnreserved(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Available Unreserved Product",
                "type": "consu",
                "is_storable": True,
            }
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product,
            cls.stock_location,
            10.0,
        )
        cls.move = cls.env["stock.move"].create(
            {
                "name": cls.product.display_name,
                "product_id": cls.product.id,
                "product_uom_qty": 4.0,
                "product_uom": cls.product.uom_id.id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
            }
        )

    def test_available_unreserved_quantity_is_not_capped_by_demand(self):
        self.move._compute_available_unreserved_quantity()
        self.assertEqual(self.move.availability, 4.0)
        self.assertEqual(self.move.available_unreserved_quantity, 10.0)

    def test_available_unreserved_quantity_without_product_or_location(self):
        move = self.env["stock.move"].new({})
        move._compute_available_unreserved_quantity()
        self.assertEqual(move.available_unreserved_quantity, 0.0)
