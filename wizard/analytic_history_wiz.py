# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from openerp import api, exceptions, fields, models, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class AnalyticHistoryWiz(models.TransientModel):
    _name = 'analytic.history.wiz'
    _description = 'Wizard to control the version of contract will be created'

    stage_id = fields.Many2one(comodel_name='analytic.history.stage', string='Stage', help='Different stage of the history')

    @api.multi
    @api.multi
    def to_validate(self):
        logger.info('\n=== ctx_to_validate = %s'% str(self._context))
        ctx = self._context.copy()
        analytic_obj = self.env['account.analytic.account']
        analytic_id = analytic_obj.browse(ctx.get('active_id'))
        seq_obj = self.env['ir.sequence'] # .with_context(number_next_actual=1).next_by_code('analytic.history')
        seq_id = seq_obj.search([('code', '=', 'account.analytic.account.policy')])
        seq = analytic_id.name + '-%%0%sd' % seq_id.padding % analytic_id.next_sequence
        logger.info('seq = %s' % seq)
        ctx.update(default_name=seq)
        ctx['default_type'] = 'contract'
        ctx['default_stage_id'] = self.stage_id.id
        ctx['default_is_last_situation'] = True
        ctx['default_parent_id'] = ctx.get('active_id')
        ctx['default_property_account_position'] = ctx.get('property_account_position')
        if not self.stage_id:
            raise exceptions.Warning(_('No stage selected. Please choose one before process'))
        logger.info('stage_id = %s' % self.stage_id)
        history_ids = analytic_obj.search([('parent_id', '=', self._context.get('active_id')), ('is_last_situation', '=', True)])
        logger.info('=== history_ids = %s' % history_ids)
        if history_ids and len(history_ids) > 1:
            raise exceptions.Warning(_('You have too many last version for this contract. Please contact your Administrator.\n [Note]'))
        if not history_ids and self.stage_id.code not in ('AFN', 'DEV'):
            raise  exceptions.Warning(_('There is no history yet for this contract. You have to select <AFN> or <DEV>'))
        elif history_ids:
            ctx['default_partner_id'] = history_ids.partner_id.id
            ctx['default_insured_id'] = history_ids.insured_id.id
            ctx['default_branch_id'] = history_ids.branch_id.id
            ctx['default_ins_product_id'] = history_ids.ins_product_id.id
            ctx['default_fraction_id'] = history_ids.fraction_id.id
            ctx['default_force_acs'] = history_ids.force_acs
            ctx['default_accessories'] = history_ids.accessories
            if self.stage_id.code in ('DEV', 'AFN'):
                logger.info('You can\'t have twice <AFN> in same contract')
                raise exceptions.Warning(_('You can\'t have twice <AFN> in same contract \n [Note]'))
            elif self.stage_id.code == 'RES' and history_ids.stage_id.code not in ('RES', 'DEV'):
                logger.info('Resilliate contract: Create history with state=RES and close current contract')
                return self.with_context(ctx).cancel_analytic_account(history_ids)
            elif self.stage_id.code in ('AVT') and history_ids.stage_id.code not in ('RES', 'SUS'):
                logger.info('Amendment contract')
                return self.with_context(ctx).update_contract()
            elif self.stage_id.code in ('REN') and history_ids.stage_id.code not in ('RES', 'SUS'):
                logger.info('Renew contract')
                return self.with_context(ctx).renew_analytic_account(history_ids)
            elif self.stage_id.code in ('SUS') and history_ids.stage_id.code not in ('RES', 'SUS'):
                logger.info('Suspend contract')
                return self.with_context(ctx).suspend_analytic_account()
            elif self.stage_id.code in ('REV') and history_ids.stage_id.code in ('SUS'):
                logger.info('Re-activate contract')
                return self.with_context(ctx).reinstatement_analytic_account(history_ids)
            else:
                logger.info('Un-treated case')
                raise exceptions.Warning(_('Un-treated case \n [Note]'))
        elif not history_ids and self.stage_id.code in ('AFN', 'DEV'):
            logger.info('Create AFN or DEV contract')
            return {
                'name': 'History',
                'type': 'ir.actions.act_window',
                'res_model': 'analytic.history',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('insurance_management.view_analytic_history_form').id,
                'target': 'current',
                'context': ctx
            }
        # else:
        #     logger.info('Un-treated case')
        #     raise exceptions.Warning(_('Un-treated case \n [Note]'))
        # logger.info('Before returning standard view')
        # return {
        #     'name': 'History',
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'analytic.history',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'view_id': self.env.ref('insurance_management.view_analytic_history_form').id,
        #     'target': 'current',
        #     'context': ctx
        # }

    @api.multi
    def renew_analytic_account(self, history_ids=False):
        # resilie = self.env.ref('insurance_management.status_resilie').id
        # devis = self.env.ref('insurance_management.status_devis').id
        # history_obj = self.env['analytic.history']
        analytic_obj = self.env['account.analytic.account']
        analytic_id = analytic_obj.browse(self._context.get('active'))
        # if self.stage_id.id == resilie:
        if analytic_id.state == 'close':
            raise exceptions.Warning(_('You can\'t create new version for contract closed'))
            # raise exceptions.Warning(_('You can\'t renew contract closed'))
        # elif self.status_id.id == devis:
        #     raise exceptions.Warning(_('You can\'t renew unvalidated contract'))
        res = {}
        ctx = self._context.copy()
        ctx['default_parent_id'] = self._context.get('active_id')
        ctx['default_type'] = 'contract'
        if not ctx.get('version_type', False):
            ctx['version_type'] = 'renew'
        # logger.info('\n === ctx version = %s' % ctx['version_type'])
        ctx['default'] = True
        # logger.info('\n === ctx = %s' % self.ending_date)
        if not history_ids:
            # history_obj = self.env['analytic.history']
            history_ids = analytic_obj.search([('parent_id', '=', self._context.get('active_id')), ('is_last_situation', '=', True)])
        if not history_ids or len(history_ids) > 1:
            raise exceptions.Warning(_('Sorry, You don\'t have or you get more than one amendment defined as last situation.\n Fix it first before continuing'))
        else:
            logger.info('\n === ending_date = %s' % history_ids.date)
            copy_vals = history_ids.with_context(ctx)._get_all_value()
            # get default_name in ctx
            if 'default_name' in ctx:
                copy_vals.pop('default_name')
            # end of ctx get name
            # ctx.update(parent_history=history_ids.id)
            # ctx.update(ver_parent_id=history_ids.id)
            copy_vals.update(default_is_last_situation=True)
            copy_vals.update(default_stage_id=self.env.ref('insurance_management.renouvellement').id)
            copy_vals.update(default_ver_parent_id=history_ids.id)
            new_date = self.get_end_date(history_ids.date)
            copy_vals.update(default_date_start=new_date.get('start_date'))
            copy_vals.update(default_date=new_date.get('end_date'))
            # logger.info('\n === copy_vals = %s' % copy_vals)
            # copy_vals.update(default_ending_date=self.get_end_date(self))
            ctx.update(copy_vals)
            view_id = self.env.ref('insurance_management.view_account_analytic_account_form').id
            res.update({
                'type': 'ir.actions.act_window',
                'name': _('Renew'),
                'res_model': 'account.analytic.account',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': [view_id],
                # 'res_id': new_amendment.id,
                'context': ctx,
                'target': 'current',
                'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}},
            })
        return res

    @api.multi
    def update_contract(self):
        """ Update contract: Avenant """
        history_obj = self.env['account.analytic.account']
        res = self.renew_analytic_account()
        ctx = res.get('context', {})
        res.update(name=_('Amendment'))
        ctx.update(version_type='amendment')
        logger.info('\n === parent_id = %s' % ctx.get('default_ver_parent_id', False))
        history_id = ctx.get('default_ver_parent_id', False)
        history_id = history_obj.browse(history_id)
        ctx.update(default_date_start=history_id.date_start)
        ctx.update(default_date=history_id.date)
        ctx.update(default_stage_id=self.env.ref('insurance_management.avenant').id)
        res.update(context=ctx)
        return res

    # TODO
    @api.multi
    def cancel_analytic_account(self, history_ids=False):
        res = False
        history_obj = self.env['account.analytic.account']
        res = self.with_context(version_type='terminate').renew_analytic_account(history_ids)
        ctx = res.get('context', {})
        res.update(name=_('Terminate'))
        history_id = ctx.get('default_ver_parent_id', False)
        history_id = history_obj.browse(history_id)
        ctx.update(default_starting_date=history_id.date_start)
        ctx.update(default_date=history_id.date)
        ctx.update(default_stage_id=self.env.ref('insurance_management.resiliation').id)
        res.update(context=ctx)
        return res

    # TODO
    @api.multi
    def suspend_analytic_account(self):
        """ Suspend subscription : Suspension """
        history_obj = self.env['analytic.history']
        res = self.with_context(version_type='suspend').renew_analytic_account()
        ctx = res.get('context', {})
        res.update(name=_('Pending'))
        history_id = ctx.get('default_parent_id', False)
        history_id = history_obj.browse(history_id)
        ctx.update(default_starting_date=history_id.starting_date)
        ctx.update(default_ending_date=history_id.ending_date)
        ctx.update(default_stage_id=self.env.ref('insurance_management.suspension').id)
        res.update(context=ctx)
        return res

    # TODO
    @api.multi
    def reinstatement_analytic_account(self, history_ids=False):
        """ Reinstatment : d'abord voir si police suspendue """
        status_id = self.env.ref('insurance_management.suspension')
        if history_ids and history_ids.stage_id != status_id:
            raise exceptions.Warning(_('Sorry, You don\'t have to reinstate a subscription which is not suspended'))
        else:
            history_obj = self.env['analytic.history']
            res = self.with_context(version_type='reinstatement').renew_analytic_account()
            ctx = res.get('context', {})
            res.update(name=_('Reinstatment'))
            history_id = ctx.get('default_parent_id', False)
            history_id = history_obj.browse(history_id)
            ctx.update(default_starting_date=history_id.starting_date)
            ctx.update(default_ending_date=history_id.ending_date)
            ctx.update(default_stage_id=self.env.ref('insurance_management.remise_en_vigueur').id)
            res.update(context=ctx)
            return res

    @api.multi
    def get_end_date(self, start_date=False):
        analytic_obj = self.env['account.analytic.account']
        analytic_id = analytic_obj.browse(self._context.get('active_id'))
        if not start_date:
            start_date = datetime.today()
        else:
            start_date = datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
        end_date = start_date
        if analytic_id.fraction_id == self.env.ref('insurance_management.fraction_annual'):
            end_date = start_date + relativedelta(months=12)
        elif analytic_id.fraction_id == self.env.ref('insurance_management.fraction_half_yearly'):
            end_date = start_date + relativedelta(months=6)
        elif analytic_id.fraction_id == self.env.ref('insurance_management.fraction_quarterly'):
            end_date = start_date + relativedelta(months=3)
        elif analytic_id.fraction_id in (self.env.ref('insurance_management.fraction_monthly'),self.env.ref('insurance_management.fraction_unique')):
            end_date = start_date + relativedelta(months=1)
        if self._context.get('version_type') != 'new':
            start_date = start_date + timedelta(days=1)
        end_date = end_date - timedelta(days=1)
        res = {
            'end_date': datetime.strftime(end_date, DEFAULT_SERVER_DATE_FORMAT),
            'start_date': datetime.strftime(start_date, DEFAULT_SERVER_DATE_FORMAT)
        }
        return res
