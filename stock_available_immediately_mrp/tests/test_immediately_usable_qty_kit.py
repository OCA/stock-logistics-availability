# Copyright 2026 FactorLibre - Álvaro Gómez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestImmediatelyUsableQtyKit(TransactionCase):
    """Validate that ``immediately_usable_qty`` for kit products (BoM phantom)
    is recomputed component-by-component, avoiding the mismatch produced by
    aggregating each kit field independently with ``min``.

    The assertions use ``immediately_usable_qty`` directly because this glue
    module is the one producing the value. If ``stock_available_mrp`` is
    additionally installed and the production potential is enabled, that
    module replaces ``immediately_usable_qty`` with ``potential_qty`` and the
    value asserted here is overridden — this test class assumes the production
    potential is disabled (the default state without ``stock_available_mrp``).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.move_obj = cls.env["stock.move"]
        # If ``stock_available_mrp`` happens to be installed in the same DB,
        # disable the production potential so this glue's per-component
        # recomputation surfaces (otherwise ``stock_available_mrp`` would
        # replace ``immediately_usable_qty`` with ``potential_qty``).
        cls.env["ir.config_parameter"].sudo().set_param(
            "stock_available_potential_based", "False"
        )

    # -- helpers ------------------------------------------------------------

    def _create_storable(self, name):
        return self.env["product.product"].create(
            {"name": name, "type": "product", "uom_id": self.uom_unit.id}
        )

    def _create_kit(self, name, components, bom_type="phantom", bom_qty=1.0):
        """Create a product with a BoM of the given type.

        :param components: list of (product, qty_per_kit)
        :param bom_type: ``phantom`` (kit), ``normal`` (manufacture) or
            ``subcontract``.
        :param bom_qty: ``mrp.bom.product_qty`` (number of finished products
            produced by one BoM execution).
        """
        product = self.env["product.product"].create(
            {"name": name, "type": "product", "uom_id": self.uom_unit.id}
        )
        bom_lines = [
            (0, 0, {"product_id": p.id, "product_qty": qty}) for p, qty in components
        ]
        self.env["mrp.bom"].create(
            {
                "product_tmpl_id": product.product_tmpl_id.id,
                "product_id": product.id,
                "type": bom_type,
                "product_qty": bom_qty,
                "product_uom_id": self.uom_unit.id,
                "bom_line_ids": bom_lines,
            }
        )
        return product

    def _set_quant(self, product, qty):
        self.env["stock.quant"]._update_available_quantity(
            product, self.stock_location, qty
        )

    def _create_outgoing(self, product, qty):
        move = self.move_obj.create(
            {
                "name": "OUT",
                "product_id": product.id,
                "product_uom": product.uom_id.id,
                "product_uom_qty": qty,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )
        move._action_confirm()
        return move

    def _create_incoming(self, product, qty):
        move = self.move_obj.create(
            {
                "name": "IN",
                "product_id": product.id,
                "product_uom": product.uom_id.id,
                "product_uom_qty": qty,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
            }
        )
        move._action_confirm()
        return move

    def _refresh(self, *records):
        for rec in records:
            rec.invalidate_model()

    @staticmethod
    def _net_immediately(product):
        """Return ``immediately_usable_qty - potential_qty``.

        For products with a non-phantom BoM (Manufacture/Subcontract), the
        optional ``stock_available_mrp`` module adds ``potential_qty`` to
        ``immediately_usable_qty``. That addition is independent of this
        module's recomputation (which only targets phantom BoMs). The helper
        factors the ``potential_qty`` contribution out so the assertions hold
        regardless of whether ``stock_available_mrp`` is installed.

        For phantom BoMs (kits) this module's assignment supersedes the
        addition; for plain products without a BoM, ``potential_qty`` is 0
        and the helper is a no-op.
        """
        return product.immediately_usable_qty - product.potential_qty

    # -- tests --------------------------------------------------------------

    def test_kit_unbalanced_components_fixes_bug(self):
        """Components limit different kit fields, so the buggy formula
        (``min(virtual)`` minus ``min(incoming)``) was algebraically wrong.

        Without the fix:
            Forecast_kit  = min(127/2, 4150/2) = 63   (limited by A)
            Incoming_kit  = min(133/2, 60/2)   = 30   (limited by B)
            DispProm_kit (bug) = 63 - 30 = 33

        With the fix:
            DispProm_A    = 8  - 14  = -6
            DispProm_B    = 4258 - 168 = 4090
            DispProm_kit  = min(-6/2, 4090/2) = -3
        """
        comp_a = self._create_storable("CompA")
        comp_b = self._create_storable("CompB")
        kit = self._create_kit("Kit Unbalanced", [(comp_a, 2), (comp_b, 2)])
        self._set_quant(comp_a, 8)
        self._set_quant(comp_b, 4258)
        self._create_incoming(comp_a, 133)
        self._create_outgoing(comp_a, 14)
        self._create_incoming(comp_b, 60)
        self._create_outgoing(comp_b, 168)
        self._refresh(comp_a, comp_b, kit)
        # Components: cancellation works, immediately_usable_qty = qty - out
        self.assertEqual(comp_a.immediately_usable_qty, -6)
        self.assertEqual(comp_b.immediately_usable_qty, 4090)
        # Kit: fixed value via min(component / need), can be negative
        self.assertEqual(kit.immediately_usable_qty, -3)

    def test_kit_balanced_components_unchanged(self):
        """Components limit the same kit fields → the buggy formula
        coincidentally produced the correct value. The fix must not change it.
        """
        comp_a = self._create_storable("CompA")
        comp_b = self._create_storable("CompB")
        kit = self._create_kit("Kit Balanced", [(comp_a, 2), (comp_b, 2)])
        self._set_quant(comp_a, 42)
        self._set_quant(comp_b, 7522)
        self._create_incoming(comp_b, 4)
        self._create_outgoing(comp_a, 5)
        self._create_outgoing(comp_b, 66)
        self._refresh(comp_a, comp_b, kit)
        self.assertEqual(comp_a.immediately_usable_qty, 37)
        self.assertEqual(comp_b.immediately_usable_qty, 7456)
        # min((37/2), (7456/2)) = min(18.5, 3728) = 18.5
        # Floored to integer (consistent with Odoo MRP aggregations) → 18.
        self.assertEqual(kit.immediately_usable_qty, 18)

    def test_kit_oversold_component_negative(self):
        """Deeply oversold component drives the kit to a strongly negative
        value, reflecting the real backlog.
        """
        comp_a = self._create_storable("CompA")
        comp_oversold = self._create_storable("CompOversold")
        comp_b = self._create_storable("CompB")
        kit = self._create_kit(
            "Kit Three",
            [(comp_a, 1), (comp_oversold, 1), (comp_b, 1)],
        )
        self._set_quant(comp_a, 20)
        self._set_quant(comp_oversold, 5)
        self._set_quant(comp_b, 10422)
        self._create_incoming(comp_a, 200)
        self._create_outgoing(comp_a, 200)
        self._create_incoming(comp_oversold, 100)
        self._create_outgoing(comp_oversold, 300)
        self._create_incoming(comp_b, 200)
        self._create_outgoing(comp_b, 27)
        self._refresh(comp_a, comp_oversold, comp_b, kit)
        # comp_oversold is the most oversold: -295 limits the kit
        self.assertEqual(comp_oversold.immediately_usable_qty, -295)
        self.assertEqual(kit.immediately_usable_qty, -295)

    def test_kit_no_oversold_positive(self):
        """All components healthy, kit reports the most limiting
        component / need ratio.
        """
        a = self._create_storable("A")
        b = self._create_storable("B")
        kit = self._create_kit("Kit Healthy", [(a, 1), (b, 2)])
        self._set_quant(a, 50)
        self._set_quant(b, 100)
        self._refresh(a, b, kit)
        # min(50/1, 100/2) = min(50, 50) = 50
        self.assertEqual(kit.immediately_usable_qty, 50)

    def test_non_kit_unaffected(self):
        """Plain product without BoM keeps the standard cancellation:
        immediately_usable_qty = qty_available - outgoing_qty.
        """
        product = self._create_storable("Plain")
        self._set_quant(product, 30)
        self._create_outgoing(product, 5)
        self._create_incoming(product, 10)
        self._refresh(product)
        # virtual = 30 + 10 - 5 = 35; immediately = 35 - 10 = 25
        self.assertEqual(product.immediately_usable_qty, 25)

    def test_manufacturing_bom_unaffected(self):
        """Products with a non-phantom BoM (Manufacture) must not be affected
        by the kit override: the BoM filter ``bom_type='phantom'`` excludes
        them. The product keeps the standard ``qty_available - outgoing_qty``
        cancellation that applies to plain products.

        The assertion uses ``_net_immediately`` so it is robust to the
        optional ``stock_available_mrp`` adding ``potential_qty`` on top for
        non-phantom BoMs (an unrelated contract that must not interfere with
        the assertion about *this* module's behaviour).
        """
        comp_a = self._create_storable("MfgComp A")
        comp_b = self._create_storable("MfgComp B")
        manuf = self._create_kit(
            "Manufactured Product",
            [(comp_a, 1), (comp_b, 2)],
            bom_type="normal",
        )
        # Stock the manufactured product itself, not the components, to make
        # the regression visible: with the override active a kit would be
        # rewritten from components, but a Manufacture BoM must be ignored
        # and the product's own stock kept.
        self._set_quant(manuf, 12)
        self._create_outgoing(manuf, 3)
        self._set_quant(comp_a, 100)
        self._set_quant(comp_b, 100)
        self._refresh(comp_a, comp_b, manuf)
        # Plain product cancellation: 12 - 3 = 9.
        self.assertEqual(self._net_immediately(manuf), 9)

    def test_kit_with_consumable_component_skipped(self):
        """Consumable components (type != 'product') do not contribute to the
        ratio min, since their stock is not tracked. The kit takes the min
        among storable components only.
        """
        storable = self._create_storable("S")
        consumable = self.env["product.product"].create(
            {"name": "Cons", "type": "consu", "uom_id": self.uom_unit.id}
        )
        kit = self._create_kit("Kit With Consu", [(storable, 1), (consumable, 1)])
        self._set_quant(storable, 7)
        self._refresh(storable, kit)
        # Consumable ignored → only storable limits → 7/1 = 7
        self.assertEqual(kit.immediately_usable_qty, 7)

    def test_kit_batch_read_uses_res_for_components(self):
        """When the kit and its components are read together (multi-record
        batch, the case of stock report views), the recomputation must read
        the component value from ``res`` instead of re-triggering the compute
        as an attribute access.

        Regression of the bug where, in batch reads under contexts wrapped by
        modules such as ``omnichannel_location_batch``, the kit was returning
        ``immediately_usable_qty=0`` because the recursive attribute access
        resolved under a different context than the one used by ``super()``
        for the batch.
        """
        comp_a = self._create_storable("BatchComp A")
        comp_b = self._create_storable("BatchComp B")
        kit = self._create_kit("Kit Batch Read", [(comp_a, 1), (comp_b, 2)])
        self._set_quant(comp_a, 30)
        self._set_quant(comp_b, 80)
        self._create_outgoing(comp_a, 4)
        self._create_outgoing(comp_b, 10)
        self._refresh(comp_a, comp_b, kit)

        products = kit | comp_a | comp_b
        products.invalidate_recordset()
        result = {r["id"]: r for r in products.read(["immediately_usable_qty"])}
        self.assertEqual(result[comp_a.id]["immediately_usable_qty"], 26)  # 30 - 4
        self.assertEqual(result[comp_b.id]["immediately_usable_qty"], 70)  # 80 - 10
        # min(26 / 1, 70 / 2) = min(26, 35) = 26
        self.assertEqual(result[kit.id]["immediately_usable_qty"], 26)

    def test_kit_bom_product_qty_greater_than_one(self):
        """Validate the formula when ``bom.product_qty != 1``: each BoM
        execution produces N finished kits, so the kit-level result must be
        scaled by ``bom.product_qty``.

        With ``bom_qty=2`` and components for 50 BoM batches, the kit can be
        delivered for 100 units (50 batches × 2 kits per batch).
        """
        comp_a = self._create_storable("BomQtyComp A")
        comp_b = self._create_storable("BomQtyComp B")
        kit = self._create_kit("Kit BoM Qty 2", [(comp_a, 1), (comp_b, 1)], bom_qty=2.0)
        self._set_quant(comp_a, 50)
        self._set_quant(comp_b, 200)
        self._refresh(comp_a, comp_b, kit)
        # min(50/1, 200/1) = 50 batches → 50 * 2 = 100 finished kits.
        self.assertEqual(kit.immediately_usable_qty, 100)

    def test_kit_floored_to_integer_independent_of_uom_rounding(self):
        """The kit ``immediately_usable_qty`` is floored to an integer
        regardless of the kit UoM rounding, mirroring the integer floor that
        Odoo MRP core applies to the other aggregated kit fields
        (``qty_available``, ``virtual_available``, ...). This keeps every kit
        quantity field internally consistent: if the user sees integers in
        the standard fields, they should see integers here too.
        """
        # Force a finer UoM rounding (the default ``Units`` rounding is 0.01,
        # but be explicit) — the result must still be integer.
        original_rounding = self.uom_unit.rounding
        self.uom_unit.rounding = 0.01
        try:
            comp_a = self._create_storable("RoundComp A")
            comp_b = self._create_storable("RoundComp B")
            kit = self._create_kit("Kit Round", [(comp_a, 2), (comp_b, 2)])
            self._set_quant(comp_a, 37)  # 37/2 = 18.5
            self._set_quant(comp_b, 1000)
            self._refresh(comp_a, comp_b, kit)
            # min((37/2), (1000/2)) = min(18.5, 500) = 18.5
            # Floored to integer (independent of UoM rounding) → 18.
            self.assertEqual(kit.immediately_usable_qty, 18)
        finally:
            self.uom_unit.rounding = original_rounding

    def test_kit_zero_bom_line_qty_skips_component(self):
        """A BoM line with a quantity of zero produces ``qty_per_kit=0``. The
        component is skipped with a warning and the kit is only constrained
        by the remaining components.
        """
        comp_a = self._create_storable("ZeroComp A")
        comp_b = self._create_storable("ZeroComp B")
        kit = self._create_kit("Kit Zero Need", [(comp_a, 1), (comp_b, 0)])
        self._set_quant(comp_a, 9)
        self._set_quant(comp_b, 100)
        self._refresh(comp_a, comp_b, kit)
        # comp_b is skipped because the BoM line declares zero quantity.
        # Only comp_a constrains the kit: 9 / 1 = 9.
        self.assertEqual(kit.immediately_usable_qty, 9)

    def test_kit_uom_category_mismatch_skips_component(self):
        """When the BoM line UoM and the component UoM belong to different
        UoM categories (``_compute_quantity`` cannot convert between them),
        the component is skipped with a warning.

        Without the explicit category check ``_compute_quantity`` would return
        the original value unchanged, leading to an inconsistent ratio.
        """
        comp_storable = self._create_storable("UomCategoryStorable")
        comp_kg = self._create_storable("UomCategoryKg")
        uom_kg = self.env.ref("uom.product_uom_kgm")
        comp_kg.write({"uom_id": uom_kg.id, "uom_po_id": uom_kg.id})
        kit = self.env["product.product"].create(
            {
                "name": "Kit UoM mismatch",
                "type": "product",
                "uom_id": self.uom_unit.id,
            }
        )
        # Force the BoM line for comp_kg to use a UoM in a category other
        # than its component (Units instead of Weight).
        self.env["mrp.bom"].create(
            {
                "product_tmpl_id": kit.product_tmpl_id.id,
                "product_id": kit.id,
                "type": "phantom",
                "product_qty": 1.0,
                "product_uom_id": self.uom_unit.id,
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": comp_storable.id,
                            "product_qty": 1,
                            "product_uom_id": self.uom_unit.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": comp_kg.id,
                            "product_qty": 1,
                            "product_uom_id": self.uom_unit.id,
                        },
                    ),
                ],
            }
        )
        self._set_quant(comp_storable, 5)
        self._set_quant(comp_kg, 100)
        self._refresh(comp_storable, comp_kg, kit)
        # comp_kg is skipped (different UoM category). Only comp_storable
        # constrains the kit: 5 / 1 = 5.
        self.assertEqual(kit.immediately_usable_qty, 5)
