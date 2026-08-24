# Copyright 2026 Duwison Guitián S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Stock Available Portal Owner",
    "summary": "Consigned stock availability query from the Portal "
    "for owners (owner_id)",
    "version": "17.0.1.0.0",
    "category": "Inventory/Inventory",
    "website": "https://github.com/OCA/stock-logistics-availability",
    "author": "Binhex Systems Solutions S.L., Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "depends": [
        "stock",
        "portal",
    ],
    "data": [
        "views/portal_home_templates.xml",
        "views/portal_consigned_stock_templates.xml",
    ],
}
