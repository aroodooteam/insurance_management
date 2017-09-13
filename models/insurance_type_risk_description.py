# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models, _


class InsuranceTypeRiskDescription(models.Model):
    _name = 'insurance_type_risk.description'
    _description = 'Description of insurance type of risk'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    type_risk_id = fields.Many2one(
        comodel_name='insurance.type.risk', string='Type of risk')
