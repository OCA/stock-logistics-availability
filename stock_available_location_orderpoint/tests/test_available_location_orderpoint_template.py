# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.fields import Command

from odoo.addons.stock_location_orderpoint.tests.common import (
    TestLocationOrderpointCommon,
)


class TestStockAvailableLocationOrderpointTemplate(TestLocationOrderpointCommon):
    """
    Specific test cases for product templates
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.template = cls.product.product_tmpl_id
        cls.attribute = cls.env["product.attribute"].create(
            {"name": "Attribute 1", "create_variant": "always"}
        )
        cls.attribute_2 = cls.env["product.attribute"].create(
            {
                "name": "Attribute 2",
                "create_variant": "always",
            }
        )
        cls.attribute_value = cls.env["product.attribute.value"].create(
            {"name": "Value 1", "attribute_id": cls.attribute.id}
        )
        cls.attribute_value_2 = cls.env["product.attribute.value"].create(
            {"name": "Value 2", "attribute_id": cls.attribute.id}
        )
        cls.attribute_2_value_1 = cls.env["product.attribute.value"].create(
            {"name": "Value 1", "attribute_id": cls.attribute_2.id}
        )
        cls.template.write(
            {
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": cls.attribute.id,
                            "value_ids": [
                                Command.link(cls.attribute_value.id),
                                Command.link(cls.attribute_value_2.id),
                            ],
                        }
                    ),
                    Command.create(
                        {
                            "attribute_id": cls.attribute_2.id,
                            "value_ids": [Command.link(cls.attribute_2_value_1.id)],
                        }
                    ),
                ],
            }
        )
        cls.product = cls.template.product_variant_ids[0]
        cls.product_2 = cls.template.product_variant_ids[1]

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
        self.assertEqual(move.state, "confirmed")
        move = self._create_outgoing_move(1)
        self.assertEqual(move.state, "confirmed")
        self.product = self.product_2
        self._create_outgoing_move(10)
        self._create_outgoing_move(1)
        self.template.invalidate_recordset()
        self.assertEqual(0.0, self.template.quantity_to_replenish)
        templates = self.template.search([("quantity_to_replenish", "=", 0.0)])
        self.assertTrue(self.template.id in templates.ids)

    def test_available_on_replenish(self):
        """
        Set stock on:
            - Replenish 1 for product 1 : 6.0
            - Replenish 1 for product 2 : 5.0

        Create outgoing moves:
            - Product 1: 13.0
            - Product 2: 11.0

        Check that template repenish quantity is:
            - 11.0 (6.0 + 5.0)
        """
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "inventory_quantity": 6.0,
                "location_id": self.location_src.id,
                "product_id": self.product.id,
            }
        )._apply_inventory()
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "inventory_quantity": 5.0,
                "location_id": self.location_src.id,
                "product_id": self.product_2.id,
            }
        )._apply_inventory()
        move = self._create_outgoing_move(12)
        move = self._create_outgoing_move(1)
        self.assertEqual(move.state, "confirmed")
        self.product = self.product_2
        self._create_outgoing_move(10)
        self._create_outgoing_move(1)
        self.template.invalidate_recordset()
        self.assertEqual(11.0, self.template.quantity_to_replenish)
        templates = self.template.search([("quantity_to_replenish", "=", 11.0)])
        self.assertTrue(self.template.id in templates.ids)

    def test_available_on_multi_replenish(self):
        """
        Set stock on:
            - Replenish 1 for product 1 : 6.0
            - Replenish 2 for product 2 : 7.0

        Create outgoing moves:
            - Product 1: 13.0
            - Product 2: 11.0

        Check that template repenish quantity is:
            - 13.0 (6.0 + 7.0)
        """
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "inventory_quantity": 6.0,
                "location_id": self.location_src.id,
                "product_id": self.product.id,
            }
        )._apply_inventory()
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "inventory_quantity": 7.0,
                "location_id": self.location_src2.id,
                "product_id": self.product_2.id,
            }
        )._apply_inventory()
        move = self._create_outgoing_move(12)
        move = self._create_outgoing_move(1)
        self.assertEqual(move.state, "confirmed")

        self.product = self.product_2
        move = self._create_outgoing_move(10)
        move = self._create_outgoing_move(1)
        self.assertEqual(move.state, "confirmed")
        self.template.invalidate_recordset()
        self.assertEqual(13.0, self.template.quantity_to_replenish)
        templates = self.template.search([("quantity_to_replenish", "=", 13.0)])
        self.assertTrue(self.template.id in templates.ids)

    def test_available_on_one_location(self):
        """
        Set stock on replenishment locations (4.0 and 6.0)

        Create two outgoing moves:
            - Product 1 : 13.0
            - Product 2 : 10.0

        Replenishment quantity should be == 10.0 (6.0 + 4.0)
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
        move = self._create_outgoing_move(13)
        self.assertEqual(move.state, "confirmed")

        self.product = self.product_2
        move = self._create_outgoing_move(10)
        self.assertEqual(move.state, "confirmed")

        self.template.invalidate_recordset()
        self.assertEqual(
            10.0,
            self.template.with_context(
                location=self.location_dest.id
            ).quantity_to_replenish,
        )
        templates = self.template.search([("quantity_to_replenish", "=", 10.0)])
        self.assertTrue(self.template.id in templates.ids)

    def test_available_on_one_shelf_location(self):
        """
        Create a second stock location
            - Stock
                - Shelf
        Create an orderpoint for that particular location
        Set stock on replenishment locations for product 1 only:
            - Replenishment 1 : 4.0
            - Replenishment 2 : 6.0
            - Replenishment Shelf: 7.0

        Create outgoing moves:
            - Product 1: 2.0
            - Product 2: 5.0

        The replenishment quantity should be for product 1 only == 2.0

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
        move = self._create_outgoing_move(2)
        self.assertEqual(move.state, "confirmed")

        self.product = self.product_2
        move = self._create_outgoing_move(5)
        self.assertEqual(move.state, "confirmed")
        self.template.invalidate_recordset()
        self.assertEqual(
            2.0,
            self.template.with_context(location=self.shelf.id).quantity_to_replenish,
        )
        templates = self.template.search([("quantity_to_replenish", "=", 2.0)])
        self.assertTrue(self.template.id in templates.ids)

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
        self.template.invalidate_recordset()
        self.assertEqual(15.0, self.template.quantity_to_replenish)

        # We are in global context
        templates = self.template.search([("quantity_to_replenish", "=", 15.0)])
        self.assertTrue(self.template.id in templates.ids)

        # We are in shelf context
        self.template.invalidate_recordset()
        templates = self.template.with_context(location=self.shelf.id).search(
            [("quantity_to_replenish", "=", 5.0)]
        )
        self.assertTrue(self.template.id in templates.ids)

    def test_action(self):
        action = self.template.action_open_replenishments()
        self.assertIn(
            ("product_id", "in", self.template.product_variant_ids.ids),
            action["domain"],
        )
