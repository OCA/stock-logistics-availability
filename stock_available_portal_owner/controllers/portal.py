# Copyright 2026 Duwison Guitián S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from collections import defaultdict

from odoo import _
from odoo.http import request as Request
from odoo.http import route
from odoo.osv.expression import AND, OR

from odoo.addons.portal.controllers.portal import (
    CustomerPortal,
)
from odoo.addons.portal.controllers.portal import (
    pager as portal_pager,
)

# Move lines not yet done/cancelled represent detailed or reserved
# incoming/outgoing operations for forecasted availability.
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
            if not owner:
                values["consigned_stock_count"] = "0"
                return values
            domain = self._get_consigned_stock_product_domain(owner)
            Product = Request.env["product.product"].sudo()
            product_consigned_count = Product.search_count(domain)
            values["consigned_stock_count"] = (
                product_consigned_count if product_consigned_count else "0"
            )
        return values

    def _get_consigned_stock_owner(self):
        """Returns the res.partner acting as the owner (owner_id)
        for the authenticated Portal user.
        """
        partner = Request.env.user.partner_id
        return partner or partner.commercial_partner_id

    def _get_consigned_stock_move_domains(self, owner, warehouse=None):
        """Builds domains for detailed/reserved move lines by direction.

        Only move lines with a positive quantity are considered. The
        owner is read from the move line itself so that incoming and
        outgoing figures only represent operations already detailed or
        reserved for this owner.
        """
        Product = Request.env["product.product"].sudo()
        context = {}
        if warehouse:
            context["warehouse"] = warehouse.id
        (
            domain_quant_loc,
            domain_move_in_loc,
            domain_move_out_loc,
        ) = Product.with_context(**context)._get_domain_locations()
        company_domain = [("company_id", "in", Request.env.companies.ids)]
        state_domain = [("state", "in", PENDING_MOVE_STATES)]
        owner_domain = [("owner_id", "in", [owner.id, owner.commercial_partner_id.id])]
        quantity_domain = [("quantity_product_uom", ">", 0)]

        move_in_domain = AND(
            [
                domain_move_in_loc,
                company_domain,
                state_domain,
                owner_domain,
                quantity_domain,
            ]
        )
        move_out_domain = AND(
            [
                domain_move_out_loc,
                company_domain,
                state_domain,
                owner_domain,
                quantity_domain,
            ]
        )
        domain_quant = AND(
            [
                domain_quant_loc,
                owner_domain,
            ]
        )
        return domain_quant, move_in_domain, move_out_domain

    def _get_consigned_stock_product_domain(self, owner, warehouse=None):
        """Builds the product.product domain of products visible to
        the owner: products with stock (stock.quant.owner_id) plus
        products with pending incoming/outgoing operations for the
        owner even when they do not have a quant yet.

        Products without any identifiable stock/movement for the
        owner are not shown, avoiding any risk of exposing goods
        belonging to other owners or to the operator itself.
        """
        Quant = Request.env["stock.quant"].sudo()
        MoveLine = Request.env["stock.move.line"].sudo()

        (
            quant_domain,
            move_in_domain,
            move_out_domain,
        ) = self._get_consigned_stock_move_domains(owner, warehouse=warehouse)
        quant_product_ids = Quant.search(quant_domain).mapped("product_id")

        move_in_product_ids = MoveLine.search(move_in_domain).mapped("product_id")
        move_out_product_ids = MoveLine.search(move_out_domain).mapped("product_id")

        product_ids = quant_product_ids | move_in_product_ids | move_out_product_ids
        return [("id", "in", product_ids.ids)]

    def _get_consigned_stock_product_values(self, products, owner, warehouse=None):
        """Prepares, in Python, the stock magnitudes shown to the
        Portal user, strictly isolated to the owner, instead of
        passing unfiltered product records to the QWeb view.
        """
        if not products:
            return []

        MoveLine = Request.env["stock.move.line"].sudo()
        context = {}
        if warehouse:
            context["warehouse"] = warehouse.id
        res = products.with_context(**context)._compute_quantities_dict(
            lot_id=None,
            owner_id=owner.id,
            package_id=None,
            from_date=False,
            to_date=False,
        )

        (
            quant_domain,
            move_in_domain,
            move_out_domain,
        ) = self._get_consigned_stock_move_domains(owner, warehouse=warehouse)
        move_in_domain = AND([move_in_domain, [("product_id", "in", products.ids)]])
        move_out_domain = AND([move_out_domain, [("product_id", "in", products.ids)]])

        incoming_by_product = defaultdict(float)
        outgoing_by_product = defaultdict(float)
        for move_line in MoveLine.search(move_in_domain):
            incoming_by_product[
                move_line.product_id.id
            ] += move_line.quantity_product_uom
        for move_line in MoveLine.search(move_out_domain):
            outgoing_by_product[
                move_line.product_id.id
            ] += move_line.quantity_product_uom

        product_values = []
        for product in products:
            qty_available = res[product.id]["qty_available"]
            free_qty = res[product.id]["free_qty"]
            incoming_qty = (
                res[product.id]["incoming_qty"]
                if res[product.id]["incoming_qty"]
                else incoming_by_product.get(product.id, 0.0)
            )
            outgoing_qty = (
                res[product.id]["outgoing_qty"]
                if res[product.id]["outgoing_qty"]
                else outgoing_by_product.get(product.id, 0.0)
            )
            if not qty_available:
                continue
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
        Quant = Request.env["stock.quant"].sudo()
        quants = Quant.search(
            [
                ("owner_id", "in", [owner.id, owner.commercial_partner_id.id]),
                ("company_id", "in", Request.env.companies.ids),
            ]
        )
        locations = quants.mapped("location_id")
        if not locations:
            return Request.env["stock.warehouse"]

        Warehouse = Request.env["stock.warehouse"].sudo()
        all_warehouses = Warehouse.search(
            [("company_id", "in", Request.env.companies.ids)]
        )

        def _warehouse_has_owner_stock(warehouse):
            view_id = str(warehouse.view_location_id.id)
            return any(
                loc.parent_path
                and (
                    loc.parent_path.startswith(f"{view_id}/")
                    or f"/{view_id}/" in loc.parent_path
                )
                for loc in locations
            )

        warehouse_ids = all_warehouses.filtered(_warehouse_has_owner_stock)
        return warehouse_ids

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
            "all": {"input": "all", "label": _("Search in All")},
            "name": {"input": "name", "label": _("Search in Name")},
            "reference": {
                "input": "reference",
                "label": _("Search in Internal Reference"),
            },
        }

    def _prepare_consigned_stock_portal_values(
        self, page=1, sortby=None, search="", search_in="all", warehouse_id=None, **kw
    ):
        Product = Request.env["product.product"].sudo()
        owner = self._get_consigned_stock_owner()

        values = self._prepare_portal_layout_values()

        if not owner:
            values.update(
                {
                    "page_name": "consigned_stock",
                    "owner": owner,
                    "product_values": [],
                    "warehouses": Request.env["stock.warehouse"],
                    "pager": {},
                    "search": search,
                    "search_in": search_in,
                    "sortby": sortby,
                    "warehouse_id": warehouse_id,
                }
            )
            return values

        warehouses = self._get_consigned_stock_warehouses(owner)
        if warehouse_id:
            try:
                warehouse_id = warehouses.browse(int(warehouse_id))
                if warehouse_id not in warehouses:
                    warehouse_id = False
            except ValueError:
                warehouse_id = False

        domain = self._get_consigned_stock_product_domain(owner, warehouse=warehouse_id)
        domain = AND(
            [
                domain,
                [
                    "|",
                    ("company_id", "=", False),
                    ("company_id", "in", Request.env.companies.ids),
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
            products, owner, warehouse=warehouse_id
        )

        values.update(
            {
                "page_name": "consigned_stock",
                "owner": owner,
                "product_values": product_values,
                "warehouses": warehouses,
                "warehouse": warehouse_id,
                "warehouse_id": warehouse_id or "0",
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

    @route(
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
        return Request.render(
            "stock_available_portal_owner.portal_my_consigned_stock", values
        )
