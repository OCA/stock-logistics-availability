from odoo import Command
from odoo.tests import HttpCase, TransactionCase

PENDING_MOVE_STATE = "assigned"


class ConsignedStockDataMixin:
    @classmethod
    def _create_product(cls, name, code):
        return cls.env["product.product"].create(
            {
                "name": name,
                "default_code": code,
                "detailed_type": "product",
                "company_id": False,
            }
        )

    @classmethod
    def _create_quant(cls, product, location, owner, qty, company=None):
        return cls.env["stock.quant"].create(
            {
                "product_id": product.id,
                "location_id": location.id,
                "owner_id": owner.id if owner else False,
                "quantity": qty,
                "company_id": (company or cls.company).id,
            }
        )

    @classmethod
    def _create_pending_move(
        cls,
        product,
        location_id,
        location_dest_id,
        picking_type,
        owner=None,
        restrict_partner_id=None,
        qty=1.0,
    ):
        picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": location_id.id,
                "location_dest_id": location_dest_id.id,
                "owner_id": owner.id if owner else False,
            }
        )
        return cls.env["stock.move"].create(
            {
                "name": product.name,
                "product_id": product.id,
                "product_uom_qty": qty,
                "product_uom": product.uom_id.id,
                "location_id": location_id.id,
                "location_dest_id": location_dest_id.id,
                "picking_id": picking.id,
                "state": PENDING_MOVE_STATE,
                "restrict_partner_id": (
                    restrict_partner_id.id if restrict_partner_id else False
                ),
            }
        )

    @classmethod
    def _create_consigned_stock_data(cls):
        cls.company = cls.env.ref("base.main_company")
        cls.other_company = cls.env["res.company"].create(
            {"name": "Other Consigned Company"}
        )
        cls.owner_a = cls.env["res.partner"].create({"name": "Consigned Owner"})
        cls.owner_b = cls.env["res.partner"].create({"name": "Other Owner"})
        cls.owner = cls.owner_a
        cls.other_owner = cls.owner_b

        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")

        cls.product_a = cls._create_product("Consigned Alpha", "CONS-ALPHA")
        cls.product_b = cls._create_product("Consigned Beta", "CONS-BETA")
        cls.other_product = cls._create_product("Other Owner Product", "OTHER-001")

        # Product shared by two owners plus stock without owner, used to
        # verify that quantities are strictly isolated per owner.
        cls.product_shared = cls._create_product("Consigned Shared", "CONS-SHARED")

        # Product with only pending incoming moves for several owners
        # (no quant yet), used to verify isolation of incoming_qty.
        cls.product_incoming = cls._create_product(
            "Consigned Incoming", "CONS-INCOMING"
        )

        # Product with stock in two warehouses for the same owner, used
        # to verify that the warehouse filter changes the figures shown.
        cls.product_multi_wh = cls._create_product(
            "Consigned Multi Warehouse", "CONS-MULTIWH"
        )

        # Product without any quant, only a pending incoming move for the
        # owner: it must still be visible in the listing.
        cls.product_pending_only = cls._create_product(
            "Consigned Pending Only", "CONS-PENDING"
        )

        # Product with stock only without an owner: must never be
        # visible to any owner through the portal.
        cls.product_unowned_only = cls._create_product(
            "Consigned Unowned Only", "CONS-UNOWNED"
        )

        warehouses = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], order="id"
        )
        cls.warehouse = warehouses[:1]
        cls.other_warehouse = warehouses[1:2]
        if not cls.other_warehouse:
            cls.other_warehouse = cls.env["stock.warehouse"].create(
                {
                    "name": "Consigned Secondary Warehouse",
                    "code": "CSW",
                    "company_id": cls.company.id,
                }
            )
        cls.other_company_warehouse = cls.env["stock.warehouse"].create(
            {
                "name": "Other Company Warehouse",
                "code": "OCW",
                "company_id": cls.other_company.id,
            }
        )

        cls._create_quant(cls.product_a, cls.warehouse.lot_stock_id, cls.owner_a, 10)
        cls._create_quant(
            cls.product_b, cls.other_warehouse.lot_stock_id, cls.owner_a, 5
        )
        cls._create_quant(
            cls.other_product, cls.warehouse.lot_stock_id, cls.owner_b, 20
        )

        # Same product, three different owner contexts: owner_a, owner_b
        # and stock without any owner.
        cls._create_quant(
            cls.product_shared, cls.warehouse.lot_stock_id, cls.owner_a, 10
        )
        cls._create_quant(
            cls.product_shared, cls.warehouse.lot_stock_id, cls.owner_b, 100
        )
        cls._create_quant(cls.product_shared, cls.warehouse.lot_stock_id, None, 25)

        cls._create_quant(
            cls.product_unowned_only, cls.warehouse.lot_stock_id, None, 15
        )

        # Same product in both warehouses for owner_a, with different
        # quantities.
        cls._create_quant(
            cls.product_multi_wh, cls.warehouse.lot_stock_id, cls.owner_a, 7
        )
        cls._create_quant(
            cls.product_multi_wh, cls.other_warehouse.lot_stock_id, cls.owner_a, 3
        )

        # Stock belonging to owner_a in a different company: must never
        # be visible through the portal, regardless of the owner.
        cls._create_quant(
            cls.product_a,
            cls.other_company_warehouse.lot_stock_id,
            cls.owner_a,
            999,
            company=cls.other_company,
        )

        # Pending incoming moves for the same product, isolated by owner
        # (owner_a, owner_b) and without any owner.
        cls._create_pending_move(
            cls.product_incoming,
            cls.supplier_location,
            cls.warehouse.lot_stock_id,
            cls.warehouse.in_type_id,
            owner=cls.owner_a,
            qty=10,
        )
        cls._create_pending_move(
            cls.product_incoming,
            cls.supplier_location,
            cls.warehouse.lot_stock_id,
            cls.warehouse.in_type_id,
            owner=cls.owner_b,
            qty=100,
        )
        cls._create_pending_move(
            cls.product_incoming,
            cls.supplier_location,
            cls.warehouse.lot_stock_id,
            cls.warehouse.in_type_id,
            owner=None,
            qty=25,
        )

        # Pending incoming move for owner_a only, no quant created for
        # this product.
        cls._create_pending_move(
            cls.product_pending_only,
            cls.supplier_location,
            cls.warehouse.lot_stock_id,
            cls.warehouse.in_type_id,
            owner=cls.owner_a,
            qty=4,
        )

        portal_group = cls.env.ref("base.group_portal")
        cls.portal_user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Consigned Portal User",
                    "login": "consigned.portal@example.com",
                    "email": "consigned.portal@example.com",
                    "password": "consigned.portal",
                    "partner_id": cls.owner_a.id,
                    "groups_id": [Command.set([portal_group.id])],
                }
            )
        )
        cls.other_portal_user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Other Consigned Portal User",
                    "login": "other.consigned.portal@example.com",
                    "email": "other.consigned.portal@example.com",
                    "password": "other.consigned.portal",
                    "partner_id": cls.owner_b.id,
                    "groups_id": [Command.set([portal_group.id])],
                }
            )
        )


class ConsignedStockCommon(ConsignedStockDataMixin, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_consigned_stock_data()


class ConsignedStockHttpCommon(ConsignedStockDataMixin, HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_consigned_stock_data()
