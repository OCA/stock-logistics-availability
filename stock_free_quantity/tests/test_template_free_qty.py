# Copyright 2021 Akretion France (https://www.akretion.com)

from odoo.addons.base.tests.common import BaseCommon


class TestTemplateFreeQty(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.warehouse = cls.env["stock.warehouse"].search([], limit=1)
        cls.location_stock = cls.warehouse.lot_stock_id

        cls.product_attribute = cls.env["product.attribute"].create(
            {
                "name": "Test Attribute",
                "value_ids": [
                    (0, 0, {"name": "Value 1"}),
                    (0, 0, {"name": "Value 2"}),
                ],
            }
        )

        cls.template_with_variant = cls.env["product.template"].create(
            {
                "name": "Test Product With Variants",
                "type": "consu",
                "is_storable": True,
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.product_attribute.id,
                            "value_ids": [(6, 0, cls.product_attribute.value_ids.ids)],
                        },
                    )
                ],
            }
        )

        cls.template_with_no_variant = cls.env["product.template"].create(
            {
                "name": "Test Product No Variants",
                "type": "consu",
                "is_storable": True,
            }
        )

        cls.template_with_no_free_qty = cls.env["product.template"].create(
            {
                "name": "Test Product No Stock",
                "type": "consu",
                "is_storable": True,
            }
        )

        cls._set_product_qty(cls.template_with_variant.product_variant_ids[0], 26.0)
        cls._set_product_qty(cls.template_with_variant.product_variant_ids[1], 30.0)
        cls._set_product_qty(cls.template_with_no_variant.product_variant_ids, 15.0)

    @classmethod
    def _set_product_qty(cls, product, qty):
        cls.env["stock.quant"]._update_available_quantity(
            product, cls.location_stock, qty
        )

    def test_template_free_qty(self):
        self.assertEqual(self.template_with_variant.free_qty, 56)
        self.assertEqual(
            self.template_with_no_variant.free_qty,
            self.template_with_no_variant.product_variant_ids.free_qty,
        )

    def test_search_template_free_qty(self):
        template_with_free_qty_ids = (
            self.env["product.template"].search([("free_qty", ">", 0)]).ids
        )
        self.assertIn(self.template_with_variant.id, template_with_free_qty_ids)
        self.assertIn(self.template_with_no_variant.id, template_with_free_qty_ids)
        self.assertNotIn(self.template_with_no_free_qty.id, template_with_free_qty_ids)
