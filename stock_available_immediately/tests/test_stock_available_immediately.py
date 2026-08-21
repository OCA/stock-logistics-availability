# Copyright 2014 Camptocamp, Akretion, Numérigraphe
# Copyright 2016 Sodexis
# Copyright 2019 Sergio Díaz <sergiodm.1989@gmail.com>
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.orm.commands import Command

from odoo.addons.base.tests.common import BaseCommon


class TestStockLogisticsWarehouse(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.attribute_color = cls.env["product.attribute"].create(
            {"name": "stock_available_immediately-Color"}
        )
        cls.attribute_color_white = cls.env["product.attribute.value"].create(
            {
                "name": "stock_available_immediately-White",
                "attribute_id": cls.attribute_color.id,
            }
        )
        cls.attribute_color_black = cls.env["product.attribute.value"].create(
            {
                "name": "stock_available_immediately-Black",
                "attribute_id": cls.attribute_color.id,
            }
        )
        # Create product template with 2 variant
        cls.templateAB = cls.env["product.template"].create(
            {
                "name": "templAB",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "type": "consu",
                "is_storable": True,
            }
        )
        cls.env["product.template.attribute.line"].create(
            {
                "product_tmpl_id": cls.templateAB.id,
                "attribute_id": cls.attribute_color.id,
                "value_ids": [
                    Command.set(
                        [
                            cls.attribute_color_white.id,
                            cls.attribute_color_black.id,
                        ],
                    )
                ],
            }
        )
        cls.productA = cls.templateAB.product_variant_ids[0]
        cls.productB = cls.templateAB.product_variant_ids[1]

    def test01_stock_levels(self):
        """
        Checking that immediately_usable_qty actually reflects the variations
        in stock, both on product and template.
        """
        moveObj = self.env["stock.move"]
        supplier_location = self.env.ref("stock.stock_location_suppliers")
        stock_location = self.env.ref("stock.stock_location_stock")
        customer_location = self.env.ref("stock.stock_location_customers")

        # Create a stock move from INCOMING to STOCK
        stockMoveInA = moveObj.create(
            {
                "location_id": supplier_location.id,
                "location_dest_id": stock_location.id,
                "product_id": self.productA.id,
                "product_uom": self.productA.uom_id.id,
                "product_uom_qty": 2,
            }
        )
        stockMoveInB = moveObj.create(
            {
                "location_id": supplier_location.id,
                "location_dest_id": stock_location.id,
                "product_id": self.productB.id,
                "product_uom": self.productB.uom_id.id,
                "product_uom_qty": 3,
            }
        )
        self.assertEqual(self.productA.immediately_usable_qty, 0)
        self.assertEqual(self.templateAB.immediately_usable_qty, 0)

        stockMoveInA._action_confirm()
        self.assertEqual(self.productA.immediately_usable_qty, 0)
        self.assertEqual(self.templateAB.immediately_usable_qty, 0)

        stockMoveInA._action_assign()
        self.assertEqual(self.productA.immediately_usable_qty, 0)
        self.assertEqual(self.templateAB.immediately_usable_qty, 0)

        stockMoveInA.move_line_ids.write({"quantity": 2.0, "picked": True})
        stockMoveInA._action_done()
        self.assertEqual(self.productA.immediately_usable_qty, 2)
        self.assertEqual(self.templateAB.immediately_usable_qty, 2)

        # will directly trigger action_done on productB
        stockMoveInB._action_confirm()
        stockMoveInB._action_assign()
        stockMoveInB.move_line_ids.write({"quantity": 3.0, "picked": True})
        stockMoveInB._action_done()
        self.assertEqual(self.productA.immediately_usable_qty, 2)
        self.assertEqual(self.productB.immediately_usable_qty, 3)
        self.assertEqual(self.templateAB.immediately_usable_qty, 5)
        # Create a stock move from STOCK to CUSTOMER
        stockMoveOutA = moveObj.create(
            {
                "location_id": stock_location.id,
                "location_dest_id": customer_location.id,
                "product_id": self.productA.id,
                "product_uom": self.productA.uom_id.id,
                "product_uom_qty": 1,
                "state": "confirmed",
            }
        )
        stockMoveOutA._action_confirm()
        stockMoveOutA._action_assign()
        stockMoveOutA.move_line_ids.write({"quantity": 1.0, "picked": True})
        stockMoveOutA._action_done()
        self.assertEqual(self.productA.immediately_usable_qty, 1)
        self.assertEqual(self.templateAB.immediately_usable_qty, 4)
        # Potential Qty is set as 0.0 by default
        self.assertEqual(self.templateAB.potential_qty, 0.0)
        self.assertEqual(self.productA.potential_qty, 0.0)
