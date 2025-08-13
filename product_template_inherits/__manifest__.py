# -*- coding: utf-8 -*-
{
    'name': "Product Template Inherits",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
                   Long description of module's purpose
                       """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Purchases',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sale','stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_template_inherits_view.xml',
        'views/sale_order_inherits_view.xml',
        'views/stock_move_inherits_view.xml',
        'views/account_move_inherits_view.xml',

    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
    'installable': True,
    'application': True,
}
