
from odoo.addons.stock.tests.common import TestStockCommon
from odoo.tools import mute_logger, float_round
from odoo.tools.misc import formatLang

class TestStockFlowTeisa(TestStockCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        decimal_product_uom = cls.env.ref('product.decimal_product_uom')
        decimal_product_uom.digits = 3
        cls.partner_company2 = cls.env['res.partner'].create({
            'name': 'My Company (Chicago)-demo',
            'email': 'chicago@yourcompany.com',
            'company_id': False,
        })
        cls.partner_id = cls.env['res.partner'].create({
            'name': 'Wood Corner Partner',
            'company_id': cls.env.user.company_id.id,
        })
        cls.company = cls.env['res.company'].create({
            'currency_id': cls.env.ref('base.MXN').id,
            'partner_id': cls.partner_company2.id,
            'name': 'My Company (Chicago)-demo',
        })
        cls.mxn_currency = cls.env.ref('base.MXN')
        cls.tax_10 = cls.env['account.tax'].create({
            'name': 'Tax 10 percent',
            'amount': 10,
            'type_tax_use': 'purchase',
            'price_include': False,
        })
        cls.product1 = cls.env['product.product'].create({
            'name': 'Large Desk',
            'type': 'product',
            # 'categ_id': cls.stock_account_product_categ.id,
            'taxes_id': [cls.tax_10.id],
        })
        cls.product2 = cls.env['product.product'].create({
            'name': 'Small Desk',
            'type': 'product',
            # 'categ_id': cls.stock_account_product_categ.id,
            'taxes_id': [cls.tax_10.id],
        })

    @mute_logger('odoo.addons.base.models.ir_model', 'odoo.models')
    def test_00_picking_incoming_total_taxes(self):
        """ Basic stock operation on incoming and outgoing shipment. """
       
        date_po1 = '2019-01-01'
        po1 = self.env['purchase.order'].create({
            'currency_id': self.mxn_currency.id,
            'partner_id': self.partner_id.id,
            'order_line': [
                (0, 0, {
                    'name': self.product1.name,
                    'product_id': self.product1.id,
                    'product_qty': 8.0,
                    'product_uom': self.product1.uom_po_id.id,
                    'price_unit': 100.0, # 50$
                    'date_planned': date_po1,
                    'taxes_id': [self.tax_10.id]
                }),
                (0, 0, {
                    'name': self.product2.name,
                    'product_id': self.product2.id,
                    'product_qty': 5.0,
                    'product_uom': self.product1.uom_po_id.id,
                    'price_unit': 50.0, # 50$
                    'date_planned': date_po1,
                    'taxes_id': [self.tax_10.id]
                }),
            ],
        })

        #Similar to po1, but different quantities
        date_po2 = '2019-01-02'
        po2 = self.env['purchase.order'].create({
            'currency_id': self.mxn_currency.id,
            'partner_id': self.partner_id.id,
            'order_line': [
                (0, 0, {
                    'name': self.product1.name,
                    'product_id': self.product1.id,
                    'product_qty': 9.0,
                    'product_uom': self.product1.uom_po_id.id,
                    'price_unit': 100.0, # 50$
                    'date_planned': date_po2
                }),
            ],
        })
        picking_in = self.PickingObj.create({
            'picking_type_id': self.picking_type_in,
            'picking_type_code': 'incoming',
            'company_id': self.company.id,
            'location_id': self.supplier_location,
            'location_dest_id': self.stock_location})

         # incoming moves
        move_a = self.MoveObj.create({
            'name': self.product1.name,
            'product_id': self.product1.id,
            'quantity_done': 10,
            'product_uom_qty': 1,
            'product_uom': self.product1.uom_id.id,
            'picking_id': picking_in.id,
            'location_id': self.supplier_location,
            'location_dest_id': self.stock_location,
            'picking_code': 'incoming',
            'purchase_line_id': po1.order_line[0].id})
        move_b = self.MoveObj.create({
            'name': self.product2.name,
            'product_id': self.product1.id,
            'quantity_done': 10,
            'product_uom_qty': 1,
            'product_uom': self.product2.uom_id.id,
            'picking_id': picking_in.id,
            'location_id': self.supplier_location,
            'location_dest_id': self.stock_location,
            'picking_code': 'incoming',
            'purchase_line_id': po1.order_line[1].id})
        # Confirm incoming shipment.
        picking_in.action_confirm()

        # Check incoming shipment move lines state.
        for move in picking_in.move_ids:
            self.assertEqual(move.state, 'assigned', 'Wrong state of move line.')

        # ----------------------------------------------------------------------
        # Incoming order from purchase
        # ----------------------------------------------------------------------
        self.assertEqual(move_a.price_unit, 100, 'The unit_price should be the original price :90 ')
        move_a.quantity_done = 10
        self.assertEqual(move_a.subtotal, 1000, 'The subtotal should be 90* 10')
        move_b.quantity_done = 10
        self.assertEqual(move_b.subtotal, 500, 'The sub total should be 50 * 10 ')
        picking_in.action_assign()
        #changing the price unit to trigger the compute_tax_total method:
        totals = picking_in.tax_totals
        subtotal_group = totals['groups_by_subtotal']['Untaxed Amount']
        # self.assertEqual(len(subtotal_group), 1, 'There should only be one subtotal group (Untaxed Amount)')
        self.assertEqual(totals['amount_untaxed'], 1500, 'amount untaxed is the sum of price unit x quantity_done per line')
        self.assertEqual(totals['amount_total'], 1500, 'amount total should be the sum of subtotals + taxes/Correct this one')

    @mute_logger('odoo.addons.base.models.ir_model', 'odoo.models')
    def test_01_picking_outgoing_total_taxes(self):
        """ Basic stock operation on incoming and outgoing shipment. """
        so1 = self.env['sale.order'].create({
            'currency_id': self.mxn_currency.id,
            'partner_id': self.partner_id.id,
            'order_line': [
                (0, 0, {
                    'name': self.product1.name,
                    'product_id': self.product1.id,
                    'product_uom_qty': 8.0,
                    'product_uom': self.product1.uom_po_id.id,
                    'price_unit': 100.0, # 50$
                    # 'date_planned': date_so1,
                    'tax_id': [self.tax_10.id]
                }),
                (0, 0, {
                    'name': self.product2.name,
                    'product_id': self.product2.id,
                    'product_uom_qty': 5.0,
                    'product_uom': self.product1.uom_po_id.id,
                    'price_unit': 50.0, # 50$
                    # 'date_planned': date_so1,
                    'tax_id': [self.tax_10.id]
                }),
            ],
        })

        picking_out = self.PickingObj.create({
            'picking_type_id': self.picking_type_out,
            'picking_type_code': 'outgoing',
            'company_id': self.company.id,
            'location_id': self.supplier_location,
            'location_dest_id': self.stock_location})

         # outgoing moves
        move_a = self.MoveObj.create({
            'name': self.product1.name,
            'product_id': self.product1.id,
            'quantity_done': 10,
            'product_uom_qty': 1,
            'product_uom': self.product1.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': self.supplier_location,
            'location_dest_id': self.stock_location,
            'picking_code': 'incoming',
            'sale_line_id': so1.order_line[0].id})
        move_b = self.MoveObj.create({
            'name': self.product2.name,
            'product_id': self.product1.id,
            'quantity_done': 10,
            'product_uom_qty': 1,
            'product_uom': self.product2.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': self.supplier_location,
            'location_dest_id': self.stock_location,
            'picking_code': 'incoming',
            'sale_line_id': so1.order_line[1].id})
        # Confirm incoming shipment.
        picking_out.action_confirm()

        # Check incoming shipment move lines state.
        for move in picking_out.move_ids:
            self.assertEqual(move.state, 'assigned', 'Wrong state of move line.')

        # ----------------------------------------------------------------------
        # Outgoing order from sale order
        # ----------------------------------------------------------------------
        self.assertEqual(move_a.price_unit, 100, 'The unit_price should be the original price :90 ')
        move_a.quantity_done = 10
        self.assertEqual(move_a.subtotal, 1000, 'The subtotal should be 90* 10')
        move_b.quantity_done = 10
        self.assertEqual(move_b.subtotal, 500, 'The sub total should be 50 * 10 ')
        picking_out.action_assign()
        #changing the price unit to trigger the compute_tax_total method:
        totals = picking_out.tax_totals
        subtotal_group = totals['groups_by_subtotal']['Untaxed Amount']
        self.assertEqual(totals['amount_untaxed'], 1500, 'amount untaxed is the sum of price unit x quantity_done per line')
        self.assertEqual(totals['amount_total'], 1500, 'amount total should be the sum of subtotals + taxes/Correct this one')
