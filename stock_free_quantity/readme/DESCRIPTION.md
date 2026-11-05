Add Product variant free quantity in Product form view and add the same
on Product templates.

In Odoo 20.0, the core computes the free quantity of a product template as
the sum of its active variants, so archived variants are no longer counted.
The module keeps the smart buttons and list/kanban columns and adds searching
on the template free quantity.
