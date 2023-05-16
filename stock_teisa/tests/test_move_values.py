# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo import fields, tests
from odoo.fields import Command
from odoo.tests.common import Form


class TestReportStockQuantity(tests.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product1 = cls.env['product.product'].create({
            'name': 'Mellohi1',
            'default_code': 'C418',
            'type': 'product',
            'categ_id': cls.env.ref('product.product_category_all').id,
            'lst_price': '100',
            'tracking': 'lot'
        })
        cls.product2 = cls.env['product.product'].create({
            'name': 'Mellohi2',
            'default_code': 'C418',
            'type': 'product',
            'categ_id': cls.env.ref('product.product_category_all').id,
            'lst_price': '100',
            'tracking': 'lot'
        })
        cls.wh = cls.env['stock.warehouse'].create({
            'name': 'Base Warehouse',
            'code': 'TESTWH'
        })
        cls.categ_unit = cls.env.ref('uom.product_uom_categ_unit')
        cls.uom_unit = cls.env['uom.uom'].search([('category_id', '=', cls.categ_unit.id), ('uom_type', '=', 'reference')], limit=1)
        cls.customer_location = cls.env.ref('stock.stock_location_customers')
        cls.supplier_location = cls.env.ref('stock.stock_location_suppliers')
        # replenish
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                Command.create({
                    'product_id': cls.product1.id,
                    'product_uom_qty': 5.0,
                }),
                Command.create({
                    'product_id': cls.service_product.id,
                    'product_uom_qty': 12.5,
                })
            ]
        })
        cls.move1 = cls.env['stock.move'].create({
            'name': 'test_incoming_1',
            'location_id': cls.supplier_location.id,
            'location_dest_id': cls.wh.lot_stock_id.id,
            'product_id': cls.product1.id,
            'product_uom': cls.uom_unit.id,
            'product_uom_qty': 100.0,
            'state': 'done',
            'date': fields.Datetime.now(),
        })
        cls.quant1 = cls.env['stock.quant'].create({
            'product_id': cls.product1.id,
            'location_id': cls.wh.lot_stock_id.id,
            'quantity': 100.0,
        })

        # ship
        cls.move2 = cls.env['stock.move'].create({
            'name': 'test_out_1',
            'location_id': cls.wh.lot_stock_id.id,
            'location_dest_id': cls.customer_location.id,
            'product_id': cls.product1.id,
            'product_uom': cls.uom_unit.id,
            'product_uom_qty': 120.0,
            'state': 'partially_available',
            'date': fields.Datetime.add(fields.Datetime.now(), days=3),
            'date_deadline': fields.Datetime.add(fields.Datetime.now(), days=3),
        })

    def test_report_stock_quantity(self):
        from_date = fields.Date.to_string(fields.Date.add(fields.Date.today(), days=-1))
        to_date = fields.Date.to_string(fields.Date.add(fields.Date.today(), days=4))
        report = self.env['report.stock.quantity'].read_group(
            [('date', '>=', from_date), ('date', '<=', to_date), ('product_id', '=', self.product1.id)],
            ['product_qty', 'date', 'product_id', 'state'],
            ['date:day', 'product_id', 'state'],
            lazy=False)
        forecast_report = [x['product_qty'] for x in report if x['state'] == 'forecast']
        self.assertEqual(forecast_report, [0, 100, 100, 100, -20, -20])

    def test_report_stock_quantity_stansit(self):
        wh2 = self.env['stock.warehouse'].create({'name': 'WH2', 'code': 'WH2'})
        transit_loc = self.wh.company_id.internal_transit_location_id

        self.move_transit_out = self.env['stock.move'].create({
            'name': 'test_transit_out_1',
            'location_id': self.wh.lot_stock_id.id,
            'location_dest_id': transit_loc.id,
            'product_id': self.product1.id,
            'product_uom': self.uom_unit.id,
            'product_uom_qty': 25.0,
            'state': 'assigned',
            'date': fields.Datetime.now(),
            'date_deadline': fields.Datetime.now(),
        })
        self.move_transit_in = self.env['stock.move'].create({
            'name': 'test_transit_in_1',
            'location_id': transit_loc.id,
            'location_dest_id': wh2.lot_stock_id.id,
            'product_id': self.product1.id,
            'product_uom': self.uom_unit.id,
            'product_uom_qty': 25.0,
            'state': 'waiting',
            'date': fields.Datetime.now(),
            'date_deadline': fields.Datetime.now(),
        })

        self.env.flush_all()
        report = self.env['report.stock.quantity'].read_group(
            [('date', '>=', fields.Date.today()), ('date', '<=', fields.Date.today()), ('product_id', '=', self.product1.id)],
            ['product_qty', 'date', 'product_id', 'state'],
            ['date:day', 'product_id', 'state'],
            lazy=False)

        forecast_in_report = [x['product_qty'] for x in report if x['state'] == 'in']
        self.assertEqual(forecast_in_report, [25])
        forecast_out_report = [x['product_qty'] for x in report if x['state'] == 'out']
        self.assertEqual(forecast_out_report, [-25])