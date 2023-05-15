from odoo import api, fields, models
from odoo.tools.sql import column_exists, create_column


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    #to be shown in Detailed operations tab

    price_unit = fields.Float("Price Unit", related='move_id.price_unit')
    subtotal = fields.Float("Subtotal", compute='compute_subtotal')
    tax_ids = fields.Many2many(comodel_name='account.tax', related='move_id.sale_line_id.tax_id')

    @api.depends('price_unit','qty_done', 'state', 'reserved_uom_qty')
    def compute_subtotal(self):
        for record in self:
            if record.state != 'done':
               record.subtotal=record.price_unit * record.reserved_uom_qty
            else:
               record.subtotal=record.price_unit * record.qty_done
