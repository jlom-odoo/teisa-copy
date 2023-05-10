/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { BomOverviewLine } from "@mrp/components/bom_overview_line/mrp_bom_overview_line";
import { formatMonetary } from "@web/views/fields/formatters";

patch(BomOverviewLine.prototype, "shelser_mrp", {
    setup() {
        this._super.apply();
        this.formatMonetaryExtraCurrency = (val,curr) => formatMonetary(val, { currencyId: curr });
    },
});

