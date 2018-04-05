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
        dom = [('is_last_situation', '=', True), ('parent_id', 'in', self.ids)]
        history_ids = self.search(dom)
        for history_id in history_ids:
            history_id.parent_id.history_stage = history_id.stage_id.id

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
    state = fields.Selection(selection_add=[('suspend', 'Suspend'),('amendment', 'Amendment')])
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
    stage_id = fields.Many2one(
        comodel_name='analytic.history.stage', string='Emission type',
    default=lambda self: self.env.ref('insurance_management.devis').id)
    # Temporary field
    ver_ident = fields.Char(string='Ver Ident')

    @api.one
    @api.depends('child_ids')
    def getListDescription(self):
        hist_ids = self.search([('parent_id', '=', self.id),('is_last_situation','=', True)], limit=1)
        risk_dict = []
        for risk_id in hist_ids.risk_line_ids:
            for description in risk_id.risk_description_ids:
                risk_dict.append(description.id)
        self.description_ids = risk_dict

    @api.one
    @api.depends('child_ids')
    def getListWarranty(self):
        hist_ids = self.search([('parent_id', '=', self.id),('is_last_situation','=', True)], limit=1)
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
    def _get_user_journal(self):
        """
        insurance_type: ['V', 'N']
        """
        logger.info('=== ctx = %s' % self._context)
        user_obj = self.env['res.users']
        journal_obj = self.env['account.journal']
        insurance_type = self._context.get('insurance_type', False)
        if not insurance_type:
            insurance_type = self.parent_id.branch_id.type
        logger.info('\n === insurance_type = %s' % insurance_type)
        user = self._uid
        user_id = user_obj.browse(user)
        # logger.info('\n === user_id = %s' % user_id)
        agency_id = user_id.agency_id
        if not agency_id and not self.agency_id:
            raise Warning(_('Please contact your Administrator to set your agency'))
        else:
            agency_id = self.agency_id

        domain = [('type', '=', 'sale'), ('agency_id', '=', agency_id.id)]
        if insurance_type == 'N':
            journal_code = 'PN%s' % agency_id.code
            domain.append(('code', '=', journal_code))
        logger.info('\n === domain = %s' % domain)
        journal_id = journal_obj.search(domain)
        logger.info('=== journal_id = %s => %s' % (journal_id, journal_id.name))
        return journal_id

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

    @api.multi
    def GetAccessAmount(self):
        vals = {
            'amount_to_invoice': self.parent_id.ins_product_id.amount_accessories,
            'product_id': False,
            'account_id': self.id,
            'amount': 0,
            # 'name': self.name + ' - ' + warranty_id.name,
            'journal_id': self._get_user_journal().analytic_journal_id.id,
            'date': dt.now(),
            'ref': self.stage_id.name,
            # 'general_account_id': warranty_id.warranty_id.property_account_income.id,
            'hist_id': self.id,
            'unit_amount': 1,
        }
        product_obj = self.env['product.product']
        access_tmpl_id = False
        if self.force_acs:
            vals['amount_to_invoice'] = self.accessories
        if self.parent_id.branch_id.category == 'T':
            access_tmpl_id = self.env.ref('aro_custom_v8.product_template_accessoire_terrestre_r0')
        elif self.parent_id.branch_id.category == 'M':
            access_tmpl_id = self.env.ref('aro_custom_v8.product_template_accessoire_maritime_r0')
        elif self.parent_id.branch_id.category == 'V':
            access_tmpl_id = self.env.ref('aro_custom_v8.product_template_accessoire_vie_r0')
        product_id = product_obj.search([('product_tmpl_id', '=', access_tmpl_id.id)], limit=1)
        vals['product_id'] = product_id.id
        vals['name'] = self.name + ' - ' + product_id.name
        vals['general_account_id'] = product_id.property_account_income.id
        return vals

    @api.one
    def generateAnalyticLines(self):
        aal_obj = self.env['account.analytic.line']
        warranty_obj = self.env['risk.warranty.line']
        # get all warranty in risk_line
        warranty_ids = self.risk_line_ids.mapped('warranty_line_ids')
        all_vals = []
        if self.stage_id.id == self.env.ref('insurance_management.avenant').id:
            logger.info('TEST')
            for warranty_id in warranty_ids:
                new_amount = 0
                if warranty_id.parent_id:
                    if warranty_id.parent_id.proratee_net_amount != warranty_id.proratee_net_amount:
                        new_amount = warranty_id.proratee_net_amount- warranty_id.parent_id.proratee_net_amount
                    else:
                        continue
                else:
                    new_amount = warranty_id.proratee_net_amount
                vals = {
                    'account_id': self.id,
                    'product_id': warranty_id.id,
                    'amount': 0,
                    'amount_to_invoice': new_amount,
                    'name': self.name + ' - ' + warranty_id.name,
                    'journal_id': self._get_user_journal().analytic_journal_id.id,
                    'date': dt.now(),
                    'ref': self.name + ' - ' + self.stage_id.name,
                    'general_account_id': warranty_id.warranty_id.property_account_income.id,
                    # 'history_id': self.id,
                    'hist_id': self.id,
                    'unit_amount': 1,
                }
                aal_obj.create(vals)
        else:
            # delete all analytic_line before re-generating new
            aal_ids = aal_obj.search([('hist_id','=',self.id)])
            if aal_ids:
                aal_ids.unlink()
            for warranty_id in warranty_ids:
                vals = {
                    'account_id': self.id,
                    'product_id': warranty_id.id,
                    'amount': 0,
                    'amount_to_invoice': warranty_id.proratee_net_amount,
                    'name': self.name + ' - ' + warranty_id.name,
                    'journal_id': self._get_user_journal().analytic_journal_id.id,
                    'date': dt.now(),
                    'ref': self.stage_id.name,
                    'general_account_id': warranty_id.warranty_id.property_account_income.id,
                    # 'history_id': self.id,
                    'hist_id': self.id,
                    'unit_amount': 1,
                }
                logger.info('aal_vals = %s' % vals)
                aal_obj.create(vals)
            # analytic line for accessories
            access_vals = self.GetAccessAmount()
            logger.info('acc_vals = %s' % access_vals)
            aal_obj.create(access_vals)

    # TODO
    @api.multi
    def _get_all_value(self):
        self.ensure_one()
        res = {}
        list_fields = ['name', 'type_risk_id', 'risk_warranty_tmpl_id', 'partner_id']
        om_fields = {
            'warranty_line_ids': ['name', 'warranty_id', 'history_risk_line_id', 'yearly_net_amount', 'proratee_net_amount', 'parent_id'],
            'risk_description_ids': ['name', 'code', 'value', 'parent_id']
        }
        new_risk_line = []
        # TODO
        # content of <if> should be implemented
        if not self._context.get('default', False):
            res['name'] = _('%s (copy)') % self.name or ''
            res['capital'] = self.capital
            res['eml'] = self.eml
            res['accessories'] = self.accessories
            for risk_line_id in self.risk_line_ids:
                new_risk_line.append(risk_line_id.read(list_fields))
        else:
            res['default_name'] = _('%s (copy)') % self.name or ''
            res['default_capital'] = self.capital
            res['default_eml'] = self.eml
            res['default_agency_id'] = self.agency_id.id
            res['default_accessories'] = self.accessories
            res['default_property_account_position'] = self.property_account_position.id
            for risk_line_id in self.risk_line_ids:
                l = risk_line_id.read(list_fields)[0]
                # get standard fields
                l['type_risk_id'] = l.get('type_risk_id', False)[0]
                l['partner_id'] = l.get('partner_id', False)[0] if l.get('partner_id', False) else False
                l['risk_warranty_tmpl_id'] = l.get('risk_warranty_tmpl_id', False)
                l['risk_warranty_tmpl_id'] = l.get('risk_warranty_tmpl_id')[0] if l.get('risk_warranty_tmpl_id', False) else False
                l['parent_id'] = l.get('id', False)
                del l['id']
                # get o2m fields value
                logger.info('wlids = %s' % risk_line_id.warranty_line_ids)
                om_warrantys = risk_line_id.warranty_line_ids.read(om_fields.get('warranty_line_ids'))
                warranty_list = []
                for om_warranty in om_warrantys:
                    om_warranty['parent_id'] = om_warranty.get('id', False)
                    del om_warranty['id']
                    om_warranty['warranty_id'] = om_warranty.get('warranty_id')[0] if om_warranty.get('warranty_id') else False
                    om_warranty['history_risk_line_id'] = om_warranty.get('history_risk_line_id')[0] if om_warranty.get('history_risk_line_id') else False
                    warranty_list.append((0, 0, om_warranty))
                l['warranty_line_ids'] = warranty_list
                # =====================================
                om_descs = risk_line_id.risk_description_ids.read(om_fields.get('risk_description_ids'))
                description_list = []
                for om_desc in om_descs:
                    om_desc['parent_id'] = om_desc.get('id', False)
                    del om_desc['id']
                    description_list.append((0, 0, om_desc))
                l['risk_description_ids'] = description_list
                # =====================================
                l = (0, 0, l)
                new_risk_line.append(l)
            res['default_risk_line_ids'] = new_risk_line
        return res

    @api.multi
    def check_riskst_from_warline_st(self, risk_state, warranty_vals=[]):
        if not warranty_vals or risk_state in ('removed', 'new', 'updated'):
            return risk_state
        for warranty in warranty_vals:
            if warranty.get('state') in ('updated','removed','new'):
                risk_state = 'updated'
        return risk_state

    @api.multi
    def get_risk_state(self, risk_line_ids, vals, warrantys={}, descriptions={}, state='intact'):
        if risk_line_ids:
            rm_vals = risk_line_ids.read(['name', 'type_risk_id'])
            for rm_val in rm_vals:
                # del rm_val['id']
                rm_val['state'] = state
                rm_val['type_risk_id'] = rm_val.get('type_risk_id', False)[0] if rm_val.get('type_risk_id', False) else False
                # vals.append((0, 0, rm_val))
                if warrantys:
                    rm_val['state'] = self.check_riskst_from_warline_st(rm_val['state'], warrantys.get(rm_val['id']))
                    wlists = []
                    for wl in warrantys.get(rm_val['id']):
                        wlists.append((0,0,wl))
                    rm_val['movement_warranty_ids'] = wlists
                if descriptions:
                    rm_val['state'] = self.check_riskst_from_warline_st(rm_val['state'], descriptions.get(rm_val['id']))
                    dlists = []
                    for dl in descriptions.get(rm_val['id']):
                        dlists.append((0,0,dl))
                    rm_val['movement_desc_ids'] = dlists
                del rm_val['id']
                vals.append(rm_val)

    @api.multi
    def compare_description(self, recset, state='intact'):
        """
        Description can't be removed just updated
        so, for description comparison we just have
        two states (updated or intact)
        :param:: state: status of risk type
        :param:: recset: analytic_history.risk.line
        """
        if not recset:
            return False
        to_read = ['name','code','value']
        # to_read = ['value']
        vals = {}
        if state in ('removed', 'new'):
            # description state = new if rec is new
            # description state = removed if rec is removed
            logger.info('\n === description state')
            for rec in recset:
                desc_list = []
                desc_ids = rec.risk_description_ids.read(to_read)
                for desc_id in desc_ids:
                    del desc_id['id']
                    desc_id['state'] = state
                    desc_list.append(desc_id)
                vals[rec.id] = desc_list
        elif state in ('updated','intact'):
            logger.info('\n >>> description case 2: updated or intact')
            for rec in recset:
                # description can't be removed
                desc_list = []
                desc_ids = rec.risk_description_ids.filtered(lambda r: r.parent_id)
                for desc_id in desc_ids:
                    inh_desc = desc_id.read(to_read)[0]
                    del inh_desc['id']
                    par_desc = desc_id.parent_id.read(to_read)[0]
                    del par_desc['id']
                    if inh_desc != par_desc:
                        logger.info('updated description')
                        inh_desc['state'] = 'updated'
                        desc_list.append(inh_desc)
                    else:
                        logger.info('intact description')
                        inh_desc['state'] = 'intact'
                        desc_list.append(inh_desc)
                if vals.get(rec.id, False):
                    vals[rec.id] += desc_list
                else:
                    vals[rec.id] = desc_list
        return vals

    @api.multi
    def compare_warranty(self, recset, state='intact'):
        if not recset:
            return False
        to_read = ['name','warranty_id','yearly_net_amount','proratee_net_amount','invoiced']
        vals = {}
        if state in ('removed', 'new'):
            logger.info('\n === compare warranty is new or removed')
            for rec in recset:
                war_list = []
                warranty_ids = rec.warranty_line_ids.read(to_read)
                for warranty in warranty_ids:
                    del warranty['id']
                    warranty['warranty_id'] = warranty.get('warranty_id', False)[0]
                    warranty['state'] = state
                    war_list.append(warranty)
                vals[rec.id] = war_list
        elif state in ('updated','intact'):
            logger.info('\n === compare warranty updated or intact')
            #1 check deleted warranty
            for rec in recset:
                parent_warranty = rec.parent_id.mapped('warranty_line_ids')
                logger.info('\n=== parent_warranty = %s' % parent_warranty)
                inh_warranty = rec.warranty_line_ids.mapped('parent_id')
                logger.info('\n=== inh_warranty = %s' % inh_warranty)
                removed_warranty = parent_warranty - inh_warranty
                logger.info('\n=== removed_warranty = %s' % removed_warranty)
                war_list = []
                if removed_warranty:
                    logger.info('\n=== ??? rec = %s' % rec)
                    warranty_ids = removed_warranty.read(to_read)
                    for warranty in warranty_ids:
                        del warranty['id']
                        warranty['warranty_id'] = warranty.get('warranty_id', False)[0]
                        warranty['state'] = 'removed'
                        war_list.append(warranty)
                    # vals[rec.id] = war_list
                    if vals.get(rec.id, False):
                        vals[rec.id] += war_list
                    else:
                        vals[rec.id] = war_list
            #2 check new warranty
            for rec in recset:
                new_warranty = rec.warranty_line_ids.filtered(lambda r: not r.parent_id)
                war_list = []
                if new_warranty:
                    warranty_ids = new_warranty.read(to_read)
                    for warranty in warranty_ids:
                        del warranty['id']
                        warranty['warranty_id'] = warranty.get('warranty_id', False)[0]
                        warranty['state'] = 'new'
                        war_list.append(warranty)
                    if vals.get(rec.id, False):
                        vals[rec.id] += war_list
                    else:
                        vals[rec.id] = war_list
            #3 check updated (and intact) warranty
            for rec in recset:
                warranty_ids = rec.warranty_line_ids.filtered(lambda r: r.parent_id)
                war_list = []
                if warranty_ids:
                    for warranty_id in warranty_ids:
                        inh_warranty_vals = warranty_id.read(to_read)[0]
                        del inh_warranty_vals['id']
                        par_warranty_vals = warranty_id.parent_id.read(to_read)[0]
                        del par_warranty_vals['id']
                        if inh_warranty_vals != par_warranty_vals:
                            logger.info('\n=== Modified warranty: may be we need to find what is the difference')
                            inh_warranty_vals['warranty_id'] = inh_warranty_vals.get('warranty_id', False)[0]
                            inh_warranty_vals['state'] = 'updated'
                            war_list.append(inh_warranty_vals)
                        else:
                            logger.info('\n=== Intact warranty')
                            inh_warranty_vals['warranty_id'] = inh_warranty_vals.get('warranty_id', False)[0]
                            inh_warranty_vals['state'] = 'intact'
                            war_list.append(inh_warranty_vals)
                    if vals.get(rec.id, False):
                        vals[rec.id] += war_list
                    else:
                        vals[rec.id] = war_list
            #4 check intact warranty
        return vals

    @api.multi
    def compare_trisk_hist(self):
        if not self.parent_id or not self.risk_line_ids:
            return False
        movement = self.env['analytic_history.movement']
        logger.info('\n=== all_risk = %s' % self.risk_line_ids)
        # check wich risk is removed from the parent version first
        current_parent_ids = self.risk_line_ids.mapped('parent_id')
        logger.info('\n=== cur_parent = %s' % current_parent_ids)
        real_parent_ids = self.ver_parent_id.risk_line_ids
        logger.info('\n=== real_parent = %s' % real_parent_ids)
        removed = real_parent_ids - current_parent_ids
        logger.info('\n=== removed = %s' % removed)
        rm_warranty = self.compare_warranty(removed, 'removed')
        rm_desc = self.compare_description(removed, 'removed')
        logger.info('\n=== rm_war = %s' % rm_warranty)
        # =========================================
        # check new risk added
        new_risk_ids = self.risk_line_ids.filtered(lambda r: not r.parent_id)
        logger.info('\n=== new_risk_ids = %s' % new_risk_ids)
        new_warranty = self.compare_warranty(new_risk_ids, 'new')
        new_desc = self.compare_description(new_risk_ids, 'new')
        logger.info('\n=== new_war = %s' % new_warranty)
        # =========================================
        # check updated risk (compare dict)
        upd_risk_ids = False
        ntc_risk_ids = False
        upd_risk_ids_1 = self.risk_line_ids.filtered(lambda r: r.parent_id)
        # logger.info('\n=== upd_risk_ids = %s' % upd_risk_ids)
        # logger.info('\n=== upd_risk_ids_data = %s' % upd_risk_ids.read(['name','type_risk_id']))
        for upd_risk in upd_risk_ids_1:
            inh_risk = upd_risk.read(['name','type_risk_id'])[0]
            del inh_risk['id']
            par_risk = upd_risk.parent_id.read(['name','type_risk_id'])[0]
            del par_risk['id']
            if inh_risk != par_risk:
                logger.info('\n=== Modified risk')
                if not upd_risk_ids:
                    upd_risk_ids = upd_risk
                else:
                    upd_risk_ids += upd_risk
            else:
                logger.info('\n=== Intact risk')
                if not ntc_risk_ids:
                    ntc_risk_ids = upd_risk
                else:
                    ntc_risk_ids += upd_risk
        logger.info('\n=== upd_risk_ids = %s' % upd_risk_ids)
        upd_warranty = self.compare_warranty(upd_risk_ids, 'updated')
        upd_desc = self.compare_description(upd_risk_ids, 'updated')
        logger.info('\n=== upd_warranty = %s' % upd_warranty)
        logger.info('\n=== ntc_risk_ids = %s' % ntc_risk_ids)
        ntc_warranty = self.compare_warranty(ntc_risk_ids, 'intact')
        ntc_desc = self.compare_description(ntc_risk_ids, 'intact')
        vals = []
        # =========================================
        # Treatment for removed risk
        self.get_risk_state(removed, vals, rm_warranty, rm_desc, 'removed')
        # =========================================
        # Treatment for new risk
        self.get_risk_state(new_risk_ids, vals, new_warranty, new_desc, 'new')
        # =========================================
        # Treatment for update risk
        self.get_risk_state(upd_risk_ids, vals, upd_warranty, upd_desc, 'updated')
        # =========================================
        # Treatment for intact risk
        self.get_risk_state(ntc_risk_ids, vals, ntc_warranty, ntc_desc, 'intact')
        logger.info('\n=== vals = %s' % vals)
        # =========================================
        mvt = {
            'name': self.parent_id.name + ' -> ' + self.name,
            # 'movement_line_ids': vals,
        }
        mvt_id = movement.create(mvt)
        logger.info('\n=== mvt_id = %s' % mvt_id)
        mvt_line_obj = self.env['analytic_history.movement.line']
        for mvt_line in vals:
            logger.info('\n=== mvt_line = %s' % mvt_line)
            mvt_line['movement_id'] = mvt_id.id
            mvt_line_obj.create(mvt_line)
        ctx = {
            'default_name': 'Test',
            'default_movement_line_ids': vals,
        }
        logger.info('\n=== ctx2 = %s' % ctx)
        # =========================================
        res = {
            'name': 'History',
            'type': 'ir.actions.act_window',
            'res_model': 'analytic_history.movement',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [self.env.ref('insurance_management.view_analytic_history_movement_form').id],
            'target': 'new',
            'res_id': mvt_id.id
            # 'context': ctx
        }
        return res

    @api.model
    def create(self, vals):
        analytic_obj = self.env['account.analytic.account']
        analytic_id = analytic_obj.browse(self._context.get('default_parent_id'))
        logger.info('create a_id = %s' % analytic_id)
        logger.info('create version_type = %s' % self._context.get('version_type'))
        # increment next_sequence in analytic_account
        ir_seq = self.env['ir.sequence'].search([('code', '=', 'account.analytic.account.policy')])
        next_sequence = analytic_id.next_sequence + ir_seq.number_increment
        analytic_id.write({'next_sequence': next_sequence})
        if self._context.get('version_type') in ['renew', 'amendment', 'terminate', 'suspend', 'reinstatement']:
            parent_history = self._context.get('parent_history')
            parent_history = self.browse(parent_history)
            parent_history.write({'is_last_situation': False})
        if self._context.get('version_type') in ['renew', 'amendment', 'reinstatement']:
            analytic_id.write({'state': 'open'})
        elif self._context.get('version_type') == 'suspend':
            analytic_id.write({'state': 'suspend'})
        elif self._context.get('version_type') == 'terminate':
            # analytic_id.write({'state': 'close'})
            analytic_id.set_close_insurance()
        res = super(AccountAnalyticAccount, self).create(vals)
        return res

    @api.multi
    def unlink(self):
        # search if it's parent
        history_list = self.search([('ver_parent_id', 'in', self.ids)])
        if history_list:
            raise exceptions.Warning(_('Can\'t delete version referenced has parent'))
        for rec in self:
            if rec.type == 'contract':
                if rec.invoice_id:
                    raise exceptions.Warning(_('Can\'t delete version allready invoiced'))
                else:
                    logger.info('vp_id = %s' % rec.ver_parent_id)
                    if rec.ver_parent_id:
                        rec.ver_parent_id.update({'is_last_situation': True})
                    if rec.parent_id:
                        rec.parent_id.update({'next_sequence': rec.parent_id.next_sequence - 1})
        return super(AccountAnalyticAccount, self).unlink()

    @api.multi
    def _get_reg_tax(self, warranty_id, fpos_id):
        """
        :param:: warranty_id: product.product()
        :param:: fpos_id: account.fiscal.position()
        """
        logger.info('war_id = %s' % warranty_id)
        logger.info('fpos_id = %s' % fpos_id)
        tax_obj = self.env['account.tax']
        tax_ids = False
        if not warranty_id :
            return False
        if not fpos_id:
            fpos_id = self.env['account.fiscal.position'].search([('name', '=', 'Z')])
        fiscal_code = warranty_id.fiscal_code
        if not fiscal_code:
            fiscal_code = '4500'
        regtaxref_obj = self.env['reg.tax.reference']
        domain = [('property_account_position', '=', fpos_id.id), ('fiscal_code', '=', fiscal_code)]
        regte = regtaxref_obj.search(domain)
        logger.info('regte = %s' % regte)
        if not regte:
            tax_ids = tax_obj.search([('description', '=', 'Te-0.0')])
        elif regte and len(regte) > 1:
            raise exceptions.Warning(_('Too much result found'))
        else:
            tax_ids = regte.tax_ids
        return tax_ids

    @api.multi
    def generateInvoiceAnalyticLine(self):
        inv_obj = self.env['account.invoice']
        invline_obj = self.env['account.invoice.line']
        # warranty_ids = self.analytic_line_ids.mapped('product_id')
        period_id = self.env['account.period'].search([('date_start','<=', self.date_start),('date_stop','>=', self.date),('special', '=', False)])
        sum_proratee = self.line_ids.mapped('amount_to_invoice')
        sum_proratee = sum(sum_proratee)
        logger.info('sum_proratee = %s' % sum_proratee)
        inv_vals = {
            'name': self.name,
            'state': 'draft',
            'type': 'out_invoice' if sum_proratee > 0 else 'out_refund',
            'history_id': self.id,
            'analytic_id': self.parent_id.id,
            'prm_datedeb': dt.strftime(dt.strptime(self.date_start, DEFAULT_SERVER_DATE_FORMAT), DEFAULT_SERVER_DATE_FORMAT),
            'prm_datefin': dt.strftime(dt.strptime(self.date, DEFAULT_SERVER_DATE_FORMAT), DEFAULT_SERVER_DATE_FORMAT),
            'date_invoice': dt.strftime(dt.now(), DEFAULT_SERVER_DATE_FORMAT),
            'partner_id': self.parent_id.partner_id.id,
            'final_customer_id': self.parent_id.partner_id.id,
            'origin': self.parent_id.name or 'Undefined' +'/'+ self.name or 'Undefined',
            'pol_numpol': self.parent_id.name,
            'journal_id': self._get_user_journal().id,
            'account_id': self.parent_id.partner_id.property_account_receivable.id,
            'comment': self.comment,
            'period_id': period_id.id,
        }
        inv = inv_obj.create(inv_vals)
        for analytic in self.line_ids:
            regte_id = self._get_reg_tax(analytic.product_id, self.property_account_position)
            logger.info('\n *-*-* regte = %s' % regte_id)
            invline_vals = {
                'product_id': analytic.product_id.id,
                'name': analytic.name,
                'account_id': analytic.general_account_id.id,
                'account_analytic_id': analytic.account_id.id,
                'quantity': 1,
                'price_unit': analytic.amount_to_invoice if sum_proratee > 0 else (-1) * analytic.amount_to_invoice,
                'invoice_line_tax_id': [(6,0,regte_id.ids)],
                'invoice_id': inv.id
            }
            invline_obj.create(invline_vals)
        self.line_ids.write({'invoice_id': inv.id})
        self.write({'invoice_id': inv.id})
        inv.button_reset_taxes()
