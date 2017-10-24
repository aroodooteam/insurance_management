# -*- coding: utf-8 -*-


from openerp import api, exceptions, fields, models, _


class AnalyticDescriptionLine(models.Model):
    _name = 'analytic.description.line'
    _description = 'Value corresponding to each risk description'

    name = fields.Char(string='Item')
    code = fields.Char(string='Code')
    value = fields.Char(string='Value')
    risk_line_id = fields.Many2one(comodel_name='analytic.risk.line', string='Risk line')