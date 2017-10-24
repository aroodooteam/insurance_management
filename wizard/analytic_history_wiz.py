# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)
from openerp import api, exceptions, fields, models, _



class AnalyticHistoryWiz(models.TransientModel):
    _name = 'analytic.history.wiz'
    _description = 'Wizard to control the version of contract will be created'

    stage_id = fields.Many2one(comodel_name='analytic.history.stage', string='Stage', help='Different stage of the history')

    @api.multi
    def to_validate(self):
        logger.info('ctx = %s'% str(self._context))
        ctx = self._context.copy()
        ctx['default_stage_id'] = self.stage_id.id
        ctx['default_is_last_situation'] = True
        ctx['default_analytic_id'] = ctx.get('active_id')
        if not self.stage_id:
            raise exceptions.Warning(_('No stage selected. Please choose one before process'))
        logger.info('stage_id = %s' % self.stage_id)
        history_obj = self.env['analytic.history']
        history_ids = history_obj.search([('analytic_id', '=', self._context.get('active_id')), ('is_last_situation', '=', True)])
        if history_ids and len(history_ids) > 1:
            raise exceptions.Warning(_('You have too many last version for this contract. Please contact your Administrator.\n [Note]'))
        if not history_ids and self.stage_id.code not in ('AFN', 'DEV'):
            raise  exceptions.Warning(_('There is no history yet for this contract. You have to select <AFN> or <DEV>'))
        elif history_ids:
            if self.stage_id.code in ('DEV', 'AFN'):
                logger.info('You can\'t have twice <AFN> in same contract')
                raise exceptions.Warning(_('You can\'t have twice <AFN> in same contract \n [Note]'))
            elif self.stage_id.code == 'RES' and history_ids.stage_id.code not in ('RES', 'DEV'):
                logger.info('Resilliate contract: Create history with state=RES and close current contract')
            elif self.stage_id.code in ('AVN') and history_ids.stage_id.code not in ('RES'):
                logger.info('Amendment contract')
            elif self.stage_id.code in ('REN') and history_ids.stage_id.code not in ('RES'):
                logger.info('Renew contract')
            elif self.stage_id.code in ('SUS') and history_ids.stage_id.code not in ('RES', 'SUS'):
                logger.info('Suspend contract')
            elif self.stage_id.code in ('REV') and history_ids.stage_id.code in ('SUS'):
                logger.info('Re-activate contract')
        elif not history_ids and self.stage_id.code in ('AFN', 'DEV'):
            logger.info('Create AFN or DEV contract')
            if self.stage_id.code == 'AFN':
                logger.info('New contract')
            if self.stage_id.code == 'DEV':
                logger.info('Devis contract')

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
