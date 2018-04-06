# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models, _

class AnalyticProdLines(models.Model):
    _name = 'analytic.prod.lines'
    _description = 'Invoices for each version of contract is generated from this model'

    name = fields.Char(string='Description')
    product_id = fields.Many2one(comodel_name='product.product', string='Product')
    amount = fields.Float(string='Amount')
    date = fields.Date(string='Date')
    journal_id = fields.Many2one(comodel_name='account.analytic.journal', string='Analytic Journal')
    analytic_id = fields.Many2one(comodel_name='account.analytic.account', string='Analytic', help='Version')
    account_id = fields.Many2one(comodel_name='account.account', string='Account')
