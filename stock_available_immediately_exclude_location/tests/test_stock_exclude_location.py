# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

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
                "type": "product",
            }
        )
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
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

    def test01(self):
        location_ids = (self.stock_location | self.pack_location).ids
        ctx_loc = {"location": location_ids}
        move_stock = self.move_model.create(
            {
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
                "name": "MOVE STOCK ",
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 15,
            }
        )
        move_pack = self.move_model.create(
            {
                "location_id": self.supplier_location.id,
                "location_dest_id": self.pack_child_location.id,
                "name": "MOVE PACK ",
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 5,
            }
        )
        (move_stock | move_pack)._action_confirm()
        (move_stock | move_pack)._action_assign()
        move_stock.move_line_ids.write({"qty_done": 7.0})
        move_stock._action_done()
        q = self.product.with_context(**ctx_loc).immediately_usable_qty
        self.assertEqual(q, 7.0)
        move_pack.move_line_ids.write({"qty_done": 4.0})
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
