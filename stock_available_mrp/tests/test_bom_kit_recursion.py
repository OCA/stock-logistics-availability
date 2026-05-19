# Copyright 2026 FactorLibre
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import math

from odoo.tests.common import TransactionCase


class TestBomKitRecursion(TransactionCase):
    """Regression and non-regression tests for explode_bom_quantities.

    The original implementation walked the BoM tree via
    ``first(product.bom_ids)`` on every component. ``bom_ids`` is
    template-wide through ``_inherits``, so for a variant it returns every
    BoM of the template - including BoMs that belong to sibling variants.
    When a phantom BoM used another variant of its own template as a
    component, the lookup re-surfaced that BoM forever and the loop
    accumulated quantity until it overflowed to ``inf`` and produced
    ``NaN``, raising ``ValueError`` from ``math.ceil``.

    The fix replaces the raw lookups with
    ``mrp.bom._bom_find(..., bom_type="phantom")`` which honours the
    variant scope. These tests cover:

    * the regression itself (sibling-variant phantom kit),
    * a multi-variant scenario closer to real-world catalogues with a
      'unit' variant and two pack variants kitting it,
    * and a happy-path where the component lives in a different template
      so we ensure the canonical case keeps working untouched.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Bom = cls.env["mrp.bom"]
        cls.BomLine = cls.env["mrp.bom.line"]

    def _make_template_with_variants(self, name, attribute_name, value_names):
        """Helper: create a product.template with one attribute and N variants."""
        attribute = self.env["product.attribute"].create(
            {"name": attribute_name, "create_variant": "always"}
        )
        values = self.env["product.attribute.value"].create(
            [{"name": vname, "attribute_id": attribute.id} for vname in value_names]
        )
        template = self.env["product.template"].create(
            {
                "name": name,
                "type": "product",
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": attribute.id,
                            "value_ids": [(6, 0, values.ids)],
                        },
                    )
                ],
            }
        )
        return template, values

    def _get_variant(self, template, attr_value):
        return template.product_variant_ids.filtered(
            lambda v: attr_value
            in v.product_template_attribute_value_ids.product_attribute_value_id
        )

    # ------------------------------------------------------------------
    # Regression: sibling-variant phantom kit (the original Natuka bug)
    # ------------------------------------------------------------------
    def test_explode_bom_quantities_does_not_recurse_on_sibling_variant(self):
        template, values = self._make_template_with_variants(
            "Cycle Repro Product", "Test Cycle Format", ["Individual", "Pack 12"]
        )
        unit = self._get_variant(template, values[0])
        pack = self._get_variant(template, values[1])
        kit_bom = self.Bom.create(
            {
                "product_tmpl_id": template.id,
                "product_id": pack.id,
                "type": "phantom",
                "product_qty": 1.0,
            }
        )
        self.BomLine.create(
            {"bom_id": kit_bom.id, "product_id": unit.id, "product_qty": 12.0}
        )
        # Precondition documenting the trap: the unit variant inherits the
        # template's BoMs via _inherits and therefore appears to "own" the
        # kit BoM as well. Kept here as executable documentation of why
        # the previous implementation looped.
        self.assertIn(kit_bom, unit.bom_ids)
        # Before the fix this raised ValueError when the loop produced NaN.
        result = pack.explode_bom_quantities()
        self.assertIn(pack.id, result)
        # Exactly one exploded line: unit x 12. Anything else would mean
        # we still walked into a sibling BoM.
        exploded = result[pack.id]
        self.assertEqual(len(exploded), 1)
        line, qty = exploded[0]
        self.assertEqual(line.product_id, unit)
        self.assertEqual(qty, 12.0)

    def test_immediately_usable_qty_does_not_recurse_on_sibling_variant(self):
        template, values = self._make_template_with_variants(
            "Cycle Repro Product UQ", "Test Cycle Format UQ", ["Individual", "Pack 12"]
        )
        unit = self._get_variant(template, values[0])
        pack = self._get_variant(template, values[1])
        kit_bom = self.Bom.create(
            {
                "product_tmpl_id": template.id,
                "product_id": pack.id,
                "type": "phantom",
                "product_qty": 1.0,
            }
        )
        self.BomLine.create(
            {"bom_id": kit_bom.id, "product_id": unit.id, "product_qty": 12.0}
        )
        # Real frontend path. Before the fix, reading this field raised
        # ValueError because the underlying _compute_available_quantities_dict
        # invoked the broken recursion.
        pack.invalidate_recordset(["immediately_usable_qty"])
        value = pack.immediately_usable_qty
        self.assertIsInstance(value, float)
        self.assertFalse(math.isnan(value), "immediately_usable_qty must not be NaN")

    def test_unit_variant_is_not_treated_as_a_kit(self):
        template, values = self._make_template_with_variants(
            "Cycle Repro Product Unit",
            "Test Cycle Format Unit",
            ["Individual", "Pack 12"],
        )
        unit = self._get_variant(template, values[0])
        pack = self._get_variant(template, values[1])
        kit_bom = self.Bom.create(
            {
                "product_tmpl_id": template.id,
                "product_id": pack.id,
                "type": "phantom",
                "product_qty": 1.0,
            }
        )
        self.BomLine.create(
            {"bom_id": kit_bom.id, "product_id": unit.id, "product_qty": 12.0}
        )
        # The unit variant has no variant_bom_ids of its own; the kit BoM
        # belongs to the pack sibling. Exploding the unit must terminate
        # and return an empty result, not enter recursion.
        self.assertFalse(unit.variant_bom_ids)
        result = unit.explode_bom_quantities()
        self.assertEqual(result.get(unit.id, []), [])

    # ------------------------------------------------------------------
    # Multi-variant scenario (closer to the real Natuka catalogue)
    # ------------------------------------------------------------------
    def test_three_variants_two_packs_kit_their_unit_sibling(self):
        template, values = self._make_template_with_variants(
            "Three Variants Product",
            "Test Three Format",
            ["Individual", "Pack 6", "Pack 12"],
        )
        unit = self._get_variant(template, values[0])
        pack_6 = self._get_variant(template, values[1])
        pack_12 = self._get_variant(template, values[2])
        bom_6 = self.Bom.create(
            {
                "product_tmpl_id": template.id,
                "product_id": pack_6.id,
                "type": "phantom",
                "product_qty": 1.0,
            }
        )
        self.BomLine.create(
            {"bom_id": bom_6.id, "product_id": unit.id, "product_qty": 6.0}
        )
        bom_12 = self.Bom.create(
            {
                "product_tmpl_id": template.id,
                "product_id": pack_12.id,
                "type": "phantom",
                "product_qty": 1.0,
            }
        )
        self.BomLine.create(
            {"bom_id": bom_12.id, "product_id": unit.id, "product_qty": 12.0}
        )
        # Both kit variants must explode to exactly their own unit-line,
        # never to the sibling's kit BoM.
        result_6 = pack_6.explode_bom_quantities()
        self.assertEqual(len(result_6[pack_6.id]), 1)
        line_6, qty_6 = result_6[pack_6.id][0]
        self.assertEqual(line_6.product_id, unit)
        self.assertEqual(qty_6, 6.0)
        result_12 = pack_12.explode_bom_quantities()
        self.assertEqual(len(result_12[pack_12.id]), 1)
        line_12, qty_12 = result_12[pack_12.id][0]
        self.assertEqual(line_12.product_id, unit)
        self.assertEqual(qty_12, 12.0)
        # And the unit variant remains a leaf.
        self.assertEqual(unit.explode_bom_quantities().get(unit.id, []), [])

    # ------------------------------------------------------------------
    # Happy-path non-regression: component lives in another template
    # ------------------------------------------------------------------
    def test_kit_with_component_in_different_template(self):
        # Component template (unrelated to the kit template).
        component = self.env["product.product"].create(
            {"name": "Standalone Component", "type": "product"}
        )
        # Kit template with a single variant.
        kit_tmpl = self.env["product.template"].create(
            {"name": "Standalone Kit", "type": "product"}
        )
        kit_variant = kit_tmpl.product_variant_ids
        kit_bom = self.Bom.create(
            {
                "product_tmpl_id": kit_tmpl.id,
                "product_id": kit_variant.id,
                "type": "phantom",
                "product_qty": 1.0,
            }
        )
        self.BomLine.create(
            {"bom_id": kit_bom.id, "product_id": component.id, "product_qty": 4.0}
        )
        # The canonical case must keep working: terminate with exactly
        # one line referencing the standalone component.
        result = kit_variant.explode_bom_quantities()
        exploded = result[kit_variant.id]
        self.assertEqual(len(exploded), 1)
        line, qty = exploded[0]
        self.assertEqual(line.product_id, component)
        self.assertEqual(qty, 4.0)
