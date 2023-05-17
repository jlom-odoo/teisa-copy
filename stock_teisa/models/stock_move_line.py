from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    price_unit = fields.Float(string="Price Unit", related="move_id.price_unit")
    subtotal = fields.Float(string="Subtotal", compute="compute_subtotal")
    tax_ids = fields.Many2many(string="Tax ids", comodel_name="account.tax", related="move_id.sale_line_id.tax_id")

    @api.depends("price_unit","qty_done", "state", "reserved_uom_qty")
    def compute_subtotal(self):
        for line in self:
            if line.state != "done":
               line.subtotal=line.price_unit * line.reserved_uom_qty
            else:
               line.subtotal=line.price_unit * line.qty_done

