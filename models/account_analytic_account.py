# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models, _
from openerp.addons.decimal_precision import decimal_precision as dp
from datetime import datetime as dt
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import logging
logger = logging.getLogger(__name__)


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    @api.multi
    @api.depends('date_start', 'date')
    def _get_nb_of_days(self):
        for rec in self:
            if rec.date_start and rec.date:
                date_end = dt.strptime(rec.date, '%Y-%m-%d')
                date_start= dt.strptime(rec.date_start, '%Y-%m-%d')
                delta = date_end - date_start
                rec.nb_of_days = delta.days

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
    is_recurrent = fields.Boolean(string=u'Recurrent (Terme)', help='Check if it is an recurrent contract')
    # risk_line_ids = fields.One2many(
    #     comodel_name='analytic.risk.line',
    #     inverse_name='analytic_id', string='Risks Type')
    insured_id = fields.Many2one(comodel_name='res.partner', string='Insured')
    history_count = fields.Integer(
        compute='get_history_count', string='History count')
    invoice_count = fields.Integer(
        compute='get_invoice_count', string='History count')
    analytic_line_count = fields.Integer(
        compute='getAnalyticLineCount', string='Analytic Line count')
    # End of new process with account_analytic_account

    on_warranty = fields.Boolean(string='On Warranty')
    state = fields.Selection(selection_add=[('suspend', 'Suspend')])
    history_stage = fields.Many2one(
        comodel_name='analytic.history.stage', string='History Stage',
        help='Stage of last history', compute='_get_last_history')
    property_account_position = fields.Many2one(
        comodel_name='account.fiscal.position', string='Fiscal Position')
    pol_ident = fields.Char(string='Police ID')
    next_sequence = fields.Integer(string='Next version Sequence')
    risk_line_ids = fields.One2many(comodel_name='analytic_history.risk.line', inverse_name='analytic_id', string='Contract')
    description_ids = fields.One2many(comodel_name='risk.description.line', compute='getListDescription', string='Description')
    history_ids = fields.One2many(comodel_name='analytic.history', inverse_name='analytic_id', string='History')
    warranty_ids = fields.One2many(comodel_name='risk.warranty.line', compute='getListWarranty', string='Warranty')

    agency_id = fields.Many2one(comodel_name='base.agency', string='Agency')
    is_last_situation = fields.Boolean(
        string='Is the last situation', default=False)
    capital = fields.Float(
        string='Capital', digit_compute=dp.get_precision('account'))
    eml = fields.Float(
        string='Expected maximum loss',
        digit_compute=dp.get_precision('account'))
    ver_parent_id = fields.Many2one(
        comodel_name='account.analytic.account', string='Parent Version',
        help='Inherited Amendment')
    force_acs = fields.Boolean(string='Force Accessories', help='Use the amount you define instead of original amoun from setting')
    accessories = fields.Float(string='Accessories')
    invoice_id = fields.Many2one(
        'account.invoice', string='Invoice', readonly=True)
    commission_invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Commission Invoice', readonly=True)
    comment = fields.Text(string='Comment', help='Some of your note')
    nb_of_days = fields.Integer(compute='_get_nb_of_days', string='Number of days', help='Number of days between start and end date')
    # Temporary field
    ver_ident = fields.Char(string='Ver Ident')

    @api.one
    @api.depends('history_ids')
    def getListDescription(self):
        hist_obj = self.env['analytic.history']
        hist_ids = hist_obj.search([('analytic_id', '=', self.id),('is_last_situation','=', True)], limit=1)
        risk_dict = []
        for risk_id in hist_ids.risk_line_ids:
            for description in risk_id.risk_description_ids:
                risk_dict.append(description.id)
        self.description_ids = risk_dict

    @api.one
    @api.depends('history_ids')
    def getListWarranty(self):
        hist_obj = self.env['analytic.history']
        hist_ids = hist_obj.search([('analytic_id', '=', self.id),('is_last_situation','=', True)], limit=1)
        warranty_list = []
        for risk_id in hist_ids.risk_line_ids:
            for warranty in risk_id.warranty_line_ids:
                warranty_list.append(warranty.id)
        self.warranty_ids = warranty_list


    @api.onchange('ins_product_id')
    def onchange_ins_product_id(self):
        fraction_ids = self.ins_product_id.fraction_ids
        logger.info('fraction_ids = %s' % fraction_ids)
        if fraction_ids:
            self.fraction_id = fraction_ids.ids[0]

    # @api.onchange('partner_id')
    # def on_change_partner_id(self):
    #     res = super(AccountAnalyticAccount, self).on_change_partner_id(self.partner_id.id, self.name)
    #     logger.info('=== res = %s' % res)
    #     values = res.get('value', {})
    #     if values.get('name'):
    #         self.name = values.get('name')
    #     self.pricelist_id = values.get('pricelist_id')
    #     if values.get('manager_id', False):
    #         self.manager_id = values.get('manager_id')
    #     self.property_account_position = self.partner_id.property_account_position.id
    #     self.insured_id = self.partner_id.id

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
        ctx = self._context.copy()
        ctx.update(property_account_position=self.property_account_position.id)
        logger.info('ctx org = %s' % ctx)
        if not self.branch_id:
            return False
        if self.branch_id.code == 'ASSPERS':
            ctx.update(insurance_person=True)
        res = {
            'name': 'History',
            'type': 'ir.actions.act_window',
            'res_model': 'analytic.history.wiz',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('insurance_management.view_analytic_history_wiz_form').id,
            'target': 'new',
            'context': ctx
        }
        return res

    @api.one
    def get_history_count(self):
        history_obj = self.env['analytic.history']
        history_count = history_obj.search_count([('analytic_id', '=', self.id)])
        self.history_count = history_count
        # part 2
        self.history_count = self.search_count([('parent_id', '=', self.id)])

    @api.one
    def get_invoice_count(self):
        inv_ids = self.history_ids.mapped('invoice_id')
        self.invoice_count = len(inv_ids)

    @api.one
    def getAnalyticLineCount(self):
        self.analytic_line_count = len(self.history_ids.mapped('analytic_line_ids'))

    @api.multi
    def getInvoices(self):
        inv_ids = self.history_ids.mapped('invoice_id')
        res = {
            'name': 'Invoices',
            'type': 'ir.actions.act_window',
            'res_model': 'account.invoice',
            'src_model': 'account.analytic.account',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', tuple(inv_ids.ids))],
        }
        return res

    @api.multi
    def getAnalyticLine(self):
        analytic_line_ids = self.history_ids.mapped('analytic_line_ids')
        res = {
            'name': 'Analytic Lines',
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.line',
            'src_model': 'account.analytic.account',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', tuple(analytic_line_ids.ids))],
        }
        return res

    @api.multi
    def get_current_version(self):
        self.ensure_one()
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

    @api.multi
    def set_close_insurance(self):
        self.write({'state': 'close'})

    @api.multi
    def open_history_list_old(self):
        ctx = self._context.copy()
        res = {
            'name': 'History',
            'type': 'ir.actions.act_window',
            'res_model': 'analytic.history',
            'src_model': 'account.analytic.account',
            'context': ctx,
            'view_type': 'form',
            'view_mode': 'tree,form',
            # 'view_id': self.env.ref('insurance_management.view_analytic_history_tree').id,
            'domain': [('analytic_id', '=', self.ids[0])],
            'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}},
        }
        if self.branch_id.code == 'ASSPERS':
            ctx.update({'insurance_person': True})
            res['context'] = ctx
        return res

    @api.multi
    def open_history_list(self):
        ctx = self._context.copy()
        tree_id = self.env.ref('insurance_management.view_account_analytic_account_policy_tree').id
        form_id = self.env.ref('insurance_management.view_account_analytic_account_form').id
        res = {
            'name': 'History',
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.account',
            'src_model': 'account.analytic.account',
            'nodestroy': True,
            'context': ctx,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_id, 'tree'),(form_id, 'form')],
            'domain': [('parent_id', '=', self.ids[0])],
            'flags': {
                'form': {'action_buttons': True, 'options': {'mode': 'edit'}},
                'tree': {'action_buttons': False, 'create': False, 'options': {}}
            },
        }
        if self.branch_id.code == 'ASSPERS':
            ctx.update({'insurance_person': True})
            res['context'] = ctx
        return res

    @api.multi
    def generate_invoice_for_each_version(self):
        """
        Generate invoice for each version doesn't have invoice yet
        """
        logger.info('=== Generate invoice for version')
        # logger.info('=== ids = %s' % self)
        # logger.info('=== ctx = %s' % self._context)
        history_obj = self.env['analytic.history']
        invoice_obj = self.env['account.invoice']
        history_ids = history_obj.search([('analytic_id', 'in', self.ids), ('invoice_id', '=', False)])
        # logger.info('=== history_ids = %s' % history_ids)
        for history_id in history_ids:
            vals = history_id.with_context(invoice_unedit=True).generate_invoice()
            if not vals:
                continue
            logger.info('=== history_id.id => vals = %s' % vals)
            inv_lines = vals.get('invoice_line')
            inv_lines_buf = []
            # logger.info('=== inv_lines => %s' % inv_lines)
            for inv_line in inv_lines:
                inv_line[2]['invoice_line_tax_id'] = [(6,0,inv_line[2].get('invoice_line_tax_id'))]
                inv_lines_buf.append(inv_line)
            logger.info('=== inv_lines_buf => %s' % inv_lines_buf)
            vals['invoice_line'] = inv_lines_buf
            # logger.info('=== history_id.id => vals = %s' % vals)
            inv_id = invoice_obj.create(vals)
            inv_id.button_reset_taxes()
            # logger.info('=== inv_id => %s' % inv_id)
            history_id.write({'invoice_id': inv_id.id})

    @api.multi
    def open_policy(self):
        self.write({'state': 'open'})

    @api.multi
    @api.onchange('parent_id')
    def on_change_parent(self):
        # res = super(AccountAnalyticAccount, self).on_change_parent(self._cr, self._uid, self, self.ids[0], self.parent_id.id)
        logger.info('res_onchange_par = %s' % self.parent_id)
        res = super(AccountAnalyticAccount, self).on_change_parent(self.parent_id.id)
        logger.info('res_onchange = %s' % res)
        return res
