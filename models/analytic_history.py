# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from openerp.exceptions import Warning,ValidationError
from datetime import datetime as dt
from datetime import date
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import logging
logger = logging.getLogger(__name__)


class AnalyticHistory(models.Model):
    _name = 'analytic.history'
    _description = 'History of the policy'

    @api.depends('starting_date', 'ending_date')
    @api.multi
    def _get_nb_of_days(self):
        for rec in self:
            if not rec.starting_date or not rec.ending_date:
                return False
            ending_date = dt.strptime(rec.ending_date, '%Y-%m-%d')
            starting_date = dt.strptime(rec.starting_date, '%Y-%m-%d')
            logger.info('=== ending_date = %s' % ending_date)
            delta = ending_date - starting_date
            logger.info('=== delta = %s' % delta)
            rec.nb_of_days = delta.days

    # def _get_user_agency(self):


    analytic_id = fields.Many2one(
        comodel_name='account.analytic.account', string='Subscription')
    name = fields.Char(string='History number')
    starting_date = fields.Date(
        string='Starting date', default=fields.Date.context_today,
        required=True)
    ending_date = fields.Date(
        string='Ending date', default=fields.Date.context_today, required=True)
    creating_date = fields.Date(
        string='Creating date', default=fields.Date.context_today,
        required=True)
    is_last_situation = fields.Boolean(
        string='Is the last situation', default=False)
    is_validated = fields.Boolean(string='Is validated', default=False)
    capital = fields.Float(
        string='Capital', digit_compute=dp.get_precision('account'))
    eml = fields.Float(
        string='Expected maximum loss',
        digit_compute=dp.get_precision('account'))
    stage_id = fields.Many2one(
        comodel_name='analytic.history.stage', string='Emission type',
        default=lambda self: self.env.ref('insurance_management.devis').id)
    risk_line_ids = fields.One2many(
        comodel_name='analytic_history.risk.line',
        inverse_name='history_id', string='Risks Type')
    parent_id = fields.Many2one(
        comodel_name='analytic.history', string='Parent',
        help='Inherited Amendment')
    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Invoice', readonly=True)
    comment = fields.Text(string='Comment', help='Some of your note')
    # apporteur_id = fields.Many2one(
    #    comodel_name='res.apporteur', string='Broker',
    #    help='Initial broker of the contract')
    ver_ident = fields.Char(string='Ver Ident')
    property_account_position = fields.Many2one(
        comodel_name='account.fiscal.position', string='Fiscal Position')
    nb_of_days = fields.Integer(compute='_get_nb_of_days', string='Number of days', help='Number of days between start and end date')
    agency_id = fields.Many2one(comodel_name='base.agency', string='Agency', default=lambda self: self.env.user.agency_id)
    accessories = fields.Float(string='Accessories')

    @api.multi
    def confirm_quotation(self):
        """Confirm Quotation and move state to valid new contract"""
        self.stage_id = self.env.ref('insurance_management.affaire_nouvelle').id

    # TODO
    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default.update(name=_("%s (copy)") % (self.name or ''))
        res = super(AnalyticHistory, self).copy(default)
        new_risk_line = False
        for risk_line_id in self.risk_line_ids:
            if not new_risk_line:
                new_risk_line = risk_line_id.copy()
                new_risk_line.write({'history_id': res.id})
            else:
                new_risk_line_buf = risk_line_id.copy()
                new_risk_line_buf.write({'history_id': res.id})
                new_risk_line += new_risk_line_buf
        return res

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

    # @api.model
    # def create(self, vals):
    #     if self._context.get('version_type') in ['renew', 'amendment']:
    #         parent_history = self._context.get('parent_history')
    #         parent_history = self.browse(parent_history)
    #         parent_history.write({'is_last_situation': False})
    #     res = super(AnalyticHistory, self).create(vals)
    #     return res

    @api.model
    def create(self, vals):
        analytic_obj = self.env['account.analytic.account']
        analytic_id = analytic_obj.browse(self._context.get('default_analytic_id'))
        logger.info('create a_id = %s' % analytic_id)
        logger.info('create version_type = %s' % self._context.get('version_type'))
        # increment next_sequence in analytic_account
        ir_seq = self.env['ir.sequence'].search([('code', '=', 'analytic.history')])
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
        res = super(AnalyticHistory, self).create(vals)
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
            insurance_type = self.analytic_id.branch_id.type
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

    @api.constrains('starting_date', 'ending_date')
    def _check_startend_date(self):
        if self.starting_date >= self.ending_date:
            raise ValidationError(_('the effective date must be less than the end date'))

    @api.constrains('capital', 'eml')
    def _check_capital(self):
        if self.eml > self.capital:
            raise ValidationError(_('The expected maximum loss should be less than the capital'))

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
    def _get_accessories_reg_tax(self, type_risk_id, fpos_id):
        """
        Get accessories register tax
        :param:: type_risk_id: insurance.type.risk()
        :param:: fpos_id: account.fiscal.position()
        """
        tax_obj = self.env['account.tax']
        tax_id = False
        if not type_risk_id:
            return False
        if not fpos_id:
            fpos_id = self.env['account.fiscal.position'].search([('name', '=', 'Z')])
        fiscal_code = type_risk_id.fiscal_code
        if not fiscal_code:
            fiscal_code = '4500'
        regtaxref_obj = self.env['reg.tax.reference']
        domain = [('property_account_position', '=', fpos_id.id), ('fiscal_code', '=', fiscal_code)]
        regte = regtaxref_obj.search(domain)
        logger.info('regte = %s' % regte)
        if not regte:
            tax_id = tax_obj.search([('description', '=', 'Te-0.0')])
        elif regte and len(regte) > 1:
            raise exceptions.Warning(_('Too much result found'))
        else:
            tax_id = regte.tax_ids
        return tax_id

    # TODO
    @api.multi
    def generate_invoice(self):
        """ Generate an invoice in draft state """
        self.ensure_one()
        invline_obj = self.env['account.invoice.line']
        product_obj = self.env['product.product']
        res = {}
        warranty_ids = False
        warranty_amount = {}
        if self.invoice_id:
            res = {
                'type': 'ir.actions.act_window',
                'name': _('Invoice'),
                'res_model': 'account.invoice',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': [self.env.ref('account.invoice_form').id],
                'res_id': self.invoice_id.id,
                'target': 'current',
                # 'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}},
            }
        else:
            # Get list of warranty in current history
            for risk_line_id in self.risk_line_ids:
                if not warranty_ids:
                    warranty_ids = risk_line_id.warranty_line_ids.mapped('warranty_id')
                else:
                    warranty_ids += risk_line_id.warranty_line_ids.mapped('warranty_id')
            # Remove duplicated Warranty (group same warranty in invoice)
            if not warranty_ids:
                raise Warning(_('There is no warranty to invoice in this contract history'))
            warranty_ids = list(set(warranty_ids.ids))
            warranty_ids = product_obj.browse(warranty_ids)
            # Get amount of warranty in current history
            warranty_line_ids_map = self.risk_line_ids.mapped('warranty_line_ids')
            logger.info('warranty_line_ids_map = %s' % warranty_line_ids_map)
            for wl_id in warranty_line_ids_map:
                if wl_id.warranty_id.id in warranty_amount.keys():
                    warranty_amount[wl_id.warranty_id.id] += wl_id.proratee_net_amount
                else:
                    warranty_amount[wl_id.warranty_id.id] = wl_id.proratee_net_amount
            logger.info('wa = %s' % warranty_amount)
            invoice_line = []
            for warranty_id in warranty_ids:
                # Get reg tax_id
                compute_line = invline_obj.product_id_change(warranty_id.id, warranty_id.uom_id.id, partner_id=self.analytic_id.partner_id.id)
                line = compute_line.get('value', {})
                line.update(product_id=warranty_id.id)
                line.update(quantity=1)
                line.update(account_analytic_id=self.analytic_id.id)
                line.update(price_unit=warranty_amount.get(warranty_id.id))
                regte_id = self._get_reg_tax(warranty_id, self.property_account_position)
                logger.info('=== regte_id = %s ===' % regte_id)
                if regte_id:
                    # line['invoice_line_tax_id'].append(regte_id.ids)
                    line['invoice_line_tax_id'] += regte_id.ids
                # logger.info('=== line = %s ===' % line)
                invoice_line.append((0, 0, line))
            # Get each type risk in current history
            type_risk_ids_map = self.risk_line_ids.mapped('type_risk_id')
            logger.info('\n=== tr_ids_map = %s' % type_risk_ids_map)
            access_reg_tax = []
            for type_risk_id in type_risk_ids_map:
                acc_te = self._get_accessories_reg_tax(type_risk_id, self.property_account_position)
                # access_reg_tax.append(acc_te.id)
                access_reg_tax = acc_te.ids
            # Insert Accessories in invoice_line
            compl_line = {
                'price_unit': self.analytic_id.ins_product_id.amount_accessories
            }
            if self._context.get('insurance_categ') == 'T' or self.analytic_id.branch_id.category == 'T':
                access_tmpl_id = self.env.ref('aro_custom_v8.product_template_accessoire_terrestre_r0')
                access_id = product_obj.search([('product_tmpl_id', '=', access_tmpl_id.id)])
                accessory_line = invline_obj.product_id_change(access_id.id, access_id.uom_id.id, partner_id=self.analytic_id.partner_id.id)
                accessory_line = accessory_line.get('value', {})
                compl_line.update({
                    'product_id': access_id.id,
                    'quantity': 1,
                    'account_analytic_id': self.analytic_id.id,
                })
                accessory_line.update(compl_line)
                # update accessory_line with register tax
                accessory_line['invoice_line_tax_id'] += access_reg_tax
                logger.info('acc_line T = %s' % accessory_line)
                # update amount of accessories if accessories in history is not zero
                if self.accessories != 0:
                    accessory_line['price_unit'] = self.accessories
                invoice_line.append((0, 0, accessory_line))
            # =========================================================
            elif self._context.get('insurance_categ') == 'M' or self.analytic_id.branch_id.category == 'M':
                access_tmpl_id = self.env.ref('aro_custom_v8.product_template_accessoire_maritime_r0')
                access_id = product_obj.search([('product_tmpl_id', '=', access_tmpl_id.id)])
                accessory_line = invline_obj.product_id_change(access_id.id, access_id.uom_id.id, partner_id=self.analytic_id.partner_id.id)
                accessory_line = accessory_line.get('value', {})
                compl_line.update({
                    'product_id': access_id.id,
                    'quantity': 1,
                    'account_analytic_id': self.analytic_id.id,
                })
                accessory_line.update(compl_line)
                # update accessory_line with register tax
                accessory_line['invoice_line_tax_id'] += access_reg_tax
                logger.info('acc_line M = %s' % accessory_line)
                # update amount of accessories if accessories in history is not zero
                if self.accessories != 0:
                    accessory_line['price_unit'] = self.accessories
                invoice_line.append((0, 0, accessory_line))
                logger.info('\n=== acc_line = %s' % accessory_line)
            # logger.info('\n=== inv_line = %s' % invoice_line)
            # =========================================================
            default_account = self.env['account.account'].search([('code', '=', '410000')])
            ctx_vals = {
                'default_name': self.name,
                'default_state': 'draft',
                'default_type': 'out_invoice',
                'default_history_id': self.id,
                'default_analytic_id': self.analytic_id.id,
                'default_prm_datedeb': dt.strftime(dt.strptime(self.starting_date, DEFAULT_SERVER_DATE_FORMAT), DEFAULT_SERVER_DATE_FORMAT),
                'default_prm_datefin': dt.strftime(dt.strptime(self.ending_date, DEFAULT_SERVER_DATE_FORMAT), DEFAULT_SERVER_DATE_FORMAT),
                'default_date_invoice': dt.strftime(dt.now(), DEFAULT_SERVER_DATE_FORMAT),
                'default_partner_id': self.analytic_id.partner_id.id,
                'default_final_customer_id': self.analytic_id.partner_id.id,
                'default_origin': self.analytic_id.name +'/'+self.name,
                'default_pol_numpol': self.analytic_id.name,
                'default_journal_id': self._get_user_journal().id,
                'journal_id': self._get_user_journal().id,
                'default_account_id': self.analytic_id.partner_id.property_account_receivable.id or default_account.id,
                'default_invoice_line': invoice_line,
                'default_comment': self.comment,
            }
            ctx = self._context.copy()
            ctx.update(ctx_vals)
            # logger.info('== ctx_journal_id = %s' % ctx.get('default_journal_id'))
            res.update({
                'type': 'ir.actions.act_window',
                'name': _('Invoice'),
                'res_model': 'account.invoice',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': [self.env.ref('account.invoice_form').id],
                'context': ctx,
                'target': 'current',
                'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}},
            })
            logger.info('ctx = %s' % res.get('context'))
            if self._context.get('invoice_unedit', False):
                res = {
                    'name': self.name,
                    'state': 'draft',
                    'type': 'out_invoice',
                    'history_id': self.id,
                    'analytic_id': self.analytic_id.id,
                    'prm_datedeb': dt.strftime(dt.strptime(self.starting_date, DEFAULT_SERVER_DATE_FORMAT), DEFAULT_SERVER_DATE_FORMAT),
                    'prm_datefin': dt.strftime(dt.strptime(self.ending_date, DEFAULT_SERVER_DATE_FORMAT), DEFAULT_SERVER_DATE_FORMAT),
                    'date_invoice': dt.strftime(dt.now(), DEFAULT_SERVER_DATE_FORMAT),
                    'partner_id': self.analytic_id.partner_id.id,
                    'final_customer_id': self.analytic_id.partner_id.id,
                    'origin': self.analytic_id.name +'/'+self.name,
                    'pol_numpol': self.analytic_id.name,
                    'journal_id': self._get_user_journal().id,
                    'account_id': self.analytic_id.partner_id.property_account_receivable.id or default_account.id,
                    'invoice_line': invoice_line,
                    'comment': self.comment,
                }
        return res

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
        # logger.info('\n=== cur_parent = %s' % current_parent_ids)
        real_parent_ids = self.parent_id.risk_line_ids
        # logger.info('\n=== real_parent = %s' % real_parent_ids)
        removed = real_parent_ids - current_parent_ids
        logger.info('\n=== removed = %s' % removed)
        rm_warranty = self.compare_warranty(removed, 'removed')
        rm_desc= self.compare_description(removed, 'removed')
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
    def check_riskst_from_warline_st(self, risk_state, warranty_vals=[]):
        if not warranty_vals or risk_state in ('removed', 'new', 'updated'):
            return risk_state
        for warranty in warranty_vals:
            if warranty.get('state') in ('updated','removed','new'):
                risk_state = 'updated'
        return risk_state

    @api.multi
    def _compare_type_risk_history(self):
        if not self.parent_id or not self.risk_line_ids:
            return False
        new_rline_list = []
        updated_rline_list = [] # if something is changed
        removed_rline_list = []
        ah_rl_obj = self.env['analytic_history.risk.line']
        for rl_id in self.risk_line_ids:
            # search if exist in parent_version
            rline = {
                'partner_id': rl_id.partner_id.id,
                'type_risk_id': rl_id.type_risk_id.id,
                'name': rl_id.name,
                'history_id': self.parent_id.id,
            }
            domain = self._convert_dict_to_domain(rline)
            ah_rl_id = ah_rl_obj.search(domain)
            if not ah_rl_id:
                rline.pop('history_id')
                rline['id'] = rl_id.id
                new_rline_list.append(rline)

    @api.multi
    def _convert_dict_to_domain(self, vals):
        res = []
        if not vals:
            return res
        for k in vals.keys():
            if isinstance(vals[k], list):
                vals[k] = tuple(vals[k])
            elif isinstance(vals[k], dict):
                logger.info('''Can't convert dict as domain''')
            res.append((k, '=', vals[k]))
        return res

    # TODO
    @api.multi
    def compute_ristourne(self):
        """
        En cas d'avenant:
            - si une garantie ou un risque est retiré du contrat alors une partie
            de la prime payé par le client doit être remboursé
            - si une garantie ou un risque est ajouté au contrat alors on recalcule
            la valeur de la prime en plus qui doit être payé par le client.
        """
        return True

    @api.multi
    def unlink(self):
        # search if it's parent
        history_list = self.search([('parent_id', 'in', self.ids)])
        if history_list:
            raise exceptions.Warning(_('Can\'t delete version referenced has parent'))
        for rec in self:
            if rec.invoice_id:
                raise exceptions.Warning(_('Can\'t delete version allready invoiced'))
            else:
                rec.parent_id.update({'is_last_situation': True})
                rec.analytic_id.update({'next_sequence': rec.analytic_id.next_sequence - 1})
        return super(AnalyticHistory, self).unlink()
