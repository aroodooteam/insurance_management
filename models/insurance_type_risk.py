# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models, _


class InsuranceTypeRisk(models.Model):
    _name = 'insurance.type.risk'
    _description = 'Insurance type of risk'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    ins_product_id = fields.Many2one(
        string='Insurance Product', required=True,
        comodel_name='insurance.product')
    fiscal_code = fields.Char(string='Fiscal code')
