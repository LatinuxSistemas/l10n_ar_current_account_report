# -*- coding: latin1 -*-

import base64
import codecs
import tempfile
import time

from openerp import models, api, fields
from openerp.tools.translate import _


class current_account_report(models.TransientModel):
    _name = "wizard.current.account.report"
    _description = "Create Current Account Reports"

    _columns = {
        'filename': fields.char('File Name', size=32),
        'data': fields.binary('Output file', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
        'state': fields.selection([('choose', 'Choose'), ('done', 'Done')], string="State"),
    }

    _defaults = {
        'state': 'choose',
    }

    @api.model
    @api.noguess
    def fields_view_get(self, view_id=False, view_type='form', toolbar=False, submenu=False):
        res = super(current_account_report, self).fields_view_get(view_id, view_type,
                                                                  toolbar=toolbar, submenu=submenu)
        sense = self.env.context.get("sense", False)
        if sense:
            filter_dict = {
                "out": [("customer", "=", True), _("Customer")],
                "in": [("supplier", "=", True), _("Supplier")],
            }
            domain = filter_dict[sense]
            string = domain.pop(1)
            partner_obj = self.pool["res.partner"]
            partner_ids = partner_obj.search(domain)
            partners = partner_obj.name_get(partner_ids)
            res["fields"]["partner_id"].update({"selection": partners, "string": string})
        return res

    #Facturas de Cliente
    def create_report(self):
        print self
        sense = self.env.context.get("sense", "%")
        invoice_obj = self.env['account.invoice']

        #sense means customer if out else supplier
        inv_ids = invoice_obj.search([
            ('partner_id', '=', self.partner_id.id),
            ('type', 'like', "%s%%" % sense),
        ], order="date_invoice")

        line_tmp = u'{};{};{};{};{};{};{}\n'
        row_header = (_("Invoice Date"), _("Invoice Number"), _("Description"),
                      _("Source Document"), _("Amount untaxed ($)"), _("Total ($)"), _("State"))
        rows = [line_tmp.format(*row_header)]

        report_file = tempfile.mkstemp(suffix='.ccreport')[1]
        with codecs.open(report_file, mode="w", encoding="latin-1") as csvfile:
            header = _("Current Account Report for %s") % self.partner_id.name,
            today = time.strftime(_("%b %d, %Y")),
            csvfile.write("%s;%s\n\n" % (header[0], today[0]))
            invoices = invoice_obj.browse(inv_ids)
            for invoice in invoices:
                number = "%s %s" % (invoice.denomination_id.name or '', invoice.internal_number)
                date = ''
                if invoice.date_invoice:
                    date = time.strftime("%d/%m/%Y", time.strptime(invoice.date_invoice,
                                                                   '%Y-%m-%d'))

                if invoice['state'] == 'draft':
                    state = 'Borrador'
                elif invoice['state'] == 'paid':
                    state = 'Pagada'
                elif invoice['state'] == 'open':
                    state = 'Abierta'
                elif invoice['state'] in ('proforma', 'proforma2'):
                    state = 'Proforma'
                elif invoice['state'] == 'cancel':
                    state = 'Cancelada'
                else:
                    state = ''

                ##### LINEA DE REPORTE #####
                total = str(invoice.amount_total)
                untaxed = str(invoice.amount_untaxed)
                desc = invoice.comment or invoice.name or ''
                origin = invoice.origin or '',
                row_data = line_tmp.format(date, number, desc, origin, untaxed, total, state)
                rows.append(row_data)
            csvfile.writelines(rows)

        f = open(report_file)
        data = base64.encodestring(f.read())
        f.close()

        self.write({'state': 'done', 'data': data, 'filename': _('cc_report.csv')})
        view = self.env.ref('view_report_cc_wizard')
        return {
            'name': 'CC',
            'res_model': 'wizard.current.account.report',
            'type': 'ir.actions.act_window',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': self.env.context,
        }
