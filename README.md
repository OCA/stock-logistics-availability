
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/stock-logistics-availability&target_branch=16.0)
[![Pre-commit Status](https://github.com/OCA/stock-logistics-availability/actions/workflows/pre-commit.yml/badge.svg?branch=16.0)](https://github.com/OCA/stock-logistics-availability/actions/workflows/pre-commit.yml?query=branch%3A16.0)
[![Build Status](https://github.com/OCA/stock-logistics-availability/actions/workflows/test.yml/badge.svg?branch=16.0)](https://github.com/OCA/stock-logistics-availability/actions/workflows/test.yml?query=branch%3A16.0)
[![codecov](https://codecov.io/gh/OCA/stock-logistics-availability/branch/16.0/graph/badge.svg)](https://codecov.io/gh/OCA/stock-logistics-availability)
[![Translation Status](https://translation.odoo-community.org/widgets/stock-logistics-availability-16-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/stock-logistics-availability-16-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# Stock Availability modules

 This repository contains modules to provide more information about product stock availability in terms of quantities

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[sale_stock_available_info_popup](sale_stock_available_info_popup/) | 16.0.1.0.0 |  | Adds an 'Available to promise' quantity to the popover shown in sale order line that display stock info of the product
[stock_available](stock_available/) | 16.0.1.1.0 |  | Stock available to promise
[stock_available_base_exclude_location](stock_available_base_exclude_location/) | 16.0.1.0.0 | [![rousseldenis](https://github.com/rousseldenis.png?size=30px)](https://github.com/rousseldenis) | Base module to exclude locations for product available quantities
[stock_available_immediately](stock_available_immediately/) | 16.0.1.0.0 |  | Ignore planned receptions in quantity available to promise
[stock_available_immediately_exclude_location](stock_available_immediately_exclude_location/) | 16.0.1.0.0 |  | Exclude locations from immediately usable quantity
[stock_available_mrp](stock_available_mrp/) | 16.0.1.0.0 |  | Consider the production potential is available to promise
[stock_available_unreserved](stock_available_unreserved/) | 16.0.1.0.0 | [![LoisRForgeFlow](https://github.com/LoisRForgeFlow.png?size=30px)](https://github.com/LoisRForgeFlow) | Quantity of stock available for immediate use
[stock_free_quantity](stock_free_quantity/) | 16.0.1.0.0 |  | Stock Free Quantity

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
