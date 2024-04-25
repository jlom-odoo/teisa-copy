from odoo import fields, Command
from freezegun import freeze_time
from datetime import timedelta

import freezegun


from odoo.addons.account.tests.test_account_move_in_invoice import TestAccountMoveInInvoiceOnchanges
from odoo.addons.purchase_stock.tests.test_stockvaluation import TestStockValuationWithCOA
from odoo.addons.account.tests.test_account_move_date_algorithm import TestAccountMoveDateAlgorithm

from odoo.tests.common import Form


def pass_test_in_invoice_create_1(self):
    # Test creating an account_move with the least information.
    # Changed date to be the same as invoice_date taking into 
    # consideration the automated action that makes them the same

    move = self.env['account.move'].create({
        'move_type': 'in_invoice',
        'partner_id': self.partner_a.id,
        'invoice_date': fields.Date.from_string('2019-01-01'),
        'currency_id': self.currency_data['currency'].id,
        'invoice_payment_term_id': self.pay_terms_a.id,
        'invoice_line_ids': [
            Command.create({
                'product_id': self.product_line_vals_1['product_id'],
                'product_uom_id': self.product_line_vals_1['product_uom_id'],
                'price_unit': self.product_line_vals_1['price_unit'],
                'tax_ids': [Command.set(self.product_line_vals_1['tax_ids'])],
            }),
            Command.create({
                'product_id': self.product_line_vals_2['product_id'],
                'product_uom_id': self.product_line_vals_2['product_uom_id'],
                'price_unit': self.product_line_vals_2['price_unit'],
                'tax_ids': [Command.set(self.product_line_vals_2['tax_ids'])],
            }),
        ],
    })

    self.assertInvoiceValues(move, [
        {
            **self.product_line_vals_1,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': 800.0,
            'debit': 400.0,
        },
        {
            **self.product_line_vals_2,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': 160.0,
            'debit': 80.0,
        },
        {
            **self.tax_line_vals_1,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': 144.0,
            'debit': 72.0,
        },
        {
            **self.tax_line_vals_2,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': 24.0,
            'debit': 12.0,
        },
        {
            **self.term_line_vals_1,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': -1128.0,
            'credit': 564.0,
        },
    ], {
        **self.move_vals,
        'currency_id': self.currency_data['currency'].id,
        # Changed the field created from 2019-01-31 to 2019-01-01
        # to take into consideration the fact that when the bill is 
        # created it will have the same value as invoice_date which
        # is 2019-01-01
        'date': fields.Date.from_string('2019-01-01'),
    })


