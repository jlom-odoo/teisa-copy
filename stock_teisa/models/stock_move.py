from odoo import api, fields, models

class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    tax_totals = fields.Binary("Tax totals", compute='_compute_tax_totals')

    @api.depends('move_ids.tax_ids', 'move_ids.price_unit', 'company_id')
    def _compute_tax_totals(self):
        for picking in self:
            #applying equivalent filter to the one applied in sale order
            move_ids = picking.move_ids.filtered(lambda x: x.picking_code == 'outgoing' and not x.sale_line_id.display_type )
            picking.tax_totals = self.env['account.tax']._prepare_tax_totals(
                [x._convert_to_tax_base_line_dict() for x in move_ids],
                picking.company_id.currency_id,
            )

class StockMove(models.Model):
    _inherit = "stock.move"
    
    price_unit = fields.Float("Price Unit", related='sale_line_id.price_unit')
    #we want to take this from the sale order for the price not to vary 
    subtotal = fields.Float("Subtotal", compute='_compute_subtotal')
    tax_ids = fields.Many2many(comodel_name='account.tax', related='sale_line_id.tax_id')

    @api.depends('price_unit','quantity_done')
    def _compute_subtotal(self):
        for record in self:
            print('SSSSSSSSSSSsale_line_id', record.sale_line_id)
            print('PPPPPPPPPPicking code', record.picking_code)
            record.subtotal = record.price_unit * record.quantity_done

    def _convert_to_tax_base_line_dict(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.partner_id,
            currency=self.sale_line_id.currency_id,
            product=self.product_id, 
            taxes=self.tax_ids,
            price_unit=self.price_unit,
            quantity=self.quantity_done,
            discount=self.sale_line_id.discount,
            price_subtotal=self.subtotal,
        )            