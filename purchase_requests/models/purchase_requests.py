from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class PurchaseRequests(models.Model):
    _name = 'purchase.requests'
    _description = 'purchase_requests'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'request_name'

    # Basic Information Fields
    request_name = fields.Char(string='Request Name', readonly=1, default="New Request")
    request_by = fields.Many2one(
        'res.users', string='Requested By', required=True,
        default=lambda self: self.env.user)
    start_date = fields.Date(string='Start Date', default=fields.Date.context_today)
    end_date = fields.Date(string='End Date')
    rejection_reason = fields.Text(string='Rejection Reason')
    notes = fields.Text(string='Notes')

    order_line = fields.One2many(
        'purchase.requests.line', 'request_id', string='Order Lines')
    total = fields.Float(string='Total', compute='_compute_total', )
    total_price = fields.Monetary(string="Total", compute="_compute_total_price", )
    price_tax = fields.Monetary(string="Tax", compute="_compute_total_price", )

    # Computed Total Price
    price_subtotal = fields.Float(string='Subtotal', compute='_compute_total_price', )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # Workflow state field
    state = fields.Selection(
        [('draft', 'Draft'),
         ('to be approved', 'To Be Approved'),
         ('approve', 'Approve'),
         ('reject', 'Reject'),
         ('cancel', 'Cancel')
         ],
        string='Status',
        default='draft',
        readonly=True,
        tracking=True
    )

    purchase_order_ids = fields.One2many(
        'purchase.order',
        'purchase_request_id',
        string='Purchase Orders'
    )
    purchase_order_count = fields.Integer(
        string='Purchase Order Count',
        compute='_compute_purchase_order_count'
    )

    all_quantities_ordered = fields.Boolean(
        string="All Quantities Ordered",
        compute='_compute_all_quantities_ordered'
    )

    def _compute_all_quantities_ordered(self):
        for request in self:
            request.all_quantities_ordered = all(
                line.quantity_remaining <= 0 for line in request.order_line
            )


    def _compute_purchase_order_count(self):
        for request in self:
            request.purchase_order_count = len(request.purchase_order_ids)

    def action_view_purchase_orders(self):
        self.ensure_one()
        return {
            'name': 'Related Purchase Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('purchase_request_id', '=', self.id)],
        }

    @api.model
    def create(self, vals):
        # Automatically generate request name if not provided
        if 'request_name' not in vals or not vals['request_name']:
            vals['request_name'] = self.env['ir.sequence'].next_by_code('purchase.requests') or 'New Request'
        return super(PurchaseRequests, self).create(vals)

    # Constraint: End date should not be before start date
    @api.constrains('end_date')
    def _check_end_date(self):
        for request in self:
            if request.end_date and request.end_date < request.start_date:
                raise UserError("End date cannot be earlier than start date.")

    # Compute total price from line totals
    @api.depends('order_line.total')
    def _compute_total(self):
        for rec in self:
            rec.total = sum(line.total for line in rec.order_line)

    @api.depends('price_subtotal', 'order_line.tax', 'order_line.total')
    def _compute_total_price(self):
        for rec in self:
            rec.price_subtotal = sum(line.total for line in rec.order_line)

            total_tax = 0.0
            for line in rec.order_line:
                if line.tax:
                    taxes = line.tax.compute_all(
                        line.cost_price,
                        currency=rec.currency_id,
                        quantity=line.quantity
                    )['taxes']
                    total_tax += sum(t['amount'] for t in taxes)

            rec.price_tax = total_tax
            rec.total_price = rec.price_subtotal + rec.price_tax

    # Move to "To Be Approved" state
    def action_submit(self):
        self.state = 'to be approved'

    # Approve the request and send email to purchase managers
    def action_approve(self):
        self.ensure_one()

        if not self.order_line:
            raise UserError("You must add at least one product before approval.")

        for line in self.order_line:
            if not line.product_id:
                raise UserError("All lines must have a product selected before approval.")
            if line.quantity <= 0:
                raise UserError(f"Product '{line.product_id.display_name}' has quantity zero or less.")

        self.state = 'approve'
        purchase_manger_group = self.env.ref('purchase.group_purchase_manager')
        users = purchase_manger_group.users
        subject = f"Purchase Request ({self.request_name}) Approved"
        body = f"<p>The purchase request <strong>{self.request_name}</strong> has been approved.</p>"
        for user in users:
            if user.partner_id.email:
                self.env['mail.mail'].create({
                    'subject': subject,
                    'body_html': body,
                    'email_to': user.partner_id.email,
                }).send()

    # Reset to draft state
    def action_reset(self):
        self.state = 'draft'

    # Cancel the request
    def action_cancel(self):
        self.state = 'cancel'

    # Trigger rejection wizard
    def action_reject(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Request',
            'res_model': 'purchase.requests.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_request_id': self.id,
            }
        }

    def action_approve_multi(self):
        for rec in self:
            if rec.state in ['draft', 'to be approved']:
                rec.state = 'approve'
            else:
                raise UserError(('You can only approve a request in draft or to be approved state.'))

    def action_create_po(self):
        self.ensure_one()

        po_vals = {
            'partner_id': self.request_by.id,
            'purchase_request_id': self.id,
            'date_order': fields.Datetime.now(),
        }

        po_lines_vals = []
        for line in self.order_line:
            if line.quantity_remaining > 0:
                line_vals = {
                    'product_id': line.product_id.id,
                    'name': line.description,
                    'product_qty': line.quantity_remaining,
                    'price_unit': line.cost_price,
                    'date_planned': fields.Date.today(),
                    'product_uom': line.product_id.uom_po_id.id,
                    'purchase_request_line_id': line.id,
                }
                po_lines_vals.append((0, 0, line_vals))

        if not po_lines_vals:
            raise models.ValidationError("No valid lines to create a purchase order.")

        po_vals['order_line'] = po_lines_vals

        new_po = self.env['purchase.order'].create(po_vals)

        return {
            'name': ('New Purchase Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': new_po.id,
            'view_mode': 'form',
            'target': 'current',
        }
