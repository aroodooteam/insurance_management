# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models, _
from openerp.addons.decimal_precision import decimal_precision as dp
import logging
logger = logging.getLogger(__name__)


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


    @api.model
    def update_tax_ids(self):
        acc_tx = self.env['account.tax']
        for reg_tx in self.search([]):
            if reg_tx.indice != 14.5:
                domain_tx = [('amount', '=', reg_tx.indice/100), ('description', 'ilike', 'Te-%')]
                acc_tx_ids = acc_tx.search(domain_tx)
                vals = {'tax_ids': [(6,0,tuple(acc_tx_ids.ids))]}
                reg_tx.write(vals)
            elif reg_tx.indice == 14.5:
                domain_tx = ['&',('amount', 'in', (0.045, 0.1)),'|',('description', 'ilike', 'Te-%'),('description', 'ilike', 'TACAVA-%')]
                acc_tx_ids = acc_tx.search(domain_tx)
                vals = {'tax_ids': [(6,0,tuple(acc_tx_ids.ids))]}
                reg_tx.write(vals)
