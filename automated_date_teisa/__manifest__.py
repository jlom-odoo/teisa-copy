{
    "name": "Accounting and Bill Date Always the Same",
    "description": """
    Made an automated function that once the user changes the bill date (invoicing date) 
    and saves the vendor bill, then the accounting date will be automatically changed
    to what the bill date has.

    GRAM: AWAI
    TASK ID: 3891517
    """,
    "author": "Odoo Inc.",
    "website": "http://www.odoo.com",
    "category": "Customizations",
    "license": "OPL-1",
    "version": "1.0.0",
    "depends": [ "stock" , "sale_management", "sale_stock", "purchase_stock", "account" , "base_automation"],
    "data": [
        "views/account_move_automation_views.xml",
    ],
}
