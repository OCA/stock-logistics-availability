/* Copyright 2026 Tecnativa - Carlos Roca
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import {qtyAtDateWidget} from "@sale_stock/widgets/qty_at_date_widget";

// The popover renders the "Available to promise" quantity, so the field has to be
// loaded by the widget itself. This way it's available no matter where the widget is
// rendered (order lines list or order line form dialog).
qtyAtDateWidget.fieldDependencies.push({
    name: "immediately_usable_qty_today",
    type: "float",
});
