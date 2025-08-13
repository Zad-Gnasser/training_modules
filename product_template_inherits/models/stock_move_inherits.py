from odoo import models, api
from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    dimension = fields.Char(string="Dimension")


