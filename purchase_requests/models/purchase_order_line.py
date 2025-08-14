# -*- coding: utf-8 -*-
from odoo import models, fields

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    purchase_request_line_id = fields.Many2one(
        'purchase.requests.line',
        string='Purchase Request Line',
        readonly=True,
    )