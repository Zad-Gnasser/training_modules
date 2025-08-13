import io
from odoo import http
from odoo.http import request
import xlsxwriter


class SaleOrderExcelReport(http.Controller):
    @http.route('/report/sale_order/excel', type='http', auth='user', methods=['GET'], csrf=False)
    def generate_detailed_sale_order_report(self, ids=None, **kwargs):

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Sale Order Dashboard")

        worksheet.hide_gridlines(2)
        worksheet.set_zoom(95)

        title_format = workbook.add_format(
            {'bold': True, 'font_size': 24, 'align': 'center', 'valign': 'vcenter', 'font_color': '#FFFFFF',
             'bg_color': '#4472C4', 'border': 2})

        info_header_format = workbook.add_format(
            {'bold': True, 'font_size': 14, 'bg_color': '#DDEBF7', 'border': 1, 'align': 'center'})
        info_label_format = workbook.add_format({'bold': True, 'align': 'right', 'border': 1, 'bg_color': '#F2F2F2'})
        info_data_format = workbook.add_format({'align': 'left', 'border': 1})
        info_address_format = workbook.add_format({'align': 'left', 'valign': 'top', 'border': 1, 'text_wrap': True})

        table_header_format = workbook.add_format(
            {'bold': True, 'bg_color': '#8EA9DB', 'font_color': '#FFFFFF', 'border': 1, 'align': 'center',
             'valign': 'vcenter' , 'font_size': 13  })
        table_data_format = workbook.add_format({'border': 1})
        table_money_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})

        totals_label_format = workbook.add_format({'bold': True, 'align': 'right', 'bg_color': '#F2F2F2', 'border': 1})
        totals_value_format = workbook.add_format(
            {'bold': True, 'num_format': '#,##0.00', 'bg_color': '#DDEBF7', 'border': 1})

        if not ids:
            return request.make_response("No ID", [('Content-Type', 'text/plain')])
        order = request.env['sale.order'].browse(int(ids.split(',')[0]))


        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:C', 18)
        worksheet.set_column('D:D', 5)
        worksheet.set_column('E:F', 18)
        worksheet.set_column('G:G', 5)
        worksheet.set_row(1, 40)

        worksheet.merge_range('B2:G2', f"Sale Order: {order.name}", title_format)

        worksheet.merge_range('B4:C4', "Order Information", info_header_format)
        worksheet.write('B5', "Order Date:", info_label_format)
        worksheet.write('C5', order.date_order.strftime('%Y-%m-%d') if order.date_order else '', info_data_format)
        worksheet.write('B6', "Salesperson:", info_label_format)
        worksheet.write('C6', order.user_id.name or '', info_data_format)

        worksheet.merge_range('E4:G4', "Customer Details", info_header_format)
        worksheet.write('E5', "Customer:", info_label_format)
        worksheet.merge_range('F5:G5', order.partner_id.name or '', info_data_format)
        worksheet.write('E6', "Address:", info_label_format)
        shipping_address = order.partner_shipping_id._display_address(without_company=True).strip()
        worksheet.set_row(5, 45)
        worksheet.merge_range('F6:G6', shipping_address, info_address_format)


        row = 9
        worksheet.set_row(row, 25)
        headers = ["Product", "Description", "Quantity", "Unit Price", "Taxes", "Subtotal"]
        worksheet.write_row(f'B{row + 1}', headers, table_header_format)
        worksheet.set_column('B:C', 35)
        worksheet.set_column('D:F', 15)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 22)
        row += 1

        for line in order.order_line:
            worksheet.set_row(row, 20)
            worksheet.write(row, 1, line.product_id.name, table_data_format)
            worksheet.write(row, 2, line.name, table_data_format)
            worksheet.write(row, 3, line.product_uom_qty, table_money_format)
            worksheet.write(row, 4, line.price_unit, table_money_format)
            worksheet.write(row, 5, ', '.join(tax.name for tax in line.tax_id), table_data_format)
            worksheet.write(row, 6, line.price_subtotal, table_money_format)
            row += 1

        row += 1
        worksheet.write(row, 5, "Untaxed Amount:", totals_label_format)
        worksheet.write(row, 6, order.amount_untaxed, totals_value_format)
        row += 1
        worksheet.write(row, 5, "Taxes:", totals_label_format)
        worksheet.write(row, 6, order.amount_tax, totals_value_format)
        row += 1
        worksheet.write(row, 5, "Total:", totals_label_format)
        worksheet.write(row, 6, order.amount_total, totals_value_format)

        workbook.close()
        output.seek(0)
        filename = f"SO_{order.name}_Report.xlsx"
        response = request.make_response(
            output.getvalue(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename="{filename}"')
            ]
        )
        return response