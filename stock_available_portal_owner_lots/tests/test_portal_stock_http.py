from unittest.mock import patch

from odoo.tests import tagged

from .common import ConsignedStockLotsHttpCommon


@tagged("post_install", "-at_install")
class TestPortalConsignedStockLotsHttp(ConsignedStockLotsHttpCommon):
    def test_anonymous_user_redirected(self):
        response = self.url_open(
            f"/my/consigned-stock/lots/{self.product_a.id}", allow_redirects=False
        )
        self.assertIn(response.status_code, (302, 303))
        self.assertIn("/web/login", response.headers.get("Location", ""))

    def test_portal_user_can_access_lots(self):
        self.authenticate(self.portal_user.login, "consigned.portal")
        response = self.url_open(f"/my/consigned-stock/lots/{self.product_a.id}")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"LOT-A1", response.content)
        self.assertIn(b"LOT-A2", response.content)
        self.assertNotIn(b"LOT-B1", response.content)

    def test_portal_user_can_paginate_lots(self):
        self.authenticate(self.portal_user.login, "consigned.portal")
        target_path = (
            "odoo.addons.stock_available_portal_owner.controllers."
            "portal.ConsignedStockCustomerPortal._items_per_page"
        )

        with patch(target_path, 1):
            response_page_1 = self.url_open(
                f"/my/consigned-stock/lots/{self.product_a.id}?page=1"
            )
            self.assertEqual(response_page_1.status_code, 200)

            has_lot1 = b"LOT-A1" in response_page_1.content
            has_lot2 = b"LOT-A2" in response_page_1.content
            self.assertTrue(has_lot1 ^ has_lot2)

            response_page_2 = self.url_open(
                f"/my/consigned-stock/lots/{self.product_a.id}?page=2"
            )
            self.assertEqual(response_page_2.status_code, 200)

            has_lot1_p2 = b"LOT-A1" in response_page_2.content
            has_lot2_p2 = b"LOT-A2" in response_page_2.content
            self.assertTrue(has_lot1_p2 ^ has_lot2_p2)
            self.assertNotEqual(has_lot1, has_lot1_p2)

    def test_warehouse_isolation(self):
        self.authenticate(self.portal_user.login, "consigned.portal")
        response = self.url_open(
            f"/my/consigned-stock/lots/{self.product_a.id}?warehouse_id={self.warehouse.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"LOT-A1", response.content)
        response_empty = self.url_open(
            f"/my/consigned-stock/lots/{self.product_a.id}?warehouse_id={self.other_warehouse.id}"
        )
        self.assertNotIn(b"LOT-A1", response_empty.content)
        self.assertNotIn(b"LOT-A2", response_empty.content)
