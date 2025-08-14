from odoo import models, fields, api


class PurchaseRequestsLine(models.Model):
    _name = 'purchase.requests.line'
    _description = 'purchase_requests_line'

    # Product reference
    product_id = fields.Many2one(
        'product.product', string='Product', required=True, )

    request_id = fields.Many2one('purchase.requests', string='Purchase Request')

    quantity = fields.Float(string='Quantity', required=True, default=1.0, )

    description = fields.Text(string='Description', required=True, )

    cost_price = fields.Float(string='Cost Price', required=True, default=0.0)

    total = fields.Float(string='Total', compute='_compute_total', store=True)

    tax = fields.Many2many('account.tax', string='Taxes', required=True)

    purchase_order_line_ids = fields.One2many(
        'purchase.order.line',
        'purchase_request_line_id',
        string='Purchase Order Lines'
    )

    quantity_ordered = fields.Float(
        string='Ordered Quantity',
        compute='_compute_ordered_quantity',
        store=True,
    )

    quantity_remaining = fields.Float(
        string='Remaining Quantity',
        compute='_compute_ordered_quantity',
        store=True,
    )

    @api.depends('quantity', 'purchase_order_line_ids.order_id.state', 'purchase_order_line_ids.product_qty')
    def _compute_ordered_quantity(self):
        for line in self:
            total_ordered = 0.0
            confirmed_po_lines = line.purchase_order_line_ids.filtered(
                lambda po_line: po_line.order_id.state in ('purchase', 'done')
            )


            if confirmed_po_lines:
                total_ordered = sum(confirmed_po_lines.mapped('product_qty'))

            line.quantity_ordered = total_ordered
            line.quantity_remaining = line.quantity - total_ordered

    @api.depends('quantity', 'cost_price')
    def _compute_total(self):
        for line in self:
            line.total = line.quantity * line.cost_price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.cost_price = line.product_id.standard_price
                line.description = line.product_id.name
            else:
                line.cost_price = 0.0
                line.description = ''

