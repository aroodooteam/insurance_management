# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models, _
import logging
logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # history_id = fields.Many2one(comodel_name='analytic.history', string='History')
    # analytic_id = fields.Many2one(comodel_name='account.analytic.account', string='Contract', related='history_id.analytic_id')
    history_id = fields.Many2one(comodel_name='account.analytic.account', string='History')
    analytic_id = fields.Many2one(comodel_name='account.analytic.account', string='Contract', related='history_id.parent_id')

    @api.model
    def create(self, vals):
        logger.info('\n *-*-* ctx = %s' % self._context)
        history_obj = self.env['account.analytic.account']
        res = super(AccountInvoice, self).create(vals)
        history_id = self._context.get('default_history_id', False)
        if history_id:
            history_id = history_obj.browse(history_id)
            history_id.write({'invoice_id': res.id})
            res.button_reset_taxes()
        return res

    @api.multi
    def onchange_company_id(self, company_id, part_id, type, invoice_line, currency_id):
        res = super(AccountInvoice, self).onchange_company_id(company_id, part_id, type, invoice_line, currency_id)
        values = res.get('value')
        journal_id = self._context.get('default_journal_id', False)
        if journal_id and values.get('journal_id'):
            res['value'] = {'journal_id': journal_id}
        return res
