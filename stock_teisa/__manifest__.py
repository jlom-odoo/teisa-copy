{
    'name': "Teisa Integral: Picking Operations report with prices and total",
    'summary': "Add columns to operations and detailed operations tab",
    'description': """
        Teisa Integral:  
        Task ID: 3247717
        1. Add field to stock move and stock.move.line
        2. Add remision report
    """,
    'author': "Odoo PS",
    'website': "http://www.odoo.com",
    'category': "Customizations",
    'license': "OPL-1",
    'version': "1.0.0",
    'depends': [ 'stock' , 'sale_management', 'sale_stock'],
    'data': [
        'views/stock_picking_views.xml',
        'views/stock_move_views.xml',
        'report/report_stockpicking_remision.xml',
        'report/stock_report_views.xml',
    ],
}
