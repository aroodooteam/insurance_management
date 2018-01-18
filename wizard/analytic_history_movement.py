# -*- coding: utf-8 -*-
from openerp import api, exceptions, fields, models, _


class AnalyticHistoryMovement(models.TransientModel):
    _name = 'analytic_history.movement'
    _description = 'Movement'

    name = fields.Char(string='Name', default="/")
    movement_line_ids = fields.One2many(comodel_name='analytic_history.movement.line', inverse_name='movement_id', string='Movement')


class AnalyticHistoryMovementLine(models.TransientModel):
    _name = 'analytic_history.movement.line'
    _description = 'Movement Line'

    name = fields.Char(string='Name')
    type_risk_id = fields.Many2one(comodel_name='insurance.type.risk', string='Risk')
    movement_id = fields.Many2one(comodel_name='analytic_history.movement', string='Movement')
    state = fields.Selection(selection=[('new', 'New'),('intact', 'Intact'),('updated','Updated'),('removed','Removed')], string='state')

