from odoo import fields
from odoo.tests import Form
from odoo.addons.mrp.tests.common import TestMrpCommon

from freezegun import freeze_time
@freeze_time(fields.Date.today())
class TestBoM(TestMrpCommon):

    def test_01_bom_report(self):
        """ Simulate a crumble receipt with mrp and open the bom structure
        report and check that data inside are correct.
        Add mark add_to_bom set as true to 2 currencies  
        """
        currency_added_one = self.env['res.currency'].create({
            'name': 'ZEN',
            'symbol': 'Z',
            'rounding': 0.01,
            'currency_unit_label': 'Zenny',
            'rate': 2,
            'active': True,
            'add_to_bom': True
        })
        currency_added_two = self.env['res.currency'].create({
            'name': 'NIC',
            'symbol': 'N',
            'rounding': 0.01,
            'currency_unit_label': 'Nicky',
            'rate': 3,
            'active': True,
            'add_to_bom': True
        })
        currency_not_added = self.env['res.currency'].create({
            'name': 'CHR',
            'symbol': 'C',
            'rounding': 0.01,
            'currency_unit_label': 'Chr',
            'rate': 2,
            'active': True,
            'add_to_bom': False
        })
        currency_not_active = self.env['res.currency'].create({
            'name': 'DAN',
            'symbol': 'D',
            'rounding': 0.01,
            'currency_unit_label': 'Danny',
            'rate': 2,
            'active': False,
            'add_to_bom': True
        })
        uom_kg = self.env.ref('uom.product_uom_kgm')
        uom_litre = self.env.ref('uom.product_uom_litre')
        crumble = self.env['product.product'].create({
            'name': 'Crumble',
            'type': 'product',
            'uom_id': uom_kg.id,
            'uom_po_id': uom_kg.id,
        })
        butter = self.env['product.product'].create({
            'name': 'Butter',
            'type': 'product',
            'uom_id': uom_kg.id,
            'uom_po_id': uom_kg.id,
            'standard_price': 7.01
        })
        biscuit = self.env['product.product'].create({
            'name': 'Biscuit',
            'type': 'product',
            'uom_id': uom_kg.id,
            'uom_po_id': uom_kg.id,
            'standard_price': 1.5
        })
        bom_form_crumble = Form(self.env['mrp.bom'])
        bom_form_crumble.product_tmpl_id = crumble.product_tmpl_id
        bom_form_crumble.product_qty = 11
        bom_form_crumble.product_uom_id = uom_kg
        bom_crumble = bom_form_crumble.save()

        workcenter = self.env['mrp.workcenter'].create({
            'costs_hour': 10,
            'name': 'Deserts Table'
        })

        # Required to display `operation_ids` in the form view
        self.env.user.groups_id += self.env.ref("mrp.group_mrp_routings")
        with Form(bom_crumble) as bom:
            with bom.bom_line_ids.new() as line:
                line.product_id = butter
                line.product_uom_id = uom_kg
                line.product_qty = 5
            with bom.bom_line_ids.new() as line:
                line.product_id = biscuit
                line.product_uom_id = uom_kg
                line.product_qty = 6
            with bom.operation_ids.new() as operation:
                operation.workcenter_id = workcenter
                operation.name = 'Prepare biscuits'
                operation.time_cycle_manual = 5
                operation.bom_id = bom_crumble  # Can't handle by the testing env
            with bom.operation_ids.new() as operation:
                operation.workcenter_id = workcenter
                operation.name = 'Prepare butter'
                operation.time_cycle_manual = 3
                operation.bom_id = bom_crumble
            with bom.operation_ids.new() as operation:
                operation.workcenter_id = workcenter
                operation.name = 'Mix manually'
                operation.time_cycle_manual = 5
                operation.bom_id = bom_crumble

        report_values = self.env['report.mrp.report_bom_structure']._get_report_data(bom_id=bom_crumble.id, searchQty=11, searchVariant=False)
        bom_cost_currencies = report_values['lines']['bom_cost_currencies']
        currency_added_one_is_present=False
        currency_added_two_is_present=False
        currency_not_added_is_present=False
        currency_not_active_is_present=False

        for currency in bom_cost_currencies:
            if (currency['id'] == currency_added_one.id):
                currency_added_one_is_present=True
            if (currency['id'] == currency_added_two.id):
                currency_added_two_is_present=True
            if (currency['id'] == currency_not_added.id):
                currency_not_added_is_present=True            
            if (currency['id'] == currency_not_active.id):
                currency_not_active_is_present=True

        self.assertTrue(currency_added_one_is_present, 'currency should be present')
        self.assertTrue(currency_added_two_is_present, 'currency should be present')
        self.assertFalse(currency_not_added_is_present, 'currency should not be present')
        self.assertFalse(currency_not_active_is_present, 'currency should not be present')

        for component_line in report_values['lines']['components']:
            bom_cost_currencies = component_line['bom_cost_currencies']
            currency_added_one_is_present=False
            currency_added_two_is_present=False
            currency_not_added_is_present=False
            currency_not_active_is_present=False

            for currency in bom_cost_currencies:
                if (currency['id'] == currency_added_one.id):
                    currency_added_one_is_present=True
                if (currency['id'] == currency_added_two.id):
                    currency_added_two_is_present=True
                if (currency['id'] == currency_not_added.id):
                    currency_not_added_is_present=True            
                if (currency['id'] == currency_not_active.id):
                    currency_not_active_is_present=True

            self.assertTrue(currency_added_one_is_present, 'currency should be present')
            self.assertTrue(currency_added_two_is_present, 'currency should be present')
            self.assertFalse(currency_not_added_is_present, 'currency should not be present')
            self.assertFalse(currency_not_active_is_present, 'currency should not be present')

