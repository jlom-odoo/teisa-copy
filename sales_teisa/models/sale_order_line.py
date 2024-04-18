from odoo import fields, models
from .constants import DELIVERY_TIME_OPTIONS

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    delivery_time_teisa = fields.Selection(selection=DELIVERY_TIME_OPTIONS)
    discount_over_limit_allowed = fields.Boolean()
