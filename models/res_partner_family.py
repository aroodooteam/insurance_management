# -*- coding: utf-8 -*-

from openerp import models, fields, api, _

class ResPartnerFamily(models.Model):

    _name = 'res.partner.family'
    _description = 'Family Partner'

    name = fields.Many2one(string='name', comodel_name='res.partner')
    type = fields.Selection(string='type', selection=[('spouse', 'Spouse'), ('child', 'Child'), ('other', 'Other')])
    partner_id = fields.Many2one(string='Parent insured', comodel_name='res.partner')
