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
        act_window_id = self.env.ref('insurance_management.act_analytic_history_request')
        fields_read = ['name', 'res_model', 'search_view_id', 'view_type', 'src_model', 'type', 'views', 'view_id', 'view_mode', 'target', 'context', 'domain']
        res = act_window_id.read(fields_read)[0]
        return res
