# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models, _


class RiskWarrantyLine(models.Model):
    _name = 'risk.warranty.line'
    _description = 'Risk detail in subscription'

    name = fields.Char(string='Description')
    history_risk_line_id = fields.Many2one(
        comodel_name='analytic_history.risk.line', string='Risk type')
    type_risk_id = fields.Many2one(
        comodel_name='insurance.type.risk', string='Type Risk',
        related='history_risk_line_id.type_risk_id')
    warranty_id = fields.Many2one(
        comodel_name='product.product', string='Warranty',
        domain="[('type_risk_id', '=', type_risk_id),('is_warranty', '=', True)]")

    @api.onchange('warranty_id')
    def onchange_warranty(self):
        if not self.warranty_id:
            return False
        else:
            self.name = self.warranty_id.name
