# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Available Location Orderpoint",
    "summary": """
        Allows to retrieve the quantity to replenish on a product from a
        location orderpoint (stock_location_orderpoint)""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-availability",
    "depends": [
        "stock_location_orderpoint",
        "stock_available",
        "stock_available_location_get_domain",
    ],
    "data": ["views/product_product.xml", "views/product_template.xml"],
}
