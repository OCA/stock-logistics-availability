from odoo import Command
from odoo.tests import HttpCase, TransactionCase


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
        company_id = company.id if company else cls.company.id
        cls.env["stock.quant"].sudo().with_company(
            company_id
        )._update_available_quantity(product, location, qty, owner_id=owner)
        return cls.env["stock.quant"].search(
            [
                ("product_id", "=", product.id),
                ("location_id", "=", location.id),
                ("owner_id", "=", owner.id if owner else False),
            ],
            limit=1,
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
        create_move_line=True,
    ):
        picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": location_id.id,
                "location_dest_id": location_dest_id.id,
                "owner_id": owner.id if owner else False,
            }
        )
        move = cls.env["stock.move"].create(
            {
                "name": product.name,
                "product_id": product.id,
                "product_uom_qty": qty,
                "product_uom": product.uom_id.id,
                "location_id": location_id.id,
                "location_dest_id": location_dest_id.id,
                "picking_id": picking.id,
                "restrict_partner_id": (
                    restrict_partner_id.id if restrict_partner_id else False
                ),
            }
        )
        move._action_confirm()

        if create_move_line:
            move.move_line_ids.unlink()
            cls.env["stock.move.line"].create(
                {
                    "product_id": product.id,
                    "product_uom_id": product.uom_id.id,
                    "quantity": qty,
                    "location_id": location_id.id,
                    "location_dest_id": location_dest_id.id,
                    "picking_id": picking.id,
                    "move_id": move.id,
                    "owner_id": owner.id if owner else False,
                    "company_id": cls.company.id,
                }
            )
        return move

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

        cls.product_shared = cls._create_product("Consigned Shared", "CONS-SHARED")
        cls.product_incoming = cls._create_product(
            "Consigned Incoming", "CONS-INCOMING"
        )
        cls.product_multi_wh = cls._create_product(
            "Consigned Multi Warehouse", "CONS-MULTIWH"
        )
        cls.product_pending_only = cls._create_product(
            "Consigned Pending Only", "CONS-PENDING"
        )
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

        cls._create_quant(
            cls.product_multi_wh, cls.warehouse.lot_stock_id, cls.owner_a, 7
        )
        cls._create_quant(
            cls.product_multi_wh, cls.other_warehouse.lot_stock_id, cls.owner_a, 3
        )

        cls._create_quant(
            cls.product_a,
            cls.other_company_warehouse.lot_stock_id,
            cls.owner_a,
            999,
            company=cls.other_company,
        )

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

        cls._create_pending_move(
            cls.product_pending_only,
            cls.supplier_location,
            cls.warehouse.lot_stock_id,
            cls.warehouse.in_type_id,
            owner=cls.owner_a,
            qty=4,
            create_move_line=False,
        )

        cls._create_pending_move(
            cls.product_a,
            cls.warehouse.lot_stock_id,
            cls.customer_location,
            cls.warehouse.out_type_id,
            owner=cls.owner_a,
            restrict_partner_id=cls.owner_a,
            qty=2,
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
