# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import Warning
import logging
logger = logging.getLogger(__name__)


class InsuranceBranch(models.Model):
    """Insurance Branch """
    _name = "insurance.branch"

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='code', required=True)
    type = fields.Selection(selection=[('V', 'Vie'), ('N', 'Non Vie')], string='Type')
    category = fields.Selection(selection=[('T', 'Terrestre'), ('M', 'Maritime'), ('V', 'Vie')], string='Category')

    _sql_constraints = [
                ('code', 'unique(code)', 'Code must be unique.'),
    ]