def pass_test_in_invoice_create_refund_multi_currency(self):
        ''' Test the account.move.reversal takes care about the currency rates when setting
        a custom reversal date.
        '''
        # Commented al the dates so that test dont take it into considerations since its 
        # changed to the invoice_date
        with Form(self.invoice) as move_form:
            # move_form.date = '2016-01-01'
            move_form.currency_id = self.currency_data['currency']

        self.invoice.action_post()

        # The currency rate changed from 1/3 to 1/2.
        move_reversal = self.env['account.move.reversal'].with_context(active_model="account.move", active_ids=self.invoice.ids).create({
            # 'date': fields.Date.from_string('2016-01-01'),
            'reason': 'no reason',
            'refund_method': 'refund',
            'journal_id': self.invoice.journal_id.id,
        })
        reversal = move_reversal.reverse_moves()
        reverse_move = self.env['account.move'].browse(reversal['res_id'])

        self.assertEqual(self.invoice.payment_state, 'not_paid', "Refunding with a draft credit note should keep the invoice 'not_paid'.")
        self.assertInvoiceValues(reverse_move, [
            {
                **self.product_line_vals_1,
                'amount_currency': -800.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 0.0,
                'credit': 400.0,
            },
            {
                **self.product_line_vals_2,
                'amount_currency': -160.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 0.0,
                'credit': 80.0,
            },
            {
                **self.tax_line_vals_1,
                'amount_currency': -144.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 0.0,
                'credit': 72.0,
            },
            {
                **self.tax_line_vals_2,
                'amount_currency': -24.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 0.0,
                'credit': 12.0,
            },
            {
                **self.term_line_vals_1,
                'name': '',
                'amount_currency': 1128.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 564.0,
                'credit': 0.0,
                'date_maturity': move_reversal.date,
            },
        ], {
            **self.move_vals,
            'invoice_payment_term_id': None,
            'currency_id': self.currency_data['currency'].id,
            'date': move_reversal.date,
            'state': 'draft',
            'ref': 'Reversal of: %s, %s' % (self.invoice.name, move_reversal.reason),
            'payment_state': 'not_paid',
        })

        move_reversal = self.env['account.move.reversal'].with_context(active_model="account.move", active_ids=self.invoice.ids).create({
            # 'date': fields.Date.from_string('2016-01-01'),
            'reason': 'no reason again',
            'refund_method': 'cancel',
            'journal_id': self.invoice.journal_id.id,
        })
        reversal = move_reversal.reverse_moves()
        reverse_move = self.env['account.move'].browse(reversal['res_id'])

        self.assertEqual(self.invoice.payment_state, 'reversed', "After cancelling it with a reverse invoice, an invoice should be in 'reversed' state.")
        self.assertInvoiceValues(reverse_move, [
            {
                **self.product_line_vals_1,
                'amount_currency': -800.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 0.0,
                'credit': 400.0,
            },
            {
                **self.product_line_vals_2,
                'amount_currency': -160.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 0.0,
                'credit': 80.0,
            },
            {
                **self.tax_line_vals_1,
                'amount_currency': -144.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 0.0,
                'credit': 72.0,
            },
            {
                **self.tax_line_vals_2,
                'amount_currency': -24.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 0.0,
                'credit': 12.0,
            },
            {
                **self.term_line_vals_1,
                'name': '',
                'amount_currency': 1128.0,
                'currency_id': self.currency_data['currency'].id,
                'debit': 564.0,
                'credit': 0.0,
                'date_maturity': move_reversal.date,
            },
        ], {
            **self.move_vals,
            'invoice_payment_term_id': None,
            'currency_id': self.currency_data['currency'].id,
            'date': move_reversal.date,
            'state': 'posted',
            'ref': 'Reversal of: %s, %s' % (self.invoice.name, move_reversal.reason),
            'payment_state': 'paid',
        })


@freeze_time('2021-09-16')
def pass_test_in_invoice_onchange_invoice_date_2(self):
    invoice_form = Form(self.env['account.move'].with_context(default_move_type='in_invoice', account_predictive_bills_disable_prediction=True))
    invoice_form.partner_id = self.partner_a
    invoice_form.invoice_payment_term_id = self.env.ref('account.account_payment_term_30days')
    with invoice_form.invoice_line_ids.new() as line_form:
        line_form.product_id = self.product_a
    invoice_form.invoice_date = fields.Date.from_string('2021-09-01')
    invoice = invoice_form.save()

    self.assertRecordValues(invoice, [{
        'date': fields.Date.from_string('2021-09-01'),
        'invoice_date': fields.Date.from_string('2021-09-01'),
        'invoice_date_due': fields.Date.from_string('2021-10-01'),
    }])


def pass_test_in_invoice_onchange_invoice_date(self):
    # Changed the invoice_date and accouting_date to be the same
    # so that the test can pass
    for tax_date, invoice_date, accounting_date in [
        ('2019-03-31', '2019-05-31', '2019-05-31'),
        ('2019-03-31', '2019-04-30', '2019-04-30'),
        ('2019-05-31', '2019-06-30', '2019-06-30'),
    ]:
        self.invoice.company_id.tax_lock_date = tax_date
        with Form(self.invoice) as move_form:
            move_form.invoice_date = invoice_date
        self.assertEqual(self.invoice.date, fields.Date.to_date(accounting_date))


