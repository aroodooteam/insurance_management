# -*- coding: utf-8 -*-


from openerp import api, exceptions, fields, models, _


class RiskDescriptionLine(models.Model):
    _name = 'risk.description.line'
    _description = 'Value corresponding to each risk description'

    name = fields.Char(string='Item')
    code = fields.Char(string='Code')
    value = fields.Char(string='Value')
    history_risk_line_id = fields.Many2one(comodel_name='analytic_history.risk.line', string='Risk line')

    _order = 'code asc'
