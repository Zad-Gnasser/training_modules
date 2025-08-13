from collections import defaultdict

from odoo import models, api
from odoo import fields, models


class SaleOrder(models.Model):
    """
    Adds a custom debug button to the sale.order model.
    """
    _inherit = 'sale.order'

    def action_print_debug_values(self):

        self.ensure_one()

        if not self.order_line:
            print("No order lines to process.")
            return

        # Loop through each line associated with this sale order
        for line in self.order_line:
            # Call the preparation method from the line
            procurement_values = line._prepare_procurement_values()

            # Print the results for this specific line

            print(procurement_values)

        return True  # Return True to indicate success

    def execl_report_button(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/sale_order/excel?ids=%s' % self.id,
            'target': 'new',
        }

class SaleOrderLineInherits(models.Model):
    _inherit = 'sale.order.line'

    dimension = fields.Char(
        string='Dimension'
    )

    @api.onchange('product_id')
    def _onchange_product_id_set_dimension(self):
        for rec in self:
            if rec.product_id:
                rec.dimension = rec.product_id.dimension
            else:
                rec.dimension = ""

    def _prepare_procurement_values(self, group_id=False):
        values = super()._prepare_procurement_values(group_id)
        values['dimension'] = self.dimension
        return values

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        move = self.move_ids.filtered(lambda m: m.state != 'cancel')[:1]
        if move and move.dimension:
            res['dimension'] = move.dimension
        else:
            res['dimension'] = self.dimension
        return res



class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        fields = super()._get_custom_move_fields()
        fields.append('dimension')
        return fields

