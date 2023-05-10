{
    'name': "Teisa Integral: Picking Operations report with prices and total",
    'summary': "Add columns to BoM overview",
    'description': """
        Shelser:  
        Task ID: 3247717
        1. Add field to res.currency
        2. Add columns to BoM overview table based on currencies having flag set as True
    """,
    'author': "Odoo PS",
    'website': "http://www.odoo.com",
    'category': "Customizations",
    'license': "OPL-1",
    'version': "1.0.0",
    'depends': [ 'stock' , 'sale_management', 'sale_stock'],
    'data': [
        'views/stock_picking_views.xml',
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'shelser_mrp/static/src/**/*.js',
    #         'shelser_mrp/static/src/**/*.xml',
    #     ],
    # }
}

