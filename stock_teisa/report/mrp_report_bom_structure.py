from odoo import fields, models, _

class ReportBomStructure(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'

    def _get_bom_data(self, bom, warehouse, product=False, line_qty=False, bom_line=False, level=0, parent_bom=False, index=0, product_info=False, ignore_stock=False):
        res = super()._get_bom_data(bom, warehouse, product, line_qty, bom_line, level, parent_bom, index, product_info, ignore_stock)
        company, currencies = self.get_additional_currencies(bom)
        bom_cost_currencies = []
        for currency_id in currencies:
            bom_cost_currency = company.currency_id._convert(res['bom_cost'], currency_id, company,fields.Date.today())
            rounded_bom_cost_currency = currency_id.round(bom_cost_currency)
            bom_cost_currencies.append({
                'id': currency_id.id,    
                'name': _('BoM Cost converted into ') + currency_id.name,
                'value': rounded_bom_cost_currency
            })    
        res['bom_cost_currencies'] = bom_cost_currencies
        res['bom_cost_main_currency_name'] = _('BoM Cost ') + company.currency_id.name
        return res

    def _get_component_data(self, bom, warehouse, bom_line, line_quantity, level, index, product_info, ignore_stock=False):
        res = super()._get_component_data(bom, warehouse, bom_line, line_quantity, level, index, product_info, ignore_stock)
        company, currencies = self.get_additional_currencies(bom)
        bom_cost_currencies = []
        for currency_id in currencies:
            bom_cost_currency = company.currency_id._convert(res['bom_cost'], currency_id, company,fields.Date.today())
            rounded_bom_cost_currency = currency_id.round(bom_cost_currency)
            bom_cost_currencies.append({'id': currency_id.id, 'value': rounded_bom_cost_currency})    
        res['bom_cost_currencies'] = bom_cost_currencies   
        return res

    def _get_byproducts_lines(self, product, bom, bom_quantity, level, total, index):
        byproducts, byproduct_cost_portion = super()._get_byproducts_lines(product, bom, bom_quantity, level, total, index)
        company, currencies = self.get_additional_currencies(bom)
        for byproduct in byproducts:
            bom_cost_currencies = []
            for currency_id in currencies:
                bom_cost_currency = company.currency_id._convert(byproduct['bom_cost'], currency_id, company,fields.Date.today())
                rounded_bom_cost_currency = currency_id.round(bom_cost_currency)
                bom_cost_currencies.append({'id': currency_id.id, 'value': rounded_bom_cost_currency
                })    
            byproduct['bom_cost_currencies'] = bom_cost_currencies   
        return byproducts, byproduct_cost_portion

    def _get_operation_line(self,  product, bom, qty, level, index):
        operations = super()._get_operation_line(product, bom, qty, level, index)
        company, currencies = self.get_additional_currencies(bom)
        for operation in operations:
            bom_cost_currencies = []
            for currency_id in currencies:
                bom_cost_currency = company.currency_id._convert(operation['bom_cost'], currency_id, company,fields.Date.today())
                rounded_bom_cost_currency = currency_id.round(bom_cost_currency)
                bom_cost_currencies.append({'id': currency_id.id, 'value': rounded_bom_cost_currency})    
            operation['bom_cost_currencies'] = bom_cost_currencies   
        return operations

    def get_additional_currencies(self,bom):
        company = bom.company_id or self.env.company
        domain = [('add_to_bom', '=', True),('id', '!=', company.currency_id.id)]
        currencies = self.env['res.currency'].search(domain)
        return company, currencies

