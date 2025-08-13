
from odoo import models, fields


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    dimension = fields.Char(
        string='Dimension',
        readonly=True
    )