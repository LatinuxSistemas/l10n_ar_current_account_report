# -*- coding: latin1 -*-

import base64
import codecs
import csv
import tempfile
import time

import netsvc
from openerp.osv import fields, orm, osv
from openerp.tools.translate import _


class current_account_report(orm.TransientModel):
    _name = "wizard.current.account.report"
    _description = "Create Current Account Reports"

    _columns = {
        'data': fields.binary('Output file', readonly=True),
        #'partner_ids': fields.many2many('res.partner', 'partner_wiz_cc_rel', 'wiz_id',
        #                                'partner_id', 'Partners'),
        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
        'state': fields.selection([('choose', 'Choose'), ('done', 'Done')], string="State"),
    }

    _defaults = {
        'state': 'choose',
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None,
                        toolbar=False):
        res = super(current_account_report, self).fields_view_get(cr, uid, view_id, view_type,
                                                                  context, toolbar)
        sense = context.get("sense", False)
        if sense:
            filter_dict = {
                "out": [("customer", "=", True), _("Customer")],
                "in": [("supplier", "=", True), _("Supplier")],
            }
            domain = filter_dict[sense]
            string = domain.pop(1)
            partner_obj = self.pool["res.partner"]
            partner_ids = partner_obj.search(cr, uid, domain)
            partners = partner_obj.name_get(cr, uid, partner_ids)
            res["fields"]["partner_id"].update({"selection": partners, "string": string})
        return res

    #Facturas de Cliente
    def create_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        logger = netsvc.Logger()
        sense = context.get("sense", "%")
        wizard = self.browse(cr, uid, ids)[0]
        invoice_obj = self.pool.get('account.invoice')
        partner_obj = self.pool.get('res.partner')

        #sense means customer if out else supplier
        inv_ids = invoice_obj.search(cr, uid, [
            ('partner_id', '=', wizard.partner_id.id),
            ('type', 'like', "%s%%" % sense),
        ], order="date_invoice", context=context)

        keys = ["date", "number", "desc", "source_doc", "amount_untaxed", "amount_total", "state"]
        row_header = {
            "date": _("Invoice Date"),
            "state": _("Invoice Number"),
            "desc": _("Description"),
            "amount_untaxed": _("Amount untaxed ($)"),
            "amount_total": _("Total ($)"),
            "number": _("State"),
            "source_doc": _("Source Document"),
        }
        row_header = ';'.join([row_header[l] for l in keys])+'\n'
        rows = [row_header]

        report_file = tempfile.mkstemp(suffix='.ccreport')[1]
        with codecs.open(report_file, mode="wb", encoding="latin-1") as csvfile:
            header = _("Current Account Report for %s") % wizard.partner_id.name,
            today = time.strftime(_("%b %d, %Y")),
            csvfile.write("%s;%s\n\n" % (header[0], today[0]))
            invoices = invoice_obj.browse(cr, uid, inv_ids)
            for invoice in invoices:
                # fecha factura
                date = ''
                if invoice.date_invoice:
                    date = time.strftime("%d/%m/%Y", time.strptime(invoice.date_invoice,
                                                                   '%Y-%m-%d'))

                # posicion fiscal
                pf = ''
                if invoice.pos_ar_id:
                    pf = invoice.pos_ar_id.name
                elif invoice.denomination_id:
                    pf = invoice.denomination_id.name

                #state
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
                row_data = {
                    "date": date,
                    "state": state,
                    "number": pf + ' - ' + (invoice.number or ''),
                    "amount_total": str(invoice.amount_total),
                    "amount_untaxed": str(invoice.amount_untaxed),
                    "desc": invoice.comment or invoice.name or '',
                    "source_doc": invoice.origin or '',
                }
                row_data = ';'.join([row_data[l] for l in keys])+'\n'
                print row_data
                rows.append(row_data)
            csvfile.writelines(rows)

        f = open(report_file)
        return self.write(cr, uid, ids, {
            'state': 'done',
            'data': f.read(),
            'name': 'reporte_cuenta_corriente.csv'
        }, context=context)
