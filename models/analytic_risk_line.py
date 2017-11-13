# -*- coding: utf-8 -*-


from openerp import api, exceptions, fields, models, _
import logging
logger = logging.getLogger(__name__)


class AnalyticRiskLine(models.Model):
    _name = 'analytic.risk.line'
    _description = 'Subscription line (Content list of risk type)'

    name = fields.Char(string='Description')
    template = fields.Boolean(string='Template', help='Used as template')
    analytic_id = fields.Many2one(comodel_name='account.analytic.account', string='Subscription')
    ins_product_id = fields.Many2one(comodel_name='insurance.product', string='Insurance Product', related='analytic_id.ins_product_id')
    type_risk_id = fields.Many2one(comodel_name='insurance.type.risk', string='Risk', domain="[('ins_product_id', '=', ins_product_id)]")
    warranty_line_ids = fields.One2many(comodel_name='analytic.warranty.line', inverse_name='risk_line_id', string='Warranty')
    risk_description_ids = fields.One2many(comodel_name='analytic.description.line', inverse_name='risk_line_id', string='Risk description')
    risk_warranty_tmpl_id = fields.Many2one(comodel_name='analytic.risk.line', string='Template', domain="[('template', '=', True), ('type_risk_id', '=', type_risk_id)]")
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner')

    # TODO
    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default.update(name="%s" % (self.name or ''))
        # res = super(AroInsuranceSubscriptionRiskLine, self).copy(default)
        res = super(AnalyticRiskLine, self).copy(default)
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
        description_obj = self.env['insurance_type_risk.description']
        desc_ids = description_obj.search([('type_risk_id', '=', self.type_risk_id.id)])
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
