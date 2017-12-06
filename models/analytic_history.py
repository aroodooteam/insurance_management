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
        if not self.starting_date or not self.ending_date:
            return False
        ending_date = dt.strptime(self.ending_date, '%Y-%m-%d')
        starting_date = dt.strptime(self.starting_date, '%Y-%m-%d')
        logger.info('=== ending_date = %s' % ending_date)
        delta = ending_date - starting_date
        logger.info('=== delta = %s' % delta)
        self.nb_of_days = delta.days

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
            'warranty_line_ids': ['name', 'warranty_id', 'history_risk_line_id'],
            'risk_description_ids': ['name', 'code', 'value']
        }
        new_risk_line = []
        # TODO
        # content of if should be implemented
        if not self._context.get('default', False):
            res['name'] = _('%s (copy)') % self.name or ''
            res['capital'] = self.capital
            res['eml'] = self.eml
            for risk_line_id in self.risk_line_ids:
                new_risk_line.append(risk_line_id.read(list_fields))
        else:
            res['default_name'] = _('%s (copy)') % self.name or ''
            res['default_capital'] = self.capital
            res['default_eml'] = self.eml
            for risk_line_id in self.risk_line_ids:
                l = risk_line_id.read(list_fields)[0]
                # get standard fields
                l['type_risk_id'] = l.get('type_risk_id', False)[0]
                l['partner_id'] = l.get('partner_id', False)[0] if l.get('partner_id', False) else False
                l['risk_warranty_tmpl_id'] = l.get('risk_warranty_tmpl_id', False)
                l['risk_warranty_tmpl_id'] = l.get('risk_warranty_tmpl_id')[0] if l.get('risk_warranty_tmpl_id', False) else False
                del l['id']
                # get o2m fields value
                logger.info('wlids = %s' % risk_line_id.warranty_line_ids)
                om_warrantys = risk_line_id.warranty_line_ids.read(om_fields.get('warranty_line_ids'))
                warranty_list = []
                for om_warranty in om_warrantys:
                    del om_warranty['id']
                    om_warranty['warranty_id'] = om_warranty.get('warranty_id')[0] if om_warranty.get('warranty_id') else False
                    om_warranty['history_risk_line_id'] = om_warranty.get('history_risk_line_id')[0] if om_warranty.get('history_risk_line_id') else False
                    warranty_list.append((0, 0, om_warranty))
                l['warranty_line_ids'] = warranty_list
                # =====================================
                om_descs = risk_line_id.risk_description_ids.read(om_fields.get('risk_description_ids'))
                description_list = []
                for om_desc in om_descs:
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
            analytic_id.set_close()
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
        if not agency_id:
            raise Warning(_('Please contact your Administrator to set your agency'))

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
            raise ValidationError(_('the effective date must be after the end date'))

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
        tax_id = False
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
            tax_id = tax_obj.search([('description', '=', 'Te-0.0')])
        elif regte and len(regte) > 1:
            raise exceptions.Warning(_('Too much result found'))
        else:
            tax_id = regte.tax_id
        return tax_id

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
            tax_id = regte.tax_id
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
                    line['invoice_line_tax_id'].append(regte_id.id)
                logger.info('=== line = %s ===' % line)
                invoice_line.append((0, 0, line))
            # Get each type risk in current history
            type_risk_ids_map = self.risk_line_ids.mapped('type_risk_id')
            logger.info('\n=== tr_ids_map = %s' % type_risk_ids_map)
            access_reg_tax = []
            for type_risk_id in type_risk_ids_map:
                acc_te = self._get_accessories_reg_tax(type_risk_id, self.property_account_position)
                access_reg_tax.append(acc_te.id)
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
                invoice_line.append((0, 0, accessory_line))
                logger.info('\n=== acc_line = %s' % accessory_line)
            logger.info('\n=== inv_line = %s' % invoice_line)
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
            logger.info('== ctx_journal_id = %s' % ctx.get('default_journal_id'))
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
        return res
