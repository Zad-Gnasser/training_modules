from odoo import models
from odoo import fields, models


class ProductTemplateInherits(models.Model):
    _inherit = 'product.template'

    dimension = fields.Char(
        string='Dimension',
        help='Dimension of the product, e.g., "(e.g 4cm * 12 cm)"'    )


