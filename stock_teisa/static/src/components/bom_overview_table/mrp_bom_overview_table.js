/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { BomOverviewTable } from "@mrp/components/bom_overview_table/mrp_bom_overview_table";
import { formatMonetary } from "@web/views/fields/formatters";

patch(BomOverviewTable.prototype, "shelser_mrp", {
    setup() {
        this._super.apply();
        this.formatMonetaryExtraCurrency = (val,curr) => formatMonetary(val, { currencyId: curr });
    },
});