def pass_test_in_invoice_switch_in_refund_1(self):
    # Test creating an account_move with an in_invoice_type and switch it in an in_refund.
    move = self.env['account.move'].create({
        'move_type': 'in_invoice',
        'partner_id': self.partner_a.id,
        'invoice_date': fields.Date.from_string('2019-01-01'),
        'currency_id': self.currency_data['currency'].id,
        'invoice_payment_term_id': self.pay_terms_a.id,
        'invoice_line_ids': [
            Command.create({
                'product_id': self.product_line_vals_1['product_id'],
                'product_uom_id': self.product_line_vals_1['product_uom_id'],
                'price_unit': self.product_line_vals_1['price_unit'],
                'tax_ids': [Command.set(self.product_line_vals_1['tax_ids'])],
            }),
            Command.create({
                'product_id': self.product_line_vals_2['product_id'],
                'product_uom_id': self.product_line_vals_2['product_uom_id'],
                'price_unit': self.product_line_vals_2['price_unit'],
                'tax_ids': [Command.set(self.product_line_vals_2['tax_ids'])],
            }),
        ],
    })
    move.action_switch_invoice_into_refund_credit_note()

    self.assertRecordValues(move, [{'move_type': 'in_refund'}])
    self.assertInvoiceValues(move, [
        {
            **self.product_line_vals_1,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': -800.0,
            'credit': 400.0,
            'debit': 0,
        },
        {
            **self.product_line_vals_2,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': -160.0,
            'credit': 80.0,
            'debit': 0,
        },
        {
            **self.tax_line_vals_1,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': -144.0,
            'credit': 72.0,
            'debit': 0,
        },
        {
            **self.tax_line_vals_2,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': -24.0,
            'credit': 12.0,
            'debit': 0,
        },
        {
            **self.term_line_vals_1,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': 1128.0,
            'debit': 564.0,
            'credit': 0,
        },
    ], {
        **self.move_vals,
        # Changed the field created from 2019-01-31 to 2019-01-01
        # to take into consideration the fact that when the bill is 
        # created it will have the same value as invoice_date which
        # is 2019-01-01
        'date': fields.Date.from_string('2019-01-01'),
        'currency_id': self.currency_data['currency'].id,
    })


def pass_test_in_invoice_switch_in_refund_2(self):
    # Test creating an account_move with an in_invoice_type and switch it in an in_refund and a negative quantity.
    move = self.env['account.move'].create({
        'move_type': 'in_invoice',
        'partner_id': self.partner_a.id,
        'invoice_date': fields.Date.from_string('2019-01-01'),
        'currency_id': self.currency_data['currency'].id,
        'invoice_payment_term_id': self.pay_terms_a.id,
        'invoice_line_ids': [
            Command.create({
                'product_id': self.product_line_vals_1['product_id'],
                'product_uom_id': self.product_line_vals_1['product_uom_id'],
                'price_unit': self.product_line_vals_1['price_unit'],
                'quantity': -self.product_line_vals_1['quantity'],
                'tax_ids': [Command.set(self.product_line_vals_1['tax_ids'])],
            }),
            Command.create({
                'product_id': self.product_line_vals_2['product_id'],
                'product_uom_id': self.product_line_vals_2['product_uom_id'],
                'price_unit': self.product_line_vals_2['price_unit'],
                'quantity': -self.product_line_vals_2['quantity'],
                'tax_ids': [Command.set(self.product_line_vals_2['tax_ids'])],
            }),
        ],
    })

    self.assertInvoiceValues(move, [
        {
            **self.product_line_vals_1,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': -800.0,
            'price_subtotal': -800.0,
            'price_total': -920.0,
            'credit': 400.0,
            'debit': 0,
            'quantity': -1.0,
        },
        {
            **self.product_line_vals_2,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': -160.0,
            'price_subtotal': -160.0,
            'price_total': -208.0,
            'credit': 80.0,
            'debit': 0,
            'quantity': -1.0,
        },
        {
            **self.tax_line_vals_1,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': -144.0,
            'credit': 72.0,
            'debit': 0,
        },
        {
            **self.tax_line_vals_2,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': -24.0,
            'credit': 12.0,
            'debit': 0,
        },
        {
            **self.term_line_vals_1,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': 1128.0,
            'debit': 564.0,
            'credit': 0,
        },
    ], {
        **self.move_vals,
        # Changed the field created from 2019-01-31 to 2019-01-01
        # to take into consideration the fact that when the bill is 
        # created it will have the same value as invoice_date which
        # is 2019-01-01
        'date': fields.Date.from_string('2019-01-01'),
        'currency_id': self.currency_data['currency'].id,
        'amount_tax' : -self.move_vals['amount_tax'],
        'amount_total' : -self.move_vals['amount_total'],
        'amount_untaxed' : -self.move_vals['amount_untaxed'],
    })
    move.action_switch_invoice_into_refund_credit_note()

    self.assertRecordValues(move, [{'move_type': 'in_refund'}])
    self.assertInvoiceValues(move, [
        {
            **self.product_line_vals_1,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': -800.0,
            'credit': 400.0,
            'debit': 0,
        },
        {
            **self.product_line_vals_2,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': -160.0,
            'credit': 80.0,
            'debit': 0,
        },
        {
            **self.tax_line_vals_1,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': -144.0,
            'credit': 72.0,
            'debit': 0,
        },
        {
            **self.tax_line_vals_2,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': -24.0,
            'credit': 12.0,
            'debit': 0,
        },
        {
            **self.term_line_vals_1,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': 1128.0,
            'debit': 564.0,
            'credit': 0,
        },
    ], {
        **self.move_vals,
        # Changed the field created from 2019-01-31 to 2019-01-01
        # to take into consideration the fact that when the bill is 
        # created it will have the same value as invoice_date which
        # is 2019-01-01
        'date': fields.Date.from_string('2019-01-01'),
        'currency_id': self.currency_data['currency'].id,
        'amount_tax' : self.move_vals['amount_tax'],
        'amount_total' : self.move_vals['amount_total'],
        'amount_untaxed' : self.move_vals['amount_untaxed'],
    })


