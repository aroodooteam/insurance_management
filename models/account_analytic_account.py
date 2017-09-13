# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models, _
from openerp.addons.decimal_precision import decimal_precision as dp
import logging
logger = logging.getLogger(__name__)


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    # TODO
    @api.multi
    def _get_warranty_invoiced(self):
        """ Compute value of field warranty_invoiced """
        for aaa in self:
            aaa.warranty_invoiced = 0.0

    # TODO
    @api.multi
    def _get_warranty_to_invoice(self):
        """ Compute value of field warranty_to_invoice """
        for aaa in self:
            aaa.warranty_to_invoice = 0.0

    # TODO
    @api.multi
    def _get_remain_warranty(self):
        """ Compute value of field remaining_warranty """
        for aaa in self:
            aaa.remaining_warranty = 0.0

    # TODO
    @api.multi
    def _get_wa_invoiced(self):
        """ Compute value of field warranty_invoiced """
        for aaa in self:
            aaa.warranty_invoiced = 0.0

    branch_id = fields.Many2one(
        comodel_name='insurance.branch', string='Branch')
    ins_product_id = fields.Many2one(
        comodel_name='insurance.product', string='Inusrance Product',
        required=True, domain="[('branch_id', '=', branch_id)]")
    on_warranty = fields.Boolean(string='On Warranty')
    warranty_invoiced = fields.Float(
        string='Invoiced', digits_compute=dp.get_precision('Account'),
        compute='_get_warranty_invoiced')
    warranty_to_invoice = fields.Float(
        string='To invoice', digits_compute=dp.get_precision('Account'),
        compute='_get_warranty_to_invoice')
    remaining_warranty = fields.Float(
        string='Remaining', digits_compute=dp.get_precision('Account'),
        compute='_get_remain_warranty')
    est_warranty = fields.Float(
        string='Estimation', digits_compute=dp.get_precision('Account'))
    wa_invoiced = fields.Float(string='Warranty Invoiced Amount', digits_compute=dp.get_precision('Account'), compute='_get_wa_invoiced')

    # def open_hr_expense(self, cr, uid, ids, context=None):
    @api.multi
    def open_analytic_history(self):
        # mod_obj = self.pool.get('ir.model.data')
        # act_obj = self.pool.get('ir.actions.act_window')

        # dummy, act_window_id = mod_obj.get_object_reference(cr, uid, 'hr_expense', 'expense_all')
        # result = act_obj.read(cr, uid, [act_window_id], context=context)[0]

        # line_ids = self.pool.get('hr.expense.line').search(cr,uid,[('analytic_account', 'in', ids)])
        # result['domain'] = [('line_ids', 'in', line_ids)]
        # names = [account.name for account in self.browse(cr, uid, ids, context=context)]
        # result['name'] = _('Expenses of %s') % ','.join(names)
        # result['context'] = {'analytic_account': ids[0]}
        # result['view_type'] = 'form'
        # return result
        return True
