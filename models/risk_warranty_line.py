# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models, _
import openerp.addons.decimal_precision as dp


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
        domain="[('type_risk_id', '=', type_risk_id),('is_warranty', '=', True)]",
        required=False
    )
    yearly_net_amount = fields.Float(string='Yearly Net', digits_compute=dp.get_precision('Account'), help='Yearly net amount')
    proratee_net_amount = fields.Float(string='Proratee Net', digits_compute=dp.get_precision('Account'), help='Proratee net amount')
    invoiced = fields.Boolean(string='Invoiced', help='This field is checked if this warranty is invoiced allready')
    parent_id = fields.Many2one(comodel_name='risk.warranty.line', string='Parent')

    # TODO
    # 1- Get yearly_net_amount value in onchange_warranty
    # 2- Get proratee_net_amount value in onchange_warranty
    @api.onchange('warranty_id')
    def onchange_warranty(self):
        if not self.warranty_id:
            return False
        else:
            self.name = self.warranty_id.name
