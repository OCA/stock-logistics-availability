The implementation of this module relies on the capacity of native odoo to calculate quantities based on a warehouse or a location passed in the context in `_get_domain_locations <https://github.com/odoo/odoo/blob/055184ea033e7068ce33c92390c73ae39b2db259/addons/stock/models/product.py#L271>`_.

But it needs a patch on odoo upstream to generalize `_compute_qty_at_date`, see `here <https://github.com/odoo/odoo/pull/174143>`_.
