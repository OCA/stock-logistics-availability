from odoo.tests import tagged

from .common import ConsignedStockHttpCommon


@tagged("post_install", "-at_install")
class TestPortalConsignedStockHttp(ConsignedStockHttpCommon):
    def test_anonymous_user_is_redirected_to_login(self):
        response = self.url_open("/my/consigned-stock", allow_redirects=False)
        self.assertIn(response.status_code, (302, 303))
        self.assertIn("/web/login", response.headers.get("Location", ""))

    def test_portal_user_can_access_consigned_stock(self):
        self.authenticate(self.portal_user.login, "consigned.portal")
        response = self.url_open("/my/consigned-stock")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Consigned Alpha", response.content)
        self.assertNotIn(b"Other Owner Product", response.content)

    def test_portal_home_shows_my_consigned_stock_access(self):
        self.authenticate(self.portal_user.login, "consigned.portal")
        response = self.url_open("/my/home")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"My Consigned Stock", response.content)
        self.assertIn(b"/my/consigned-stock", response.content)

    def test_invalid_sortby_does_not_error(self):
        self.authenticate(self.portal_user.login, "consigned.portal")
        response = self.url_open("/my/consigned-stock?sortby=not-a-sort-key")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Consigned Alpha", response.content)

    def test_invalid_warehouse_id_does_not_error_nor_expand_scope(self):
        self.authenticate(self.portal_user.login, "consigned.portal")
        response = self.url_open("/my/consigned-stock?warehouse_id=not-a-number")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Other Owner Product", response.content)

    def test_foreign_warehouse_id_is_ignored(self):
        self.authenticate(self.portal_user.login, "consigned.portal")
        response = self.url_open(
            f"/my/consigned-stock?warehouse_id={self.other_company_warehouse.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Consigned Alpha", response.content)
        self.assertNotIn(b"Other Owner Product", response.content)
