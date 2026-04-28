Glue module that fixes ``immediately_usable_qty`` on products with a phantom
BoM (kits) when both ``stock_available_immediately`` and ``mrp`` are
installed. Auto-installs whenever both parents are present.

For products with a phantom BoM (kits), ``stock_available_immediately``
applies the formula
``immediately_usable_qty = virtual_available - incoming_qty`` to the
aggregated kit fields. Each aggregated kit field (``virtual_available``,
``incoming_qty``, ...) is computed by Odoo MRP as an independent ``min``
over the components and may be limited by different components. Subtracting
two such mins is not equivalent to ``qty_available - outgoing_qty`` for
kits, even though that algebraic cancellation does hold for plain products.

Example
-------

Kit with two components, ``need=2`` each:

  Component A: qty=8,    in=133, out=14   →  virtual=127,  immediately=-6
  Component B: qty=4258, in=60,  out=168  →  virtual=4150, immediately=4090

  Forecasted (kit) = min(127/2, 4150/2)   = 63    ← limited by A
  Incoming   (kit) = min(133/2, 60/2)     = 30    ← limited by B
  immediately_usable_qty (current bug) = 63 - 30  = 33    ← inflated
  immediately_usable_qty (expected)    = min(-6/2, 4090/2) = -3

This module recomputes ``immediately_usable_qty`` for products with a
phantom BoM directly from the components and aggregates the result with
``min(component / qty_per_kit) * bom.product_qty``, rounded DOWN to the kit
UoM rounding (consistently with ``stock_available_mrp.potential_qty``).

The other kit fields (``qty_available``, ``virtual_available``,
``incoming_qty``, ``outgoing_qty``, ``free_qty``) are intentionally left
untouched and keep the standard Odoo MRP aggregation as
``min(component / need)`` per field.

Interaction with stock_available_mrp
------------------------------------

This module is independent of ``stock_available_mrp`` and does not depend
on it. They compose cleanly when both are installed:

* This module fixes the ``immediately_usable_qty`` base value for kits.
* ``stock_available_mrp`` then increments it with ``potential_qty`` (the
  quantity that can be manufactured from currently-available components).

The end result for kits with both modules installed is therefore
``correct_kit_immediately + potential_qty`` instead of the previous
``buggy_kit_immediately + potential_qty``.
