# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models, _


class InsuranceTypeRiskClause(models.Model):
    _name = 'insurance_type_risk.clause'
    _description = 'Clause of insurance type of risk'
    _order = "name asc"

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Clause description')
    type_risk_id = fields.Many2one(comodel_name='insurance.type.risk',
                                     string='Type of risk')
