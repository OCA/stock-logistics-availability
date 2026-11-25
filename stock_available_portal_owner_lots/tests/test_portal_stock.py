from odoo.tests import tagged

from odoo.addons.stock_available_portal_owner.controllers.portal import (
    ConsignedStockCustomerPortal,
)
from odoo.addons.stock_available_portal_owner_lots.controllers.portal import (
    ConsignedStockCustomerPortalExtended,
)
from odoo.addons.website.tools import MockRequest

from .common import ConsignedStockLotsCommon


@tagged("post_install", "-at_install")
class TestPortalConsignedStock(ConsignedStockLotsCommon):
    def setUp(self):
        super().setUp()
        self.controller = ConsignedStockCustomerPortal()

    def _with_owner_request(self):
        return MockRequest(self.env(user=self.portal_user))

    def test_owner_is_resolved_from_portal_user(self):
        with self._with_owner_request():
            self.assertEqual(self.controller._get_consigned_stock_owner(), self.owner)

    def test_portal_home_consigned_stock_count(self):
        with self._with_owner_request():
            values = self.controller._prepare_home_portal_values(
                {"consigned_stock_count"}
            )
            expected_count = self.env["product.product"].search_count(
                self.controller._get_consigned_stock_product_domain(self.owner)
            )
        self.assertEqual(values["consigned_stock_count"], expected_count)

    def test_portal_home_consigned_stock_count_without_owner(self):
        self.portal_user.partner_id = None
        with self._with_owner_request():
            values = self.controller._prepare_home_portal_values(
                {"consigned_stock_count"}
            )
        self.assertEqual(values["consigned_stock_count"], "0")

    def test_portal_home_values_skip_count_when_not_requested(self):
        with self._with_owner_request():
            values = self.controller._prepare_home_portal_values(set())
        self.assertNotIn("consigned_stock_count", values)

    def test_portal_values_without_owner(self):
        self.portal_user.partner_id = False
        with self._with_owner_request():
            values = self.controller._prepare_consigned_stock_portal_values(
                page=3,
                sortby="name_desc",
                search="Alpha",
                search_in="name",
                warehouse_id="42",
            )
        self.assertEqual(values["page_name"], "consigned_stock")
        self.assertFalse(values["owner"])
        self.assertFalse(values["product_values"])
        self.assertFalse(values["warehouses"])
        self.assertEqual(values["pager"], {})
        self.assertEqual(values["search"], "Alpha")
        self.assertEqual(values["search_in"], "name")
        self.assertEqual(values["sortby"], "name_desc")
        self.assertEqual(values["warehouse_id"], "42")

    def test_product_listing_is_limited_to_owner_stock(self):
        with self._with_owner_request():
            products = self.env["product.product"].search(
                self.controller._get_consigned_stock_product_domain(self.owner)
            )
        self.assertEqual(
            products,
            self.product_a
            | self.product_b
            | self.product_shared
            | self.product_multi_wh
            | self.product_incoming,
        )
        self.assertNotIn(self.other_product, products)
        self.assertNotIn(self.product_unowned_only, products)

    def test_availability_magnitudes_are_available_for_listed_products(self):
        with self._with_owner_request():
            values = self.controller._prepare_consigned_stock_portal_values()
            product_value = next(
                pv for pv in values["product_values"] if pv["product"] == self.product_a
            )
        # Se le suman 10 a los valores originales por los lotes añadidos en el mixin
        self.assertEqual(product_value["qty_available"], 20.0)
        self.assertEqual(product_value["free_qty"], 18.0)
        self.assertEqual(product_value["incoming_qty"], 0)
        self.assertEqual(product_value["outgoing_qty"], 2)
        self.assertEqual(product_value["virtual_available"], 18.0)

    def test_search_by_name_and_reference(self):
        with self._with_owner_request():
            by_name = self.controller._prepare_consigned_stock_portal_values(
                search="Alpha", search_in="name"
            )["product_values"]
            by_reference = self.controller._prepare_consigned_stock_portal_values(
                search="CONS-BETA", search_in="reference"
            )["product_values"]
        self.assertEqual([pv["product"] for pv in by_name], [self.product_a])
        self.assertEqual([pv["product"] for pv in by_reference], [self.product_b])

    def test_search_all_matches_name_or_reference(self):
        with self._with_owner_request():
            by_name = self.controller._prepare_consigned_stock_portal_values(
                search="Alpha", search_in="all"
            )["product_values"]
            by_reference = self.controller._prepare_consigned_stock_portal_values(
                search="CONS-BETA", search_in="all"
            )["product_values"]
            no_match = self.controller._prepare_consigned_stock_portal_values(
                search="NO-SUCH-PRODUCT", search_in="all"
            )["product_values"]
        self.assertEqual([pv["product"] for pv in by_name], [self.product_a])
        self.assertEqual([pv["product"] for pv in by_reference], [self.product_b])
        self.assertFalse(no_match)

    def test_warehouse_filter_limits_listing(self):
        with self._with_owner_request():
            values = self.controller._prepare_consigned_stock_portal_values(
                warehouse_id=self.warehouse
            )
        products = {pv["product"] for pv in values["product_values"]}
        self.assertIn(self.product_a, products)
        self.assertNotIn(self.product_b, products)
        self.assertEqual(values["warehouses"], self.warehouse | self.other_warehouse)

    def test_invalid_warehouse_id_does_not_filter_listing(self):
        with self._with_owner_request():
            values = self.controller._prepare_consigned_stock_portal_values(
                warehouse_id="not-a-warehouse"
            )
        self.assertFalse(values["warehouse"])
        self.assertEqual(values["warehouse_id"], "")
        products = {pv["product"] for pv in values["product_values"]}
        self.assertIn(self.product_a, products)
        self.assertIn(self.product_b, products)

    def test_sorting(self):
        with self._with_owner_request():
            values = self.controller._prepare_consigned_stock_portal_values(
                sortby="name_desc"
            )
        products = [pv["product"] for pv in values["product_values"]]
        filtered = [p for p in products if p in (self.product_a, self.product_b)]
        self.assertEqual(filtered, [self.product_b, self.product_a])

    def test_pagination(self):
        self.controller._items_per_page = 1
        with self._with_owner_request():
            first_page = self.controller._prepare_consigned_stock_portal_values(page=1)
            second_page = self.controller._prepare_consigned_stock_portal_values(page=2)
            total_products = self.env["product.product"].search_count(
                self.controller._get_consigned_stock_product_domain(self.owner)
            )
        self.assertEqual(len(first_page["product_values"]), 1)
        self.assertEqual(len(second_page["product_values"]), 1)
        self.assertNotEqual(
            first_page["product_values"][0]["product"],
            second_page["product_values"][0]["product"],
        )
        self.assertEqual(first_page["pager"]["page_count"], total_products)

    def test_owner_without_visible_stock_gets_empty_listing(self):
        owner_without_stock = self.env["res.partner"].create({"name": "Empty Owner"})
        with self._with_owner_request():
            domain = self.controller._get_consigned_stock_product_domain(
                owner_without_stock
            )
        self.assertFalse(self.env["product.product"].search(domain))

    def test_warehouses_without_owner_stock_returns_empty_recordset(self):
        owner_without_stock = self.env["res.partner"].create({"name": "Empty Owner"})
        with self._with_owner_request():
            warehouses = self.controller._get_consigned_stock_warehouses(
                owner_without_stock
            )
        self.assertFalse(warehouses)
        self.assertEqual(warehouses, self.env["stock.warehouse"])

    def test_search_by_reference_partial_match(self):
        with self._with_owner_request():
            product_values = self.controller._prepare_consigned_stock_portal_values(
                search="cons-", search_in="reference"
            )["product_values"]
        self.assertEqual(
            {pv["product"] for pv in product_values},
            {
                self.product_a,
                self.product_b,
                self.product_shared,
                self.product_multi_wh,
                self.product_incoming,
            },
        )

    def test_search_by_reference_no_match(self):
        with self._with_owner_request():
            product_values = self.controller._prepare_consigned_stock_portal_values(
                search="OTHER-001", search_in="reference"
            )["product_values"]
        self.assertFalse(product_values)

    def _get_product_value(self, values, product):
        return next(pv for pv in values["product_values"] if pv["product"] == product)

    def test_qty_available_is_isolated_by_owner(self):
        with self._with_owner_request():
            values = self.controller._prepare_consigned_stock_portal_values(
                search="CONS-SHARED", search_in="reference"
            )
        product_value = self._get_product_value(values, self.product_shared)
        self.assertEqual(product_value["qty_available"], 10)
        self.assertEqual(product_value["free_qty"], 10)

    def test_incoming_qty_is_isolated_by_owner(self):
        with self._with_owner_request():
            values = self.controller._prepare_consigned_stock_portal_values(
                search="CONS-INCOMING", search_in="reference"
            )
        product_value = self._get_product_value(values, self.product_incoming)
        self.assertEqual(product_value["incoming_qty"], 10)
        self.assertEqual(product_value["qty_available"], 0)
        self.assertEqual(product_value["virtual_available"], 10)

    def test_product_without_quant_or_move_line_is_not_listed(self):
        with self._with_owner_request():
            values = self.controller._prepare_consigned_stock_portal_values(
                search="CONS-PENDING", search_in="reference"
            )
        self.assertFalse(values["product_values"])

    def test_owners_are_isolated_from_each_other(self):
        with self._with_owner_request():
            owner_a_products = {
                pv["product"]
                for pv in self.controller._prepare_consigned_stock_portal_values()[
                    "product_values"
                ]
            }
        with MockRequest(self.env(user=self.other_portal_user)):
            owner_b_products = {
                pv["product"]
                for pv in self.controller._prepare_consigned_stock_portal_values()[
                    "product_values"
                ]
            }
        self.assertNotIn(self.other_product, owner_a_products)
        self.assertNotIn(self.product_a, owner_b_products)
        self.assertIn(self.other_product, owner_b_products)

    def test_stock_without_owner_is_not_visible(self):
        with self._with_owner_request():
            domain = self.controller._get_consigned_stock_product_domain(self.owner_a)
        products = self.env["product.product"].search(domain)
        self.assertNotIn(self.product_unowned_only, products)

    def test_other_company_stock_is_not_visible(self):
        with self._with_owner_request():
            values = self.controller._prepare_consigned_stock_portal_values(
                search="CONS-ALPHA", search_in="reference"
            )
        product_value = self._get_product_value(values, self.product_a)
        # El stock pasó de 10 a 20 tras inyectar los lotes en el mixin
        self.assertEqual(product_value["qty_available"], 20.0)

    def test_prepare_consigned_stock_by_lot_values_without_owner(self):
        self.controller = ConsignedStockCustomerPortalExtended()

        self.portal_user.partner_id = False

        with self._with_owner_request():
            values = self.controller._prepare_consigned_stock_by_lot_portal_values(
                product_id=self.product_a.id,
                search="Alpha",
                search_in="lot",
                sortby="name_desc",
            )

        self.assertEqual(values["page_name"], "consigned_stock_by_lot")
        self.assertFalse(values["owner"])
        self.assertEqual(values["product_id"], self.product_a.id)
        self.assertIsNone(values["product"])
        self.assertFalse(values["lot_ids"])
        self.assertEqual(values["lot_ids"]._name, "stock.lot")
        self.assertEqual(values["pager"], {})
        self.assertEqual(values["search"], "Alpha")
        self.assertEqual(values["search_in"], "lot")
        self.assertEqual(values["sortby"], "name_desc")

    def test_consigned_stock_by_lot_search_in_all(self):
        self.controller = ConsignedStockCustomerPortalExtended()
        with self._with_owner_request():
            values = self.controller._prepare_consigned_stock_by_lot_portal_values(
                product_id=self.product_a.id, search="A1", search_in="all"
            )
        self.assertIn(self.lot_a1, values["lot_ids"])
        self.assertNotIn(self.lot_a2, values["lot_ids"])

    def test_consigned_stock_by_lot_search_in_lot(self):
        self.controller = ConsignedStockCustomerPortalExtended()
        with self._with_owner_request():
            values = self.controller._prepare_consigned_stock_by_lot_portal_values(
                product_id=self.product_a.id, search="A2", search_in="lot"
            )
        self.assertNotIn(self.lot_a1, values["lot_ids"])
        self.assertIn(self.lot_a2, values["lot_ids"])

    def test_consigned_stock_by_lot_sorting_fallback(self):
        self.controller = ConsignedStockCustomerPortalExtended()
        with self._with_owner_request():
            values = self.controller._prepare_consigned_stock_by_lot_portal_values(
                product_id=self.product_a.id, sortby="clave_invalida_de_ordenamiento"
            )
        self.assertEqual(values["sortby"], "name")
        self.assertEqual(values["lot_ids"][0], self.lot_a1)

    def test_consigned_stock_by_lot_date_filtering(self):
        self.controller = ConsignedStockCustomerPortalExtended()
        from datetime import timedelta

        from odoo import fields

        now = fields.Datetime.now()
        date_from = now + timedelta(days=10)
        date_to = now + timedelta(days=20)

        with self._with_owner_request():
            values = self.controller._prepare_consigned_stock_by_lot_portal_values(
                product_id=self.product_a.id, date_from=date_from, date_to=date_to
            )

        self.assertIn(self.lot_a2, values["lot_ids"])
        self.assertNotIn(self.lot_a1, values["lot_ids"])

    def test_consigned_stock_by_lot_warehouse_validation(self):
        self.controller = ConsignedStockCustomerPortalExtended()

        with self._with_owner_request():
            valid_values = (
                self.controller._prepare_consigned_stock_by_lot_portal_values(
                    product_id=self.product_a.id, warehouse_id=str(self.warehouse.id)
                )
            )
            self.assertEqual(valid_values["warehouse_id"], self.warehouse.id)

            value_error_values = (
                self.controller._prepare_consigned_stock_by_lot_portal_values(
                    product_id=self.product_a.id, warehouse_id="not-a-number"
                )
            )
            self.assertEqual(value_error_values["warehouse_id"], "")

            not_in_warehouses_values = (
                self.controller._prepare_consigned_stock_by_lot_portal_values(
                    product_id=self.product_a.id,
                    warehouse_id="999999",
                )
            )
            self.assertEqual(not_in_warehouses_values["warehouse_id"], "")
