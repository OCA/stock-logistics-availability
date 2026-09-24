from odoo import _
from odoo.http import request as Request
from odoo.http import route
from odoo.osv.expression import AND, OR

from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.stock_available_portal_owner.controllers.portal import (
    ConsignedStockCustomerPortal,
)


class ConsignedStockCustomerPortalExtended(ConsignedStockCustomerPortal):
    @route(
        [
            "/my/consigned-stock/lots/<int:product_id>",
            "/my/consigned-stock/lots/<int:product_id>/page/<int:page>",
        ],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_consigned_stock_by_lot(
        self,
        product_id,
        page=1,
        sortby=None,
        search="",
        search_in="all",
        warehouse_id=None,
        date_from=None,
        date_to=None,
        **kw,
    ):
        values = self._prepare_consigned_stock_by_lot_portal_values(
            product_id=product_id,
            page=page,
            sortby=sortby,
            search=search,
            search_in=search_in,
            warehouse_id=warehouse_id,
            date_from=date_from,
            date_to=date_to,
            **kw,
        )
        return Request.render(
            "stock_available_portal_owner_lots.portal_my_consigned_stock_by_lots",
            values,
        )

    def _get_consigned_stock_product_quant_domain(
        self, owner, product_id, warehouse=None
    ):
        domain = [("owner_id", "=", owner.id), ("product_id", "=", product_id)]
        if warehouse:
            domain.append(("warehouse_id", "=", warehouse))
        return domain

    def _get_consigned_stock_by_lot_searchbar_inputs(self):
        return {
            "all": {"input": "all", "label": _("Search in All")},
            "lot": {"input": "lot", "label": _("Search by Lot/serial")},
        }

    def _get_consigned_stock_by_lot_searchbar_sortings(self):
        return {
            "name": {"label": _("Lot/Serial"), "order": "name asc"},
            "name_desc": {"label": _("Lot/Serial (Z-A)"), "order": "name desc"},
            "date": {
                "label": _("Expiration Date"),
                "order": "expiration_date asc",
            },
        }

    def _prepare_consigned_stock_by_lot_portal_values(
        self,
        product_id,
        page=1,
        sortby=None,
        search="",
        search_in="all",
        warehouse_id=None,
        date_from=None,
        date_to=None,
        **kw,
    ):
        owner = self._get_consigned_stock_owner()
        values = self._prepare_portal_layout_values()

        if not owner:
            values.update(
                {
                    "page_name": "consigned_stock_by_lot",
                    "owner": owner,
                    "product_id": product_id,
                    "product": None,
                    "lot_ids": Request.env["stock.lot"],
                    "pager": {},
                    "search": search,
                    "search_in": search_in,
                    "sortby": sortby,
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

        domain = self._get_consigned_stock_product_quant_domain(
            owner, product_id, warehouse=warehouse_id.id if warehouse_id else None
        )
        Quant = Request.env["stock.quant"].sudo()

        quant_lot_ids = Quant.search(domain).mapped("lot_id").ids
        lot_domain = [("id", "in", quant_lot_ids)]
        domain = AND(
            [
                lot_domain,
                [
                    "|",
                    ("company_id", "=", False),
                    ("company_id", "in", Request.env.companies.ids),
                ],
            ]
        )

        # Search (standard Portal infrastructure)
        searchbar_inputs = self._get_consigned_stock_by_lot_searchbar_inputs()
        if search and search_in:
            if search_in == "all":
                lot_domain = AND(
                    [
                        lot_domain,
                        OR([[("name", "ilike", search)]]),
                    ]
                )
            elif search_in == "lot":
                lot_domain = AND([lot_domain, [("name", "ilike", search)]])

        # Sorting
        searchbar_sortings = self._get_consigned_stock_by_lot_searchbar_sortings()
        if not sortby or sortby not in searchbar_sortings:
            sortby = "name"
        order = searchbar_sortings[sortby]["order"]

        if date_from and date_to:
            lot_domain = AND(
                [
                    lot_domain,
                    [
                        ("expiration_date", ">", date_from),
                        ("expiration_date", "<", date_to),
                    ],
                ]
            )

        Lot = Request.env["stock.lot"].sudo()
        lots_count = Lot.search_count(lot_domain)

        # Corrección: Enviar el ID al paginador, no el recordset
        pager = portal_pager(
            url="/my/consigned-stock/lots/%s" % product_id,
            url_args={
                "sortby": sortby,
                "search": search,
                "search_in": search_in,
                "warehouse_id": warehouse_id.id if warehouse_id else None,
            },
            total=lots_count,
            page=page,
            step=self._items_per_page,
        )

        lot_ids = Lot.search(
            lot_domain, order=order, limit=self._items_per_page, offset=pager["offset"]
        )

        values.update(
            {
                "page_name": "consigned_stock_by_lot",
                "owner": owner,
                "lot_ids": lot_ids,
                "product": lot_ids.mapped("product_id"),
                "product_id": product_id,
                "warehouses": warehouses,
                "warehouse": warehouse_id,
                "warehouse_id": warehouse_id.id
                if warehouse_id
                else "",  # Corrección: Devolver el ID
                "pager": pager,
                "search": search,
                "search_in": search_in,
                "sortby": sortby,
                "date_from": date_from,
                "date_to": date_to,
                "searchbar_sortings": searchbar_sortings,
                "searchbar_inputs": searchbar_inputs,
            }
        )
        return values
