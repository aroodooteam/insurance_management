# -*- coding: utf-8 -*-
from openerp import api, exceptions, fields, models, _
from datetime import datetime as dt
import logging
logger = logging.getLogger(__name__)



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    final_customer_id = fields.Many2one(comodel_name='res.partner', string='Final Customer')
    agency_id = fields.Many2one(comodel_name='base.agency', string='Agency')

    @api.v7
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        res = super(SaleOrder, self)._prepare_invoice(cr, uid, order, lines, context)
        logger.info('type agence = %s' % order.agency_id.agency_type)
        acc_obj = self.pool['account.account']
        acc_id = acc_obj.search(cr, uid, [('code','=','411100')], context)
        logger.info('acc_id = %s' % acc_id)
        if order.amount_total < 0:
            res['type'] = 'out_refund'
        new_journal = order._get_user_journal(res['type'])[0]
        if new_journal:
            new_journal = new_journal.id
            res['journal_id'] = new_journal
        if order.project_id:
            res['history_id'] = order.project_id.id
            res['analytic_id'] = order.project_id.parent_id.id
            res['pol_numpol'] = order.project_id.parent_id.name
            res['prm_datedeb'] = order.project_id.date_start
            res['prm_datefin'] = order.project_id.date
            res['date_invoice'] = dt.now()
        if order.agency_id.agency_type == 'GRA':
            res['final_customer_id'] = res.get('partner_id')
            res['partner_id'] = order.agency_id.partner_id.id
            res['account_id'] = acc_id[0]
        return res

    @api.one
    def _get_user_journal(self, invoice_type='out_invoice'):
        journal_obj = self.env['account.journal']
        user_obj = self.env['res.users']
        domain = [('type', '=', 'sale')]
        jrn_type = 'P'
        if invoice_type == 'out_refund':
            jrn_type = 'V'
            domain = [('type', '=', 'sale_refund')]
        insurance_type = self.project_id.branch_id.type
        user = self._uid
        user_id = user_obj.browse(user)
        agency_id = user_id.agency_id
        if not agency_id and not self.agency_id:
            raise Warning(_('Please contact your Administrator to set your agency'))
        else:
            agency_id = self.agency_id
        domain.append(('agency_id', '=', agency_id.id))
        if insurance_type == 'N':
            journal_code = '%sN%s' % (jrn_type,agency_id.code)
            domain.append(('code', '=', journal_code))
        else:
            journal_code = '%sV%s' % (jrn_type,agency_id.code)
            domain.append(('code', '=', journal_code))
        journal_id = journal_obj.search(domain)
        logger.info('=== journal_id = %s => %s' % (journal_id, journal_id.name))
        return journal_id
