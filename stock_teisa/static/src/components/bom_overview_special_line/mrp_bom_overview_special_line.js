/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { BomOverviewSpecialLine } from "@mrp/components/bom_overview_special_line/mrp_bom_overview_special_line";
import { formatMonetary } from "@web/views/fields/formatters";

patch(BomOverviewSpecialLine.prototype, "shelser_mrp", {
    setup() {
        this._super.apply();
        this.formatMonetaryExtraCurrency = (val,curr) => formatMonetary(val, { currencyId: curr });
    },
});
