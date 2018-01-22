# -*- coding: utf-8 -*-
from openerp import api, exceptions, fields, models, _
import openerp.addons.decimal_precision as dp


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
    movement_warranty_ids = fields.One2many(comodel_name='movement.warranty.line', inverse_name='movement_line_id', string='Warranty')


class MovementWarrantyLine(models.TransientModel):
    _name = 'movement.warranty.line'
    _description = 'Difference in warranty for each risk'

    name = fields.Char(string='Description')
    movement_line_id = fields.Many2one(
        comodel_name='analytic_history.movement.line', string='Lines')
    # type_risk_id = fields.Many2one(
        # comodel_name='insurance.type.risk', string='Type Risk',
        # related='history_risk_line_id.type_risk_id')
    warranty_id = fields.Many2one(
        comodel_name='product.product', string='Warranty',
        domain="[('type_risk_id', '=', type_risk_id),('is_warranty', '=', True)]",
        required=False
    )
    yearly_net_amount = fields.Float(string='Yearly Net', digits_compute=dp.get_precision('Account'), help='Yearly net amount')
    proratee_net_amount = fields.Float(string='Proratee Net', digits_compute=dp.get_precision('Account'), help='Proratee net amount')
    invoiced = fields.Boolean(string='Invoiced', help='This field is checked if this warranty is invoiced allready')
    state = fields.Selection(selection=[('new', 'New'),('intact', 'Intact'),('updated','Updated'),('removed','Removed')], string='state')
