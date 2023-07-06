# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.stock_location_orderpoint.tests.common import (
    TestLocationOrderpointCommon,
)


class TestStockAvailableLocationOrderpoint(TestLocationOrderpointCommon):
    def setUp(self):
        super().setUp()
        self.orderpoint, self.location_src = self._create_orderpoint_complete(
            "Stock2", trigger="manual"
        )
        self.orderpoint2, self.location_src2 = self._create_orderpoint_complete(
            "Stock2.2", trigger="manual"
        )

    def test_available_on_replenish_zero(self):
        """
        There is no stock available in replenishment location
        """
        move = self._create_outgoing_move(12)
        move = self._create_outgoing_move(1)
        self.assertEqual(move.state, "confirmed")
        self.product.invalidate_recordset()
        self.assertEqual(0.0, self.product.quantity_to_replenish)

    def test_available_on_replensih(self):
        """
        There is no stock available in replenishment location
        """
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "inventory_quantity": 10.0,
                "location_id": self.location_src.id,
                "product_id": self.product.id,
            }
        )._apply_inventory()
        move = self._create_outgoing_move(12)
        move = self._create_outgoing_move(1)
        self.assertEqual(move.state, "confirmed")
        self.product.invalidate_recordset()
        self.assertEqual(10.0, self.product.quantity_to_replenish)

    def test_available_on_multi_replenish(self):
        """
        There is no stock available in replenishment location
        """
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "inventory_quantity": 4.0,
                "location_id": self.location_src.id,
                "product_id": self.product.id,
            }
        )._apply_inventory()
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "inventory_quantity": 6.0,
                "location_id": self.location_src2.id,
                "product_id": self.product.id,
            }
        )._apply_inventory()
        move = self._create_outgoing_move(12)
        move = self._create_outgoing_move(1)
        self.assertEqual(move.state, "confirmed")
        self.product.invalidate_recordset()
        self.assertEqual(10.0, self.product.quantity_to_replenish)

    def test_available_on_one_location(self):
        """
        Set stock on replenishment locations (4.0 and 6.0)
        """
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "inventory_quantity": 4.0,
                "location_id": self.location_src.id,
                "product_id": self.product.id,
            }
        )._apply_inventory()
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "inventory_quantity": 6.0,
                "location_id": self.location_src2.id,
                "product_id": self.product.id,
            }
        )._apply_inventory()
        move = self._create_outgoing_move(12)
        move = self._create_outgoing_move(1)
        self.assertEqual(move.state, "confirmed")
        self.product.invalidate_recordset()
        self.assertEqual(
            10.0,
            self.product.with_context(
                location=self.location_dest.id
            ).quantity_to_replenish,
        )

    def test_available_on_one_shelf_location(self):
        """
        Create a second stock location
            - Stock
                - Shelf
        Create an orderpoint for that particular location
        Set stock on replenishment locations (4.0 and 6.0)

        """
        self.shelf = self.env["stock.location"].create(
            {"name": "Shelf to Replenish", "location_id": self.location_dest.id}
        )
        self.location_dest = self.shelf
        (
            self.orderpoint_shelf,
            self.location_src_shelf,
        ) = self._create_orderpoint_complete("Shelf Replenishment", trigger="manual")

        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "inventory_quantity": 4.0,
                "location_id": self.location_src.id,
                "product_id": self.product.id,
            }
        )._apply_inventory()
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "inventory_quantity": 6.0,
                "location_id": self.location_src2.id,
                "product_id": self.product.id,
            }
        )._apply_inventory()
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "inventory_quantity": 7.0,
                "location_id": self.location_src_shelf.id,
                "product_id": self.product.id,
            }
        )._apply_inventory()
        move = self._create_outgoing_move(12)
        move = self._create_outgoing_move(1)
        self.assertEqual(move.state, "confirmed")
        self.product.invalidate_recordset()
        self.assertEqual(
            7.0, self.product.with_context(location=self.shelf.id).quantity_to_replenish
        )

    def test_available_on_one_stock_location_with_shelf(self):
        """
        Create a second stock location
            - Stock
                - Shelf
        Create an orderpoint for that particular location
        Set stock on replenishment locations (4.0 and 6.0) and on shelf
        one.

        Create three outgoing moves on:
            - stock (12.0)
            - stock (1.0)
            - shelf (5.0)

        Check that the global quantity to replenish is == 15.0:
            - 10.0 for stock
            - 5.0 for shelf

        """
        self.shelf = self.env["stock.location"].create(
            {"name": "Shelf to Replenish", "location_id": self.location_dest.id}
        )
        self.location_dest = self.shelf
        (
            self.orderpoint_shelf,
            self.location_src_shelf,
        ) = self._create_orderpoint_complete("Shelf Replenishment", trigger="manual")

        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "inventory_quantity": 4.0,
                "location_id": self.location_src.id,
                "product_id": self.product.id,
            }
        )._apply_inventory()
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "inventory_quantity": 6.0,
                "location_id": self.location_src2.id,
                "product_id": self.product.id,
            }
        )._apply_inventory()
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "inventory_quantity": 7.0,
                "location_id": self.location_src_shelf.id,
                "product_id": self.product.id,
            }
        )._apply_inventory()
        self.location_dest = self.warehouse.lot_stock_id
        move = self._create_outgoing_move(12)
        move = self._create_outgoing_move(1)
        self.assertEqual(move.state, "confirmed")

        self.location_dest = self.shelf
        move = self._create_outgoing_move(5.0)
        self.product.invalidate_recordset()
        self.assertEqual(15.0, self.product.quantity_to_replenish)

        # Check the replenishment value for shelf location only
        self.assertEqual(
            5.0, self.product.with_context(location=self.shelf.id).quantity_to_replenish
        )

        # We are not in shelf location context
        product = self.product.search([("quantity_to_replenish", "=", 5.0)])
        self.assertFalse(self.product.id in product.ids)

        # We are in shelf location context
        product = self.product.with_context(location=self.shelf.id).search(
            [("quantity_to_replenish", "=", 5.0)]
        )
        self.assertTrue(self.product.id in product.ids)

    def test_action(self):
        action = self.product.action_open_replenishments()
        self.assertIn(
            ("product_id", "=", self.product.id),
            action["domain"],
        )
