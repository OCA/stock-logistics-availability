import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-stock-logistics-availability",
    description="Meta package for oca-stock-logistics-availability Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-sale_stock_available_info_popup>=16.0dev,<16.1dev',
        'odoo-addon-stock_available>=16.0dev,<16.1dev',
        'odoo-addon-stock_available_base_exclude_location>=16.0dev,<16.1dev',
        'odoo-addon-stock_available_immediately>=16.0dev,<16.1dev',
        'odoo-addon-stock_available_immediately_exclude_location>=16.0dev,<16.1dev',
        'odoo-addon-stock_available_mrp>=16.0dev,<16.1dev',
        'odoo-addon-stock_available_unreserved>=16.0dev,<16.1dev',
        'odoo-addon-stock_free_quantity>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
