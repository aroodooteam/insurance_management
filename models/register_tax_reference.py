# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models, _
from openerp.addons.decimal_precision import decimal_precision as dp


class RegisterTaxReference(models.Model):
    _name = 'reg.tax.reference'
    _description = 'Register Tax'

    name = fields.Char(string='Name')
    fiscal_code = fields.Char(string='Code')
    property_account_position = fields.Many2one(comodel_name='account.fiscal.position', string='Fiscal Position')
    indice = fields.Float(string='Indice', digits_compute=dp.get_precision('Account'))
    tax_id = fields.Many2one(comodel_name='account.tax', string='Register tax')
    tax_ids = fields.Many2many(comodel_name='account.tax', string='Register Tax')
    date_start = fields.Date(string='Start')
    date_end = fields.Date(string='End')
