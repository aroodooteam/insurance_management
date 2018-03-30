# -*- coding: utf-8 -*-


from openerp import api, exceptions, fields, models, _
import logging
logger = logging.getLogger(__name__)
from openerp.tools.safe_eval import safe_eval


class AnalyticHistoryRiskLine(models.Model):
    _name = 'analytic_history.risk.line'
    _description = 'Subscription line (Content list of risk type)'

    @api.depends('insured_id')
    @api.multi
    def _get_partner_right(self):
        if not self.insured_id:
            return False
        family_obj = self.env['res.partner.family']
        family_ids = family_obj.search([('partner_id', '=', self.insured_id.id)])
        having_right = self.insured_id
        having_right += family_ids.mapped('name')
        self.have_right_ids = having_right
        return {
            'domain': {
                'partner_id': [('id', 'in', having_right.ids)]
            }
        }


    name = fields.Char(string='Description')
    template = fields.Boolean(string='Template', help='Used as template')
    # history_id = fields.Many2one(comodel_name='analytic.history', string='Amendment Line')
    history_id = fields.Many2one(comodel_name='account.analytic.account', string='Amendment Line') # version
    analytic_id = fields.Many2one(comodel_name='account.analytic.account', string='Subscription') # contract
    ins_product_id = fields.Many2one(comodel_name='insurance.product', string='Insurance Product', related='analytic_id.ins_product_id')
    type_risk_id = fields.Many2one(comodel_name='insurance.type.risk', string='Risk', domain="[('ins_product_id', '=', ins_product_id)]")
    warranty_line_ids = fields.One2many(comodel_name='risk.warranty.line', inverse_name='history_risk_line_id', string='Warranty')
    risk_description_ids = fields.One2many(comodel_name='risk.description.line', inverse_name='history_risk_line_id', string='Risk description')
    # risk_warranty_tmpl_id = fields.Many2one(comodel_name='type.risk.warranty.template', string='Template', domain="[('type_risk_id', '=', type_risk_id)]")
    risk_warranty_tmpl_id = fields.Many2one(comodel_name='analytic_history.risk.line', string='Template', domain="[('type_risk_id', '=', type_risk_id),('template', '=', True)]")
    insured_id = fields.Many2one(comodel_name='res.partner', string='Insured', related='analytic_id.insured_id')
    have_right_ids = fields.One2many(comodel_name='res.partner', string='Having right', compute='_get_partner_right', store=False)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner')
    comment = fields.Text(string='Comment')
    sor_ident = fields.Char(string='Sor Ident')
    parent_id = fields.Many2one(comodel_name='analytic_history.risk.line', string='Parent', help='Parent of this analytic_history.risk.line')

    @api.onchange('insured_id')
    def onchange_insured_id(self):
        if not self.insured_id:
            return False
        self.partner_id = self.insured_id
        return {
            'domain': {
                'partner_id': [('id', 'in', self.have_right_ids.ids)]
            },
        }

    @api.onchange('history_id')
    def onchange_amendment_line(self):
        self.analytic_id = self.history_id.parent_id.id

    # TODO
    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default.update(name="%s" % (self.name or ''))
        res = super(AroInsuranceSubscriptionRiskLine, self).copy(default)
        new_warranty_line = False
        for warranty_line_id in self.warranty_line_ids:
            if not new_warranty_line:
                new_warranty_line = warranty_line_id.copy()
                new_warranty_line.write({'risk_id': res.id})
            else:
                new_warranty_line_buf = warranty_line_id.copy()
                new_warranty_line_buf.write({'risk_id': res.id})
                new_warranty_line += new_warranty_line_buf
        logger.info('res = %s' % res)
        return res

    @api.onchange('type_risk_id')
    def onchange_type_risk(self):
        if not self.type_risk_id:
            return False
        ctx = self._context.copy()
        ctx.update(onchange_type_risk=True)
        self.with_context(ctx)
        description_obj = self.env['insurance_type_risk.description']
        desc_ids = description_obj.search([('type_risk_id', '=', self.type_risk_id.id)], order='code asc')
        all_desc = []
        # tmpl_obj = self.env['type.risk.warranty.template']
        tmpl_id = self.search([('template', '=', True), ('type_risk_id', '=', self.type_risk_id.id)], limit=1)
        # tmpl_id = tmpl_obj.search([('type_risk_id', '=', self.type_risk_id.id), ('is_default', '=', True)], limit=1)
        for desc_id in desc_ids:
            all_desc.append(
                (0, 0, {'code': desc_id.code, 'name': desc_id.name,})
            )
            self.update({'risk_description_ids': all_desc, 'risk_warranty_tmpl_id': tmpl_id.id if tmpl_id else False})

    # TODO
    @api.onchange('risk_warranty_tmpl_id')
    def onchange_risk_warranty_template(self):
        if not self.risk_warranty_tmpl_id or not self._context:
            return False
        # tmpl_obj = self.env['type.risk.warranty.template']
        # tmpl_id = tmpl_obj.search([('type_risk_id', '=', self.type_risk_id), ('is_default', '=', True)], limit=1)
        all_tmpl = []
        for tmpl_id in self.risk_warranty_tmpl_id.warranty_line_tmpl_ids:
            all_tmpl.append(
                (0, 0, {'warranty_id': tmpl_id.warranty_id.id, 'name': tmpl_id.name,})
            )
            self.update({'warranty_line_ids': all_tmpl})
        logger.info(' \n === onchange warranty template')

    # TODO
    # @api.multi
    # def compute_risk_description_ids(self):
    @api.onchange('risk_description_ids')
    def onchange_risk_description_ids(self):
        desc_obj = self.env['risk.description.line']
        logger.info('self = %s' % self)
        if not self.risk_description_ids:
            # self.name = _("No description specified")
            logger.info('desc_list = %s' % self.risk_description_ids)
            return False
        else:
            logger.info('else desc_list = %s' % self.risk_description_ids)
            if self.type_risk_id.description:
                code = safe_eval(self.type_risk_id.description)
                logger.info('desc_ok = %s' % code)
                if isinstance(code, list):
                    # dom = [('code','in', code),('id','in',self.risk_description_ids.ids)]
                    self.name = ''
                    for cd in code:
                        for risk in self.risk_description_ids:
                            if risk.code == cd and risk.value:
                                logger.info('value %s = %s' % (code, risk.value))
                                if not self.name:
                                    self.name = risk.value + ' | '
                                else:
                                    self.name += risk.value
                            elif risk.code == cd and not risk.value:
                                logger.info('value %s = %s' % (code, risk.value))
                                # raise exceptions.Warning(_('Contact your Administrator to fix the description of risk in type of risk'))
