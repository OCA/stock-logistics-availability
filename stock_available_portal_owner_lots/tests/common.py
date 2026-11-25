from datetime import timedelta

from odoo import fields

from odoo.addons.stock_available_portal_owner.tests.common import (
    ConsignedStockCommon,
    ConsignedStockHttpCommon,
)


class ConsignedStockLotsDataMixin:
    @classmethod
    def _create_lot(cls, name, product, company=None, expiration_date=None):
        return cls.env["stock.lot"].create(
            {
                "name": name,
                "product_id": product.id,
                "company_id": (company or cls.company).id,
                "expiration_date": expiration_date,
            }
        )

    @classmethod
    def _create_consigned_stock_lots_data(cls):
        cls.env.user.groups_id += cls.env.ref("stock.group_production_lot")

        now = fields.Datetime.now()

        cls.lot_a1 = cls._create_lot(
            "LOT-A1", cls.product_a, expiration_date=now - timedelta(days=5)
        )
        cls.lot_a2 = cls._create_lot(
            "LOT-A2", cls.product_a, expiration_date=now + timedelta(days=15)
        )
        cls.lot_b1 = cls._create_lot("LOT-B1", cls.product_b)

        cls.env["stock.quant"].sudo()._update_available_quantity(
            cls.product_a,
            cls.warehouse.lot_stock_id,
            5,
            lot_id=cls.lot_a1,
            owner_id=cls.owner_a,
        )
        cls.env["stock.quant"].sudo()._update_available_quantity(
            cls.product_a,
            cls.warehouse.lot_stock_id,
            5,
            lot_id=cls.lot_a2,
            owner_id=cls.owner_a,
        )
        cls.env["stock.quant"].sudo()._update_available_quantity(
            cls.product_b,
            cls.warehouse.lot_stock_id,
            10,
            lot_id=cls.lot_b1,
            owner_id=cls.owner_b,
        )


class ConsignedStockLotsCommon(ConsignedStockCommon, ConsignedStockLotsDataMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_consigned_stock_lots_data()


class ConsignedStockLotsHttpCommon(
    ConsignedStockHttpCommon, ConsignedStockLotsDataMixin
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_consigned_stock_lots_data()