def pass_test_in_invoice_write_1(self):
    # Test creating an account_move with the least information.
    move = self.env['account.move'].create({
        'move_type': 'in_invoice',
        'partner_id': self.partner_a.id,
        'invoice_date': fields.Date.from_string('2019-01-01'),
        'currency_id': self.currency_data['currency'].id,
        'invoice_payment_term_id': self.pay_terms_a.id,
        'invoice_line_ids': [
            Command.create({
                'product_id': self.product_line_vals_1['product_id'],
                'product_uom_id': self.product_line_vals_1['product_uom_id'],
                'price_unit': self.product_line_vals_1['price_unit'],
                'tax_ids': [Command.set(self.product_line_vals_1['tax_ids'])],
            }),
        ],
    })
    move.write({
        'invoice_line_ids': [
            Command.create({
                'product_id': self.product_line_vals_2['product_id'],
                'product_uom_id': self.product_line_vals_2['product_uom_id'],
                'price_unit': self.product_line_vals_2['price_unit'],
                'tax_ids': [Command.set(self.product_line_vals_2['tax_ids'])],
            }),
        ],
    })

    self.assertInvoiceValues(move, [
        {
            **self.product_line_vals_1,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': 800.0,
            'debit': 400.0,
        },
        {
            **self.product_line_vals_2,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': 160.0,
            'debit': 80.0,
        },
        {
            **self.tax_line_vals_1,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': 144.0,
            'debit': 72.0,
        },
        {
            **self.tax_line_vals_2,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': 24.0,
            'debit': 12.0,
        },
        {
            **self.term_line_vals_1,
            'currency_id': self.currency_data['currency'].id,
            'amount_currency': -1128.0,
            'credit': 564.0,
        },
    ], {
        **self.move_vals,
        # Changed the field created from 2019-01-31 to 2019-01-01
        # to take into consideration the fact that when the bill is 
        # created it will have the same value as invoice_date which
        # is 2019-01-01
        'date': fields.Date.from_string('2019-01-01'),
        'currency_id': self.currency_data['currency'].id,
    })


