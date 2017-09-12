# -*- coding: utf-8 -*-

from openerp import api, fields, models
import logging
logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    commissionable = fields.Boolean(
        string='Commissionable',
        help='Check if this product is commissionable')

    is_warranty = fields.Boolean(
        string='Is warranty',
        help='Check if this product is an warranty')

    type_risk_id = fields.Many2one(
        comodel_name='insurance.type.risk', string='Type of risk', required=False)
    ins_product_id = fields.Many2one(comodel_name='insurance.product', string='Insurance Product', related='type_risk_id.ins_product_id', store=True)
    branch_id = fields.Many2one(comodel_name='insurance.branch', string='Insurance Product', related='type_risk_id.ins_product_id.branch_id', store=True)
    branch_categ = fields.Selection(related='branch_id.category', string='Branch Category', store=True)
    # aro_taxe_ids = fields.One2many(
    #     comodel_name='aro.taxe', inverse_name='product_id',
    #     string='Aro tax', help='Aro special tax')

    # registration_fee = fields.Char(
    #     string='Registration fee',
    #     required=False
    # )

    @api.model
    def update_property_income(self):
        account_obj = self.env['account.account']
        ter_account_id = account_obj.search([('code', '=', '702101')])
        mar_account_id = account_obj.search([('code', '=', '702102')])
        for warranty in self.search([('is_warranty', '=', True)]):
            if warranty.branch_categ == 'T':
                warranty.write({'property_account_income': ter_account_id.id})
            elif warranty.branch_categ == 'M':
                warranty.write({'property_account_income': mar_account_id.id})
