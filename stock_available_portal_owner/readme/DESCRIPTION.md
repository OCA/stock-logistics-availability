This module adds a new section to the Odoo Portal, "My Consigned Stock",
allowing owners of consigned goods (owner_id) to independently check the
availability of their own products.

Isolation of information between owners is guaranteed for every
quantity shown: on hand and free stock rely on the standard `owner_id`
concept of `stock.quant`, while incoming and outgoing quantities are
computed from the pending stock moves whose originating operation
(`stock.picking`) or reservation is linked to the authenticated owner.
Forecasted stock is derived exclusively from these owner-isolated
figures. Products are only listed when they have identifiable stock or
pending movements for the authenticated owner.