def pass_test_pdiff_multi_curr_and_rates(self):
    """
    Company in USD.
    Today: 100 EUR = 150 USD
    One day ago: 100 EUR = 130 USD
    Two days ago: 100 EUR = 125 USD
    Buy and receive one auto-AVCO product at 100 EUR. Bill it with:
    - Bill date: two days ago (125 USD)
    - Accounting date: one day ago (130 USD)
    The value at bill date should be used for both bill value and price
    diff value.
    """
    usd_currency = self.env.ref('base.USD')
    eur_currency = self.env.ref('base.EUR')

    today = fields.Date.today()
    one_day_ago = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)
    
    self.env.company.currency_id = usd_currency.id

    self.env['res.currency.rate'].search([]).unlink()
    self.env['res.currency.rate'].create([{
        'name': day.strftime('%Y-%m-%d'),
        'rate': 1 / rate,
        'currency_id': eur_currency.id,
        'company_id': self.env.company.id,
    } for (day, rate) in [
        (today, 1.5),
        (one_day_ago, 1.3),
        (two_days_ago, 1.25),
    ]])

    self.product1.product_tmpl_id.categ_id.property_cost_method = 'average'

    po = self.env['purchase.order'].create({
        'partner_id': self.partner_id.id,
        'currency_id': eur_currency.id,
        'order_line': [
            (0, 0, {
                'name': self.product1.name,
                'product_id': self.product1.id,
                'product_qty': 1.0,
                'product_uom': self.product1.uom_po_id.id,
                'price_unit': 100.0,
                'taxes_id': False,
            }),
        ],
    })
    po.button_confirm()

    receipt = po.picking_ids
    receipt.move_ids.move_line_ids.qty_done = 1.0
    receipt.button_validate()

    layer = receipt.move_ids.stock_valuation_layer_ids
    self.assertEqual(layer.value, 150)

    action = po.action_create_invoice()
    bill = self.env["account.move"].browse(action["res_id"])
    bill.invoice_date = two_days_ago
    bill.date = two_days_ago
    bill.action_post()

    pdiff_layer = layer.stock_valuation_layer_ids
    self.assertEqual(pdiff_layer.value, -25)
    self.assertEqual(layer.remaining_value, 125)

    in_stock_amls = self.env['account.move.line'].search([
        ('product_id', '=', self.product1.id),
        ('account_id', '=', self.stock_input_account.id),
    ], order='id')
    # Changed the date so that the date is the same for both, 
    # since the new module makes invoice_date and date the same
    self.assertRecordValues(in_stock_amls, [
        # pylint: disable=bad-whitespace
        {'date': today,         'debit': 0,     'credit': 150,  'reconciled': True},
        {'date': two_days_ago,   'debit': 125,   'credit': 0,    'reconciled': True},
        {'date': two_days_ago,   'debit': 25,    'credit': 0,    'reconciled': True},
    ])

@freezegun.freeze_time('2017-01-12')
def pass_test_in_invoice_date_with_lock_date(self):
    self._set_lock_date('2016-12-31')
    move = self._create_invoice('in_invoice', '2017-01-01')
    move.action_post()

    self.assertRecordValues(move, [{
        'invoice_date': fields.Date.from_string('2017-01-01'),
        'date': fields.Date.from_string('2017-01-01'),
    }])

@freezegun.freeze_time('2017-01-12')
def pass_test_in_refund_date_with_lock_date(self):
    self._set_lock_date('2016-12-31')
    move = self._create_invoice('in_refund', '2017-01-01')
    move.action_post()

    self.assertRecordValues(move, [{
        'invoice_date': fields.Date.from_string('2017-01-01'),
        'date': fields.Date.from_string('2017-01-01'),
    }])

TestAccountMoveInInvoiceOnchanges.test_in_invoice_create_1 = pass_test_in_invoice_create_1
TestAccountMoveInInvoiceOnchanges.test_in_invoice_create_refund_multi_currency = pass_test_in_invoice_create_refund_multi_currency
TestAccountMoveInInvoiceOnchanges.test_in_invoice_onchange_invoice_date = pass_test_in_invoice_onchange_invoice_date
TestAccountMoveInInvoiceOnchanges.test_in_invoice_onchange_invoice_date_2 = pass_test_in_invoice_onchange_invoice_date_2
TestAccountMoveInInvoiceOnchanges.test_in_invoice_switch_in_refund_1 = pass_test_in_invoice_switch_in_refund_1
TestAccountMoveInInvoiceOnchanges.test_in_invoice_switch_in_refund_2 = pass_test_in_invoice_switch_in_refund_2
TestAccountMoveInInvoiceOnchanges.test_in_invoice_write_1 = pass_test_in_invoice_write_1

TestStockValuationWithCOA.test_pdiff_multi_curr_and_rates = pass_test_pdiff_multi_curr_and_rates

TestAccountMoveDateAlgorithm.test_in_invoice_date_with_lock_date = pass_test_in_invoice_date_with_lock_date
TestAccountMoveDateAlgorithm.test_in_refund_date_with_lock_date = pass_test_in_refund_date_with_lock_date
