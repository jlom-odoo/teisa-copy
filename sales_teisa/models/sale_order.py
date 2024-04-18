from odoo import fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sale_under_margin_allowed = fields.Boolean()
    sale_on_debt_allowed = fields.Boolean()

    def write(self, vals):
        update_state = vals.get('state')
        if not update_state or update_state == "cancel":
            return super().write(vals)
        
        for so in self:
            if so.state not in ["draft", "sent"]:
                continue
            
            # In case sale_loyalty module is installed in the future,
            # only validate these constrains in sale order lines where
            # coupon_id == False
            sale_lines = so.order_line.filtered(lambda l: l.display_type == False)
            if any((line.product_uom_qty > 0 and line.price_unit <= 0) for line in sale_lines): 
                raise UserError(_("At least one sale order line has a unit price $0"))
            
            if sale_lines.filtered(lambda l: l.margin_percent < 0.079) and not so.sale_under_margin_allowed: 
                raise UserError(_("At least one sale order line has a margin under 7.9%"))
            
            if any((line.discount and line.discount > 3 and not line.discount_over_limit_allowed) for line in sale_lines):
                raise UserError(_("At least one sale order line has a discount over 3%"))
            
            if any(line.product_id.default_code == "99999" for line in sale_lines): 
                raise UserError(_("At least one sale order line has the generic product"))
            
            if any(line.delivery_time_teisa == False for line in sale_lines): 
                raise UserError(_("At least one sale order line does not have TEISA delivery time set"))
            
            if so.partner_credit_warning and not so.sale_on_debt_allowed:
                raise UserError(_("Total amount of this sale order is bigger than the credit limit of the customer"))
            
            if not so.partner_id.sale_warn == 'no-message' and update_state not in ['sent','draft'] and not so.sale_on_debt_allowed: 
                raise UserError(so.partner_id.sale_warn_msg)
        
        return super().write(vals)
