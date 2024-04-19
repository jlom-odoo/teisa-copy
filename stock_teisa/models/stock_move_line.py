from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    price_unit = fields.Float(string="Price Unit", related="move_id.teisa_price_unit")
    subtotal = fields.Float(string="Subtotal", compute="_compute_subtotal")
    tax_ids = fields.Many2many(string="Tax ids", comodel_name="account.tax", related="move_id.sale_line_id.tax_id")

    @api.depends("price_unit", "qty_done")
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.price_unit * line.qty_done

