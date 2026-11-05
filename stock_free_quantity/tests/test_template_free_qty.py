# Copyright 2021 Akretion France (https://www.akretion.com)

from odoo.fields import Command

from odoo.addons.base.tests.common import BaseCommon


class TestTemplateFreeQty(BaseCommon):
    _test_user_groups = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.location_stock = (
            cls.env["stock.warehouse"]
            .search([("company_id", "=", cls.env.company.id)], limit=1)
            .lot_stock_id
        )
        attribute = cls.env["product.attribute"].create(
            {
                "name": "Test Attribute",
                "value_ids": [
                    Command.create({"name": "Value 1"}),
                    Command.create({"name": "Value 2"}),
                ],
            }
        )
        Template = cls.env["product.template"]
        product_vals = {"type": "consu", "is_storable": True}
        cls.template_with_variant = Template.create(
            {
                **product_vals,
                "name": "Product With Variants",
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": attribute.id,
                            "value_ids": [Command.set(attribute.value_ids.ids)],
                        }
                    )
                ],
            }
        )
        cls.template_with_no_variant = Template.create(
            {**product_vals, "name": "Product Without Variants"}
        )
        cls.template_with_no_free_qty = Template.create(
            {**product_vals, "name": "Product Without Stock"}
        )
        variant_1, variant_2 = cls.template_with_variant.product_variant_ids
        Quant = cls.env["stock.quant"]
        Quant._update_available_quantity(variant_1, cls.location_stock, 26.0)
        Quant._update_available_quantity(variant_2, cls.location_stock, 30.0)
        Quant._update_available_quantity(
            cls.template_with_no_variant.product_variant_id, cls.location_stock, 15.0
        )

    def test_template_free_qty(self):
        templates = self.template_with_variant | self.template_with_no_variant
        self.assertEqual(templates.mapped("free_qty"), [56.0, 15.0])

    def test_search_template_free_qty(self):
        all_templates = (
            self.template_with_variant
            | self.template_with_no_variant
            | self.template_with_no_free_qty
        )
        for operator, value, expected in (
            (">", 0, self.template_with_variant | self.template_with_no_variant),
            ("=", 0, self.template_with_no_free_qty),
        ):
            with self.subTest(operator=operator, value=value):
                found = self.env["product.template"].search(
                    [("id", "in", all_templates.ids), ("free_qty", operator, value)]
                )
                self.assertEqual(found, expected)
