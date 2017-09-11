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

    # type_risque_id = fields.Many2one(comodel_name='aro.type.risque',
    #                                  string='Type of risk', required=False)
    # product_insurance_id = fields.Many2one(comodel_name='aro.produit.assurance', string='Insurance Product', related='type_risque_id.produit_assurance_id', store=True)
    # branch_insurance_id = fields.Many2one(comodel_name='aro.branche.assurance', string='Insurance Product', related='type_risque_id.produit_assurance_id.branche_assurance_id', store=True)
    # branch_categ = fields.Selection(related='branch_insurance_id.category', string='Branch Category', store=True)
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
