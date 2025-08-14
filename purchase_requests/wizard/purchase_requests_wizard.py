# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PurchaseRequestsWizard(models.TransientModel):
    _name = 'purchase.requests.reject.wizard'
    _description = 'Purchase Requests Reject Wizard'
    #
    # # Reference to the purchase request (readonly in the wizard)
    # request_id = fields.Many2one('purchase.requests', string='Request Name', readonly=True)

    # Text field for entering the rejection reason
    rejection_reason = fields.Text(string='Rejection Reason', required=True)

    # Method to reject the request and set the rejection reason
    def action_reject_request(self):
        self.ensure_one()
        request = self.env['purchase.requests'].browse(self._context.get('active_id'))
        # Ensure there is a request selected
        if not request:
            raise ValidationError(_("No request selected for rejection."))

        request.state = 'reject'

        # Update the request state and rejection reason

        request.rejection_reason = self.rejection_reason

        # Optionally close the wizard window
        return {'type': 'ir.actions.act_window_close'}
