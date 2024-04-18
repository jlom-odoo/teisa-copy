{
    "name": "Teisa Integral: Sales Orders Restrictions",
    "description": 
    """
      This module validates creation and confirmation of
      Sales Orders according to the users business rules:

      - They can't confirm a SO if the price is 0 and the quantity is more than 0.

      - They can't sell with a margin on a line less than 7.9% unless it is allowed by an admin.

      - They can't confirm a SO with the generic product "99999".

      - They must include the "Tiempo de entrega Teisa" field.

      - The credit limit of the customer must not be exceeded with this SO.

      - The can't confirm a SO if the credit limit of the customer is already exceeded.

      Developer: JLOM
      
      Task ID: 3866925
      """,
    "category": "Custom Development",
    "version": "1.0.0",
    "author": "Odoo Development Services",
    "maintainer": "Odoo Development Services",
    "website": "https://www.odoo.com/",
    "license": "OPL-1",
    "depends": [
        "sale_margin",
    ],
    "data": [
        "views/sale_order_views.xml",
    ],
    "demo": [
        "demo/ir_default_demo.xml",
    ],
}
