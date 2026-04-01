
[![Support the OCA](https://odoo-community.org/readme-banner-image)](https://odoo-community.org/get-involved?utm_source=repo-readme)

# Stock Availability
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/stock-logistics-availability&target_branch=18.0)
[![Pre-commit Status](https://github.com/OCA/stock-logistics-availability/actions/workflows/pre-commit.yml/badge.svg?branch=18.0)](https://github.com/OCA/stock-logistics-availability/actions/workflows/pre-commit.yml?query=branch%3A18.0)
[![Build Status](https://github.com/OCA/stock-logistics-availability/actions/workflows/test.yml/badge.svg?branch=18.0)](https://github.com/OCA/stock-logistics-availability/actions/workflows/test.yml?query=branch%3A18.0)
[![codecov](https://codecov.io/gh/OCA/stock-logistics-availability/branch/18.0/graph/badge.svg)](https://codecov.io/gh/OCA/stock-logistics-availability)
[![Translation Status](https://translation.odoo-community.org/widgets/stock-logistics-availability-18-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/stock-logistics-availability-18-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

This repository contains modules to provide more information about product stock availability in terms of quantities

Are you looking for modules related to logistics? Or would like to contribute
to? There are many repositories with specific purposes. Have a look at this
[README](https://github.com/OCA/wms/blob/18.0/README.md).

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[stock_available](stock_available/) | 18.0.1.0.0 |  | Stock available to promise
[stock_available_base_exclude_location](stock_available_base_exclude_location/) | 18.0.1.0.2 | <a href='https://github.com/rousseldenis'><img src='https://github.com/rousseldenis.png' width='32' height='32' style='border-radius:50%;' alt='rousseldenis'/></a> | Base module to exclude locations for product available quantities
[stock_available_immediately](stock_available_immediately/) | 18.0.1.0.0 |  | Ignore planned receptions in quantity available to promise
[stock_available_immediately_exclude_location](stock_available_immediately_exclude_location/) | 18.0.1.0.0 |  | Exclude locations from immediately usable quantity
[stock_available_location_get_domain](stock_available_location_get_domain/) | 18.0.1.0.0 |  | This is a technical helper module in order to reuse the standard _get_domain_locations() function for locations and not quants
[stock_available_unreserved](stock_available_unreserved/) | 18.0.2.0.0 | <a href='https://github.com/LoisRForgeFlow'><img src='https://github.com/LoisRForgeFlow.png' width='32' height='32' style='border-radius:50%;' alt='LoisRForgeFlow'/></a> | Quantity of stock available for immediate use
[stock_free_quantity](stock_free_quantity/) | 18.0.1.1.0 |  | Stock Free Quantity
[stock_picking_product_availability_inline](stock_picking_product_availability_inline/) | 18.0.1.0.0 | <a href='https://github.com/CarlosRoca13'><img src='https://github.com/CarlosRoca13.png' width='32' height='32' style='border-radius:50%;' alt='CarlosRoca13'/></a> | Show product availability in product drop-down of picking form view.

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
