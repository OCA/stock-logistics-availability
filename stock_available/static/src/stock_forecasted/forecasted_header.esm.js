/* Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import {ForecastedHeader} from "@stock/stock_forecasted/forecasted_header";
import {patch} from "@web/core/utils/patch";

patch(ForecastedHeader.prototype, {
    get immediatelyUsableQty() {
        return Object.values(this.products).reduce(
            (sum, product) => sum + product.immediately_usable_qty,
            0
        );
    },
});
