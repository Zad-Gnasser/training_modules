from odoo import models, fields
from odoo.exceptions import UserError
from odoo.tools import float_compare


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_request_id = fields.Many2one(
        'purchase.requests',
        string='Purchase Request',
        readonly=True,
    )

    def button_confirm(self):
        for order in self:
            if order.purchase_request_id:
                for line in order.order_line:
                    if line.purchase_request_line_id:
                        pr_line = line.purchase_request_line_id

                        already_ordered_qty = pr_line.quantity_ordered
                        current_line_qty = line.product_qty

                        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

                        if float_compare(already_ordered_qty + current_line_qty, pr_line.quantity,
                                         precision_digits=precision) > 0:
                            raise UserError(
                                "Cannot confirm purchase order"
                            )

        return super(PurchaseOrder, self).button_confirm()
