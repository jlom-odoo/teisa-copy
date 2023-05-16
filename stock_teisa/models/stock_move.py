from odoo import api, fields, models

class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    tax_totals = fields.Binary("Tax totals", compute='_compute_tax_totals')

    @api.depends('move_ids.tax_ids', 'move_ids.price_unit', 'company_id')
    def _compute_tax_totals(self):
        for picking in self:
            if picking.picking_type_code == 'incoming' or picking.picking_type_code == 'outgoing':
                move_ids = picking.move_ids.filtered(lambda x: not x.purchase_line_id.display_type and not x.sale_line_id.display_type)   
            else:
                move_ids = False      
            if move_ids:
                picking.tax_totals = self.env['account.tax']._prepare_tax_totals(
                    [x._convert_to_tax_base_line_dict() for x in move_ids],
                    picking.company_id.currency_id,
                )
            else:
                picking.tax_totals = False

    def do_print_picking_remision(self):
        return self.env.ref('stock.action_report_picking_remision').report_action(self)
class StockMove(models.Model):
    _inherit = "stock.move"
    
    price_unit = fields.Float("Price Unit", compute='_compute_price_unit')
    subtotal = fields.Float("Subtotal", compute='_compute_subtotal')
    tax_ids = fields.Many2many(comodel_name='account.tax', compute='_compute_tax_ids')

    @api.depends('quantity_done')
    def _compute_price_unit(self):
        for record in self:
            if record.picking_code == 'incoming':
                if record.origin_returned_move_id:
                    record.price_unit = record.origin_returned_move_id.sale_line_id.price_unit
                else:
                    record.price_unit = record.purchase_line_id.price_unit
            elif record.picking_code == 'outgoing': 
                record.price_unit = record.sale_line_id.price_unit
            else:
                record.price_unit = 0

    def _compute_tax_ids(self):
        for record in self:
            if record.picking_code == 'incoming':
                if record.origin_returned_move_id:
                    record.tax_ids = record.origin_returned_move_id.sale_line_id.tax_id
                else:
                    record.tax_ids = record.purchase_line_id.taxes_id
            elif record.picking_code == 'outgoing': 
                record.tax_ids = record.sale_line_id.tax_id
            else:
                record.tax_ids = False

    @api.depends('price_unit','quantity_done')
    def _compute_subtotal(self):
        for record in self:
            record.subtotal = record.price_unit * record.quantity_done

    def _convert_to_tax_base_line_dict(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        currency = False
        discount = 0

        if self.picking_code == 'incoming':
            if self.origin_returned_move_id:
                currency = self.origin_returned_move_id.sale_line_id.currency_id
            else:
                currency = self.purchase_line_id.currency_id
        if self.picking_code == 'outgoing': 
            currency = self.sale_line_id.currency_id
            discount = self.sale_line_id.discount
        
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.partner_id,
            currency=currency,
            product=self.product_id, 
            taxes=self.tax_ids,
            price_unit=self.price_unit,
            quantity=self.quantity_done,
            discount=discount,
            price_subtotal=self.subtotal,
        )            