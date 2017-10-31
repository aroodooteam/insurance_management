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

    @api.multi
    def _get_last_history(self):
        history_obj = self.env['analytic.history']
        # history_ids = history_obj.search([('analytic_id', 'in', self)])
        dom = [('is_last_situation', '=', True), ('analytic_id', 'in', self.ids)]
        history_ids = history_obj.search(dom)
        for history_id in history_ids:
            history_id.analytic_id.history_stage = history_id.stage_id.id

    branch_id = fields.Many2one(
        comodel_name='insurance.branch', string='Branch')
    ins_product_id = fields.Many2one(
        comodel_name='insurance.product', string='Inusrance Product',
        required=False, domain="[('branch_id', '=', branch_id)]")

    fraction_ids = fields.Many2many(
        comodel_name='insurance.fraction', string='Fractions',
        related='ins_product_id.fraction_ids')

    fraction_id = fields.Many2one(
        comodel_name='insurance.fraction', string='Fraction',
        domain="[('id', 'in', fraction_ids[0][2])]")

    is_insurance = fields.Boolean(string='Insurance contract', help='Check if it is an insurance contract')
    risk_line_ids = fields.One2many(
        comodel_name='analytic.risk.line',
        inverse_name='analytic_id', string='Risks Type')
    insured_id = fields.Many2one(comodel_name='res.partner', string='Insured')
    history_count = fields.Integer(
        compute='get_history_count', string='History count')
    # End of new process with account_analytic_account

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
    state = fields.Selection(selection_add=[('suspend', 'Suspend')])
    history_stage = fields.Many2one(
        comodel_name='analytic.history.stage', string='History Stage',
        help='Stage of last history', compute='_get_last_history')

    # def open_hr_expense(self, cr, uid, ids, context=None):
    @api.multi
    def open_analytic_history(self):
        act_window_id = self.env.ref('insurance_management.act_analytic_history_request')
        res = act_window_id.read()[0]
        res['domain'] = [('analytic_id', '=', self.id)]
        res['context'] = {'default_analytic_id': self.id}
        return res

    @api.multi
    def open_analytic_history_wiz(self):
        res = {
            'name': 'History',
            'type': 'ir.actions.act_window',
            'res_model': 'analytic.history.wiz',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('insurance_management.view_analytic_history_wiz_form').id,
            'target': 'new',
            'context': {}
        }
        return res

    @api.multi
    def get_history_count(self):
        history_obj = self.env['analytic.history']
        for analytic in self:
            history_count = history_obj.search_count([('analytic_id', '=', analytic.id)])
            analytic.history_count = history_count

    @api.multi
    def get_current_version(self):
        res = {}
        history_obj = self.env['analytic.history']
        domain = [('is_last_situation', '=', True), ('analytic_id', '=', self.id)]
        history_id = history_obj.search(domain)
        if not history_id:
            raise exceptions.Warning(_('Sorry, there is no recent version for this contract'))
        view_id = self.env.ref('insurance_management.view_aro_amendment_line_form').id
        res.update({
                'type': 'ir.actions.act_window',
                'name': _('Last Version'),
                'res_model': 'analytic.history',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': [view_id],
                'res_id': history_id.id,
                'target': 'current',
            })
        return res

    @api.multi
    def set_suspend(self):
        self.ensure_one()
        self.write({'state': 'suspend'})
