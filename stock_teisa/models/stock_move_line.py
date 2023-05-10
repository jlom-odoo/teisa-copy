from odoo import api, fields, models
from odoo.tools.sql import column_exists, create_column


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    #to be shown in Detailed operations tab

    price_unit = fields.Float("Price Unit", related='move_id.sale_line_id.price_unit')
    subtotal = fields.Float("Subtotal", compute='compute_subtotal')
    tax_ids = fields.Many2many("Tax ids", related='move_id.sale_line_id.tax_id')

    @api.depends('price_unit','qty_done')
    def compute_subtotal(self):
        for record in self:
            record.subtotal=record.price_unit * record.qty_done

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
            taxes=self.sale_line_id.tax_id,
            price_unit=self.price_unit,
            quantity=self.quantity_done,
            discount=self.sale_line_id.discount,
            price_subtotal=self.subtotal,
        )            