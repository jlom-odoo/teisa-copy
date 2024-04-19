from odoo import api, fields, models

class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    tax_totals = fields.Binary(string="Tax totals moves", compute="_compute_tax_totals")

    @api.depends("move_ids.tax_ids", "move_ids.teisa_price_unit", "company_id")
    def _compute_tax_totals(self):
        for picking in self:
            if picking.picking_type_code == "incoming" or picking.picking_type_code == "outgoing":
                move_ids = picking.move_ids.filtered(lambda x: not x.purchase_line_id.display_type and not x.sale_line_id.display_type)   
            else:
                move_ids = []
            picking.tax_totals = self.env["account.tax"]._prepare_tax_totals(
                [x._convert_to_tax_base_line_dict() for x in move_ids],
                picking.sale_id.currency_id if picking.sale_id else picking.company_id.currency_id,
                )

    def do_print_picking_remision(self):
        return self.env.ref("stock.action_report_picking_remision_teisa").report_action(self)


class StockMove(models.Model):
    _inherit = "stock.move"
    
    teisa_price_unit = fields.Float("Price Unit", compute="_compute_teisa_price_unit")
    subtotal = fields.Float("Subtotal", compute="_compute_subtotal")
    tax_ids = fields.Many2many(comodel_name="account.tax", compute="_compute_teisa_price_unit")

    @api.depends("quantity_done", "picking_code", "origin_returned_move_id", "sale_line_id", "purchase_line_id")
    def _compute_teisa_price_unit(self):
        for move in self:
            if move.picking_code == "incoming":
                if move.origin_returned_move_id:
                    move.teisa_price_unit = move.origin_returned_move_id.sale_line_id.price_unit
                    move.tax_ids = move.origin_returned_move_id.sale_line_id.tax_id
                else:
                    move.teisa_price_unit = move.purchase_line_id.price_unit
                    move.tax_ids = move.purchase_line_id.taxes_id
            elif move.picking_code == "outgoing": 
                move.teisa_price_unit = move.sale_line_id.price_unit
                move.tax_ids = move.sale_line_id.tax_id
            else:
                move.teisa_price_unit = 0
                move.tax_ids = False

    @api.depends("teisa_price_unit","quantity_done")
    def _compute_subtotal(self):
        for move in self:
            move.subtotal = move.teisa_price_unit * move.quantity_done

    def _convert_to_tax_base_line_dict(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        currency = False
        discount = 0

        if self.picking_code == "incoming":
            if self.origin_returned_move_id:
                currency = self.origin_returned_move_id.sale_line_id.currency_id
            else:
                currency = self.purchase_line_id.currency_id
        if self.picking_code == "outgoing": 
            currency = self.sale_line_id.currency_id
            discount = self.sale_line_id.discount
        
        return self.env["account.tax"]._convert_to_tax_base_line_dict(
            self,
            partner=self.partner_id,
            currency=currency,
            product=self.product_id, 
            taxes=self.tax_ids,
            price_unit=self.teisa_price_unit,
            quantity=self.quantity_done,
            discount=discount,
            price_subtotal=self.subtotal,
        )

