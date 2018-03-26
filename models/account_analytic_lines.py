# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models, _
from openerp.addons.decimal_precision import decimal_precision as dp


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    history_id = fields.Many2one(comodel_name='analytic.history', string='History')
    hist_id = fields.Many2one(comodel_name='account.analytic.account', string='History')
    amount_to_invoice = fields.Float(string='Amount to invoice', digits_compute=dp.get_precision('Account'))
