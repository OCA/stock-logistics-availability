# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests.common import TransactionCase


class TestStockLogisticsWarehouse(TransactionCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.move_model = cls.env["stock.move"]
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product Test",
                "uom_id": cls.uom_unit.id,
                "type": "consu",
                "is_storable": True,
            }
        )
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.pack_location = cls.env.ref("stock.location_pack_zone")
        cls.pack_location.usage = "view"
        (cls.stock_location | cls.pack_location).write({"active": True})

        cls.pack_child_location = cls.env["stock.location"].create(
            {
                "name": "Pack Child Location",
                "location_id": cls.pack_location.id,
                "usage": "internal",
            }
        )

    def _receive(self, location, qty):
        move = self.move_model.create(
            {
                "location_id": self.supplier_location.id,
                "location_dest_id": location.id,
                "product_id": self.product.id,
                "product_uom_qty": qty,
            }
        )
        move._action_confirm()
        move._action_assign()
        move.move_line_ids.write({"quantity": qty, "picked": True})
        move._action_done()

    def _get_immediately_usable_qty(self, product, **context):
        location_ids = (self.stock_location | self.pack_location).ids
        return product.with_context(
            location=location_ids, **context
        ).immediately_usable_qty

    def test01(self):
        location_ids = (self.stock_location | self.pack_location).ids
        ctx_loc = {"location": location_ids}
        move_stock = self.move_model.create(
            {
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 15,
            }
        )
        move_pack = self.move_model.create(
            {
                "location_id": self.supplier_location.id,
                "location_dest_id": self.pack_child_location.id,
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 5,
            }
        )
        (move_stock | move_pack)._action_confirm()
        (move_stock | move_pack)._action_assign()
        move_stock.move_line_ids.write({"quantity": 7.0, "picked": True})
        move_stock._action_done()
        q = self.product.with_context(**ctx_loc).immediately_usable_qty
        self.assertEqual(q, 7.0)
        move_pack.move_line_ids.write({"quantity": 4.0, "picked": True})
        move_pack._action_done()
        q = self.product.with_context(**ctx_loc).immediately_usable_qty
        self.assertEqual(q, 11.0)
        self.pack_location.exclude_from_immediately_usable_qty = True
        self.product.invalidate_recordset()  # force recompute
        q = self.product.with_context(**ctx_loc).immediately_usable_qty
        self.assertEqual(q, 7.0)
        # test with a date in the past
        self.product.invalidate_recordset()
        q = self.product.with_context(
            **ctx_loc, to_date="2023-01-01"
        ).immediately_usable_qty
        self.assertEqual(q, 0.0)

    def test_get_excluded_location_ids(self):
        self.pack_location.exclude_from_immediately_usable_qty = True
        excluded_location_ids = (
            self.product._get_location_ids_excluded_from_immediately_usable_qty()
        )
        self.assertEqual(
            set(excluded_location_ids),
            set(self.pack_location.ids + self.pack_child_location.ids),
        )

    def test_delivery_reserved_in_excluded_location(self):
        """A delivery reserved in an excluded location is not deduced twice.

        The immediately usable quantity is the quantity on hand, minus the
        outgoing quantity. The delivery is outgoing, so it is already deduced
        from the quantity on hand: the goods it takes from the excluded location
        must not be deduced a second time as goods of the excluded location.

        Scenario:
            1. Have 10 units in stock and 5 units in the excluded location.
            2. Confirm a delivery of 5 units, reserved in the excluded location.
        Expected:
            - The 10 units in stock are still immediately usable.
        """
        self.pack_location.exclude_from_immediately_usable_qty = True
        quant_model = self.env["stock.quant"]
        quant_model._update_available_quantity(self.product, self.stock_location, 10)
        quant_model._update_available_quantity(
            self.product, self.pack_child_location, 5
        )
        self.assertEqual(self._get_immediately_usable_qty(self.product), 10)
        delivery = self.move_model.create(
            {
                "location_id": self.pack_child_location.id,
                "location_dest_id": self.customer_location.id,
                "product_id": self.product.id,
                "product_uom_qty": 5,
            }
        )
        delivery._action_confirm()
        delivery._action_assign()
        self.assertEqual(delivery.state, "assigned")
        self.assertEqual(self._get_immediately_usable_qty(self.product), 10)

    def test_transfer_from_excluded_location(self):
        """Goods leaving an excluded location are not usable before they arrive.

        A transfer from the excluded location to the stock is incoming for the
        stock. Like goods arriving from a supplier, its goods are not
        immediately usable until they are in stock: they must not be counted as
        no longer excluded as soon as the transfer is confirmed.

        Scenario:
            1. Have 10 units in stock and 5 units in the excluded location.
            2. Confirm a transfer of the 5 units from the excluded location to
               the stock, reserved in the excluded location.
        Expected:
            - Only the 10 units in stock are immediately usable.
        """
        self.pack_location.exclude_from_immediately_usable_qty = True
        quant_model = self.env["stock.quant"]
        quant_model._update_available_quantity(self.product, self.stock_location, 10)
        quant_model._update_available_quantity(
            self.product, self.pack_child_location, 5
        )
        transfer = self.move_model.create(
            {
                "location_id": self.pack_child_location.id,
                "location_dest_id": self.stock_location.id,
                "product_id": self.product.id,
                "product_uom_qty": 5,
            }
        )
        transfer._action_confirm()
        transfer._action_assign()
        self.assertEqual(transfer.state, "assigned")
        self.assertEqual(self._get_immediately_usable_qty(self.product), 10)

    def test_date_without_time(self):
        """A date without time covers the whole day, for the excluded locations too.

        Odoo reads a date without time as the end of that day, so the goods
        received today are on hand at today's date. The goods received today in
        the excluded location must be deduced at today's date as well.

        Scenario:
            1. Receive 10 units in stock and 5 units in the excluded location,
               today.
            2. Get the immediately usable quantity at today's date, without time.
        Expected:
            - Only the 10 units in stock are immediately usable.
        """
        self.pack_location.exclude_from_immediately_usable_qty = True
        self._receive(self.stock_location, 10)
        self._receive(self.pack_child_location, 5)
        today = fields.Date.to_string(fields.Date.today())
        self.assertEqual(
            self._get_immediately_usable_qty(self.product, to_date=today), 10
        )

    def test_lot_in_context(self):
        """Only the goods of the lot asked for are deduced.

        Scenario:
            1. Have 10 units of lot A in stock, and 5 units of lot B in the
               excluded location.
            2. Get the immediately usable quantity of lot A.
        Expected:
            - The 10 units of lot A are immediately usable: the goods of lot B
              in the excluded location are not deduced from them.
        """
        self.pack_location.exclude_from_immediately_usable_qty = True
        product = self.env["product.product"].create(
            {
                "name": "Lot Product Test",
                "type": "consu",
                "is_storable": True,
                "tracking": "lot",
            }
        )
        lot_a, lot_b = self.env["stock.lot"].create(
            [
                {"name": "Lot A", "product_id": product.id},
                {"name": "Lot B", "product_id": product.id},
            ]
        )
        quant_model = self.env["stock.quant"]
        quant_model._update_available_quantity(
            product, self.stock_location, 10, lot_id=lot_a
        )
        quant_model._update_available_quantity(
            product, self.pack_child_location, 5, lot_id=lot_b
        )
        self.assertEqual(self._get_immediately_usable_qty(product, lot_id=lot_a.id), 10)
