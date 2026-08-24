# Copyright 2026 Duwison Guitián S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from collections import defaultdict

from odoo import http
from odoo.osv.expression import AND, OR

from odoo.addons.portal.controllers.portal import (
    CustomerPortal,
)
from odoo.addons.portal.controllers.portal import (
    pager as portal_pager,
)

# Moves not yet done/cancelled: they still represent pending
# incoming/outgoing operations that must be considered for
# forecasted availability.
PENDING_MOVE_STATES = ("waiting", "confirmed", "assigned", "partially_available")


class ConsignedStockCustomerPortal(CustomerPortal):
    """Extends the standard Portal to add the "My Consigned Stock"
    section, allowing an owner (owner_id) to check the availability
    of their own stock.
    """

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "consigned_stock_count" in counters:
            owner = self._get_consigned_stock_owner()
            if owner:
                domain = self._get_consigned_stock_product_domain(owner)
                Product = http.request.env["product.product"].sudo()
                count = Product.search_count(domain)
            else:
                count = 0
            values["consigned_stock_count"] = count
        return values

    def _get_consigned_stock_owner(self):
        """Returns the res.partner acting as the owner (owner_id)
        for the authenticated Portal user.
        """
        partner = http.request.env.user.partner_id
        if not partner:
            return http.request.env["res.partner"]
        return partner.commercial_partner_id

    def _get_consigned_stock_quantity_context(self, owner, warehouse=None):
        """Builds the context used to compute product quantities
        (qty_available, free_qty) strictly isolated to the given
        owner and, when provided, to a single warehouse.
        """
        context = {"owner_id": owner.id}
        if warehouse:
            context["warehouse"] = warehouse.id
        return context

    def _get_consigned_stock_quant_domain(self, owner, warehouse=None):
        """Builds the stock.quant domain identifying the owner's
        stock, always scoped to the allowed companies.
        """
        domain = [
            ("owner_id", "=", owner.id),
            ("company_id", "in", http.request.env.companies.ids),
        ]
        if warehouse:
            domain = AND(
                [domain, [("location_id", "child_of", warehouse.view_location_id.id)]]
            )
        return domain

    def _get_consigned_stock_move_domains(self, owner, warehouse=None):
        """Builds the domains identifying, respectively, pending
        incoming and outgoing stock moves belonging to the owner.

        Incoming moves are identified through the owner set on the
        originating operation (stock.picking.owner_id), since goods
        still in transit have not generated a quant/reservation yet.
        Outgoing moves rely on the standard reservation/restriction
        field (restrict_partner_id) used by stock to reserve quants
        belonging to a specific owner.
        """
        Product = http.request.env["product.product"].sudo()
        context = {}
        if warehouse:
            context["warehouse"] = warehouse.id
        (
            _domain_quant_loc,
            domain_move_in_loc,
            domain_move_out_loc,
        ) = Product.with_context(**context)._get_domain_locations()
        company_domain = [("company_id", "in", http.request.env.companies.ids)]
        state_domain = [("state", "in", PENDING_MOVE_STATES)]

        move_in_domain = AND(
            [
                domain_move_in_loc,
                company_domain,
                state_domain,
                [("picking_id.owner_id", "=", owner.id)],
            ]
        )
        move_out_domain = AND(
            [
                domain_move_out_loc,
                company_domain,
                state_domain,
                [("restrict_partner_id", "=", owner.id)],
            ]
        )
        return move_in_domain, move_out_domain

    def _get_consigned_stock_product_domain(self, owner, warehouse=None):
        """Builds the product.product domain of products visible to
        the owner: products with stock (stock.quant.owner_id) plus
        products with pending incoming/outgoing operations for the
        owner even when they do not have a quant yet.

        Products without any identifiable stock/movement for the
        owner are not shown, avoiding any risk of exposing goods
        belonging to other owners or to the operator itself.
        """
        Quant = http.request.env["stock.quant"].sudo()
        quant_domain = self._get_consigned_stock_quant_domain(
            owner, warehouse=warehouse
        )
        quant_product_ids = Quant.search(quant_domain).mapped("product_id").ids

        move_in_domain, move_out_domain = self._get_consigned_stock_move_domains(
            owner, warehouse=warehouse
        )
        Move = http.request.env["stock.move"].sudo().with_context(active_test=False)
        move_product_ids = (
            Move.search(OR([move_in_domain, move_out_domain])).mapped("product_id").ids
        )

        product_ids = list(set(quant_product_ids) | set(move_product_ids))
        return [("id", "in", product_ids)]

    def _get_consigned_stock_product_values(self, products, owner, warehouse=None):
        """Prepares, in Python, the stock magnitudes shown to the
        Portal user, strictly isolated to the owner, instead of
        passing unfiltered product records to the QWeb view.
        """
        if not products:
            return []

        context = self._get_consigned_stock_quantity_context(owner, warehouse=warehouse)
        products_ctx = products.with_context(**context)

        move_in_domain, _move_out_domain = self._get_consigned_stock_move_domains(
            owner, warehouse=warehouse
        )
        move_in_domain = AND([move_in_domain, [("product_id", "in", products.ids)]])
        Move = http.request.env["stock.move"].sudo().with_context(active_test=False)
        incoming_by_product = defaultdict(float)
        outgoing_by_product = defaultdict(float)
        for move in Move.search(move_in_domain):
            incoming_by_product[
                move.product_id.id
            ] += move.product_uom._compute_quantity(
                move.product_uom_qty, move.product_id.uom_id
            )
        for move in Move.search(_move_out_domain):
            outgoing_by_product[
                move.product_id.id
            ] += move.product_uom._compute_quantity(
                move.product_uom_qty, move.product_id.uom_id
            )

        product_values = []
        for product in products_ctx:
            qty_available = product.qty_available
            free_qty = product.free_qty
            incoming_qty = incoming_by_product.get(product.id, 0.0)
            outgoing_qty = outgoing_by_product.get(product.id, 0.0)
            product_values.append(
                {
                    "product": product,
                    "qty_available": qty_available,
                    "free_qty": free_qty,
                    "incoming_qty": incoming_qty,
                    "outgoing_qty": outgoing_qty,
                    "virtual_available": qty_available + incoming_qty - outgoing_qty,
                }
            )
        return product_values

    def _get_consigned_stock_warehouses(self, owner):
        """Returns only the warehouses in which the owner has
        identifiable stock.
        """
        Quant = http.request.env["stock.quant"].sudo()
        quants = Quant.search(
            [
                ("owner_id", "=", owner.id),
                ("company_id", "in", http.request.env.companies.ids),
            ]
        )
        locations = quants.mapped("location_id")
        if not locations:
            return http.request.env["stock.warehouse"]

        Warehouse = http.request.env["stock.warehouse"].sudo()
        all_warehouses = Warehouse.search(
            [("company_id", "in", http.request.env.companies.ids)]
        )

        def _warehouse_has_owner_stock(warehouse):
            view_id_str = f"/{warehouse.view_location_id.id}/"
            return any(view_id_str in (loc.parent_path or "") for loc in locations)

        return all_warehouses.filtered(_warehouse_has_owner_stock)

    def _get_consigned_stock_searchbar_sortings(self):
        return {
            "name": {"label": ("Name"), "order": "name asc"},
            "name_desc": {"label": ("Name (Z-A)"), "order": "name desc"},
            "code": {
                "label": ("Internal Reference"),
                "order": "default_code asc",
            },
        }

    def _get_consigned_stock_searchbar_inputs(self):
        return {
            "all": {"input": "all", "label": ("Search in All")},
            "name": {"input": "name", "label": ("Search in Name")},
            "reference": {
                "input": "reference",
                "label": ("Search in Internal Reference"),
            },
        }

    def _prepare_consigned_stock_portal_values(
        self, page=1, sortby=None, search="", search_in="all", warehouse_id=None, **kw
    ):
        Product = http.request.env["product.product"].sudo()
        owner = self._get_consigned_stock_owner()

        values = self._prepare_portal_layout_values()

        if not owner:
            values.update(
                {
                    "page_name": "consigned_stock",
                    "owner": owner,
                    "product_values": [],
                    "warehouses": http.request.env["stock.warehouse"],
                    "pager": {},
                    "search": search,
                    "search_in": search_in,
                    "sortby": sortby,
                    "warehouse_id": warehouse_id,
                }
            )
            return values

        warehouses = self._get_consigned_stock_warehouses(owner)
        warehouse = None
        if warehouse_id:
            try:
                warehouse_id = int(warehouse_id)
            except (TypeError, ValueError):
                warehouse_id = False
            if warehouse_id:
                # Only a warehouse belonging to the set allowed for
                # the owner can be used; any other value is ignored.
                warehouse = warehouses.filtered(lambda w: w.id == warehouse_id)
                warehouse = warehouse[:1]
                if not warehouse:
                    warehouse_id = False

        domain = self._get_consigned_stock_product_domain(owner, warehouse=warehouse)
        domain = AND(
            [
                domain,
                [
                    "|",
                    ("company_id", "=", False),
                    ("company_id", "in", http.request.env.companies.ids),
                ],
            ]
        )

        # Search (standard Portal infrastructure)
        searchbar_inputs = self._get_consigned_stock_searchbar_inputs()
        if search and search_in:
            if search_in == "all":
                domain = AND(
                    [
                        domain,
                        OR(
                            [
                                [("name", "ilike", search)],
                                [("default_code", "ilike", search)],
                            ]
                        ),
                    ]
                )
            elif search_in == "name":
                domain = AND([domain, [("name", "ilike", search)]])
            elif search_in == "reference":
                domain = AND([domain, [("default_code", "ilike", search)]])

        # Sorting
        searchbar_sortings = self._get_consigned_stock_searchbar_sortings()
        if not sortby or sortby not in searchbar_sortings:
            sortby = "name"
        order = searchbar_sortings[sortby]["order"]

        product_count = Product.search_count(domain)

        pager = portal_pager(
            url="/my/consigned-stock",
            url_args={
                "sortby": sortby,
                "search": search,
                "search_in": search_in,
                "warehouse_id": warehouse_id,
            },
            total=product_count,
            page=page,
            step=self._items_per_page,
        )

        products = Product.search(
            domain, order=order, limit=self._items_per_page, offset=pager["offset"]
        )
        product_values = self._get_consigned_stock_product_values(
            products, owner, warehouse=warehouse
        )

        values.update(
            {
                "page_name": "consigned_stock",
                "owner": owner,
                "product_values": product_values,
                "warehouses": warehouses,
                "warehouse": warehouse,
                "warehouse_id": warehouse_id or "",
                "pager": pager,
                "search": search,
                "search_in": search_in,
                "sortby": sortby,
                "searchbar_sortings": searchbar_sortings,
                "searchbar_inputs": searchbar_inputs,
                "default_url": "/my/consigned-stock",
            }
        )
        return values

    @http.route(
        ["/my/consigned-stock", "/my/consigned-stock/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_consigned_stock(
        self, page=1, sortby=None, search="", search_in="all", warehouse_id=None, **kw
    ):
        values = self._prepare_consigned_stock_portal_values(
            page=page,
            sortby=sortby,
            search=search,
            search_in=search_in,
            warehouse_id=warehouse_id,
            **kw,
        )
        return http.request.render(
            "stock_available_portal_owner.portal_my_consigned_stock", values
        )
