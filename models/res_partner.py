# -*- coding: utf-8 -*-

from openerp import models, api, fields, exceptions


class ResPartner(models.Model):
    _inherit = 'res.partner'

    family_ids = fields.One2many(string='family', comodel_name='res.partner.family', inverse_name='partner_id')
    is_broker = fields.Boolean(string='Broker')
    # broker_agency_id = fields.Many2one(related='partner_id.agency_id', inherited=True)
    is_under_agency = fields.Boolean(string='Under Agency')
    # title = fields.Many2one(related='partner_id.title', inherited=True)
    ap_code = fields.Char(string='AP code', size=8)
    serial_identification = fields.Char(string='Serial Id', size=8)
    statut = fields.Char(string='Statut', size=16)
    ua_code = fields.Char(string='UA Code', size=16)
    ref_apporteur = fields.Char(string='Reference', size=16)
    account_charge_vie_id = fields.Many2one('account.account', string='Expense Account Life')
    account_charge_id = fields.Many2one('account.account', string='Expense Account')
