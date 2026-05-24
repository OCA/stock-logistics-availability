# Copyright 2026 FactorLibre - Álvaro Gómez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.depends(
        "bom_ids",
        "bom_ids.product_qty",
        "bom_ids.bom_line_ids",
        "bom_ids.bom_line_ids.product_id",
        "bom_ids.bom_line_ids.product_qty",
        "bom_ids.bom_line_ids.product_uom_id",
        "variant_bom_ids",
        "variant_bom_ids.product_qty",
        "variant_bom_ids.bom_line_ids",
        "variant_bom_ids.bom_line_ids.product_id",
        "variant_bom_ids.bom_line_ids.product_qty",
        "variant_bom_ids.bom_line_ids.product_uom_id",
    )
    def _compute_available_quantities(self):
        return super()._compute_available_quantities()

    def _compute_available_quantities_dict(self):
        res, stock_dict = super()._compute_available_quantities_dict()
        # Recompute ``immediately_usable_qty`` for kits from components: see
        # module description for the algebraic justification.
        self._stock_available_immediately_mrp_recompute_kits(res)
        return res, stock_dict

    def _stock_available_immediately_mrp_recompute_kits(self, res):
        """Recompute ``immediately_usable_qty`` for products with a phantom BoM
        from their components.

        The recomputation only applies to products having a ``phantom`` BoM.
        The other kit fields (qty_available, virtual_available, incoming_qty,
        outgoing_qty, free_qty) are intentionally left untouched: they keep
        the standard Odoo MRP aggregation as ``min(component / need)`` per
        field.

        The component's ``immediately_usable_qty`` is read from ``res`` when
        the component already belongs to the current batch (``self``). Reading
        the attribute directly would re-trigger the compute under any context
        that overlays may have set during this call (notably modules that wrap
        ``_compute_available_quantities_dict`` to switch the location/batch
        context such as ``omnichannel_location_batch``), which can lead to a
        mismatched value compared to what ``super()`` already computed for the
        component in the same call. The ``res`` lookup keeps both kit and
        components consistent with the same context.
        """
        bom_kits = self.env["mrp.bom"]._bom_find(self, bom_type="phantom")
        for product, bom in bom_kits.items():
            __, bom_sub_lines = bom.explode(product, 1)
            ratios = []
            for bom_line, line_data in bom_sub_lines:
                component = bom_line.product_id
                if component.type != "product":
                    continue
                # If BoM line and component live in different UoM categories
                # ``_compute_quantity(raise_if_failure=False)`` returns the
                # original quantity unchanged, which would silently produce
                # an inconsistent ratio. Skip the component with a warning so
                # the misconfiguration is detectable in production logs.
                if bom_line.product_uom_id.category_id != component.uom_id.category_id:
                    _logger.warning(
                        "Cannot compute immediately_usable_qty for kit %s: "
                        "component %s skipped (incompatible UoM categories "
                        "between %s and %s)",
                        product.display_name,
                        component.display_name,
                        bom_line.product_uom_id.name,
                        component.uom_id.name,
                    )
                    continue
                qty_per_kit = line_data["qty"] / line_data["original_qty"]
                qty_per_kit = bom_line.product_uom_id._compute_quantity(
                    qty_per_kit,
                    component.uom_id,
                    round=False,
                    raise_if_failure=False,
                )
                if not qty_per_kit:
                    # The BoM line declares a zero quantity for the component.
                    # Skip it so the kit is constrained only by the remaining
                    # components.
                    _logger.warning(
                        "Cannot compute immediately_usable_qty for kit %s: "
                        "component %s skipped (BoM line declares zero "
                        "quantity)",
                        product.display_name,
                        component.display_name,
                    )
                    continue
                if component.id in res:
                    comp_immediately = res[component.id]["immediately_usable_qty"]
                else:
                    comp_immediately = component.immediately_usable_qty
                ratios.append(comp_immediately / qty_per_kit)
            if ratios:
                # Floor to integer with ``// 1`` to mirror the rounding that
                # Odoo MRP core already applies to the other aggregated kit
                # fields (``qty_available``, ``virtual_available``,
                # ``incoming_qty``, ``outgoing_qty``, ``free_qty``) in
                # ``addons/mrp/models/product.py``. Using the kit UoM
                # ``rounding`` here would diverge from those siblings whenever
                # the UoM allows fractions (e.g. the default ``Units``
                # rounding of 0.01), surfacing decimals in this field while
                # the others stay integer. The integer floor keeps every kit
                # quantity field internally consistent.
                res[product.id]["immediately_usable_qty"] = (
                    min(ratios) * bom.product_qty // 1
                )
