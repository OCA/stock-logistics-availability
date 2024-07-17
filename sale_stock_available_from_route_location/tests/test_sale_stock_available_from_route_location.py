# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestSaleAvailableFromRouteLocation(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Storable product", "detailed_type": "product"}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Mr. Odoo"})
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.warehouse = cls.stock_location.warehouse_id
        cls.test_location = cls.env["stock.location"].create(
            {
                "name": "Test Location",
                "warehouse_id": cls.warehouse.id,
            }
        )
        cls.test_route = cls.env["stock.route"].create(
            {
                "name": "Output to Customers",
                "sale_selectable": True,
            }
        )
        cls.stock_rule = cls.env["stock.rule"].create(
            {
                "name": "Test location to Customers",
                "route_id": cls.test_route.id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                "location_src_id": cls.test_location.id,
                "action": "pull",
                "picking_type_id": cls.warehouse.out_type_id.id,
            },
        )
        # Update quantity in Stock location
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.stock_location, 10
        )
        cls.env["stock.quant"]._update_reserved_quantity(
            cls.product, cls.stock_location, 3
        )
        # Update quantity in Test Location
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.test_location, 20
        )
        cls.env["stock.quant"]._update_reserved_quantity(
            cls.product, cls.test_location, 10
        )
        cls.so = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": cls.product.name,
                            "product_id": cls.product.id,
                            "product_uom_qty": 1,
                            "product_uom": cls.product.uom_id.id,
                            "price_unit": cls.product.list_price,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": cls.product.name,
                            "product_id": cls.product.id,
                            "product_uom_qty": 2,
                            "product_uom": cls.product.uom_id.id,
                            "price_unit": cls.product.list_price,
                        },
                    ),
                ],
            }
        )
        cls.lines = cls.so.order_line

    def test_sale_lines_without_defined_route(self):
        self.lines._compute_qty_at_date()
        # Default location to consider is lot_stock_id of warehouse if not defined route
        # Checking line 1
        self.assertEqual(self.lines[0].virtual_available_at_date, 10)
        self.assertEqual(self.lines[0].free_qty_today, 7)
        self.assertEqual(self.lines[0].qty_available_today, 10)
        self.assertEqual(self.lines[0].qty_to_deliver, 1)
        # Checking line 2
        # Line 2 will be calculated based on line 1 also
        # because line 1 has the same products and locations to consider
        self.assertEqual(self.lines[1].virtual_available_at_date, 9)
        self.assertEqual(self.lines[1].free_qty_today, 6)
        self.assertEqual(self.lines[1].qty_available_today, 9)
        self.assertEqual(self.lines[1].qty_to_deliver, 2)

    def test_sale_lines_with_defined_route(self):
        self.lines.write({"route_id": self.test_route.id})
        self.lines._compute_qty_at_date()
        # Now location to consider is Test location (got from route)
        # Checking line 1
        self.assertEqual(self.lines[0].virtual_available_at_date, 20)
        self.assertEqual(self.lines[0].free_qty_today, 10)
        self.assertEqual(self.lines[0].qty_available_today, 20)
        self.assertEqual(self.lines[0].qty_to_deliver, 1)
        # Checking line 2
        # Line 2 will be calculated based on line 1
        # because line 1 has same products and locations to consider
        self.assertEqual(self.lines[1].virtual_available_at_date, 19)
        self.assertEqual(self.lines[1].free_qty_today, 9)
        self.assertEqual(self.lines[1].qty_available_today, 19)
        self.assertEqual(self.lines[1].qty_to_deliver, 2)

    def test_sale_lines_with_different_routes(self):
        self.lines[1].write({"route_id": self.test_route.id})
        self.lines._compute_qty_at_date()
        # Checking line 1
        # Default location to consider is lot_stock_id of warehouse if not defined route
        self.assertEqual(self.lines[0].virtual_available_at_date, 10)
        self.assertEqual(self.lines[0].free_qty_today, 7)
        self.assertEqual(self.lines[0].qty_available_today, 10)
        self.assertEqual(self.lines[0].qty_to_deliver, 1)
        # Checking line 2
        # Now location to consider is Test location (got from route)
        self.assertEqual(self.lines[1].virtual_available_at_date, 20)
        self.assertEqual(self.lines[1].free_qty_today, 10)
        self.assertEqual(self.lines[1].qty_available_today, 20)
        self.assertEqual(self.lines[1].qty_to_deliver, 2)
