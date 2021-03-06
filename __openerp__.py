# -*- coding: utf-8 -*-

{
    "name": 'Insurance Management',
    "version": "0.1",
    "depends": [
        'account',
        'account_journal_agency',
        'analytic',
        'aro_custom_v8',
        'base',
        'insurance_setup',
        'product',
        'sale',
    ],
    "author": "Haritiana Rakotomalala <hmrakotomalala@aro.mg>",
    "category": "Tools",
    "installable": True,
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/insurance_branch_data.xml',
        'data/insurance_fraction_data.xml',
        'data/insurance_product_data.xml',
        'data/insurance_type_risk_data.xml',
        'data/insurance_type_risk_description_data.xml',
        'data/insurance_type_risk_clause_data.xml',
        'data/analytic_history_stage_data.xml',
        'data/product_template_data.xml',
        'views/menu.xml',
        'views/product_template_view.xml',
        'views/insurance_branch_view.xml',
        'views/insurance_fraction_view.xml',
        'views/analytic_history_stage_view.xml',
        'views/insurance_type_risk_view.xml',
        'views/insurance_type_risk_description_view.xml',
        'views/insurance_type_risk_clause_view.xml',
        'views/analytic_history_view.xml',
        'views/account_analytic_account_view.xml',
        'views/insurance_product_view.xml',
        'views/analytic_history_wiz_view.xml',
        'views/res_partner_family_view.xml',
        'views/res_partner_view.xml',
        'data/account_fiscal_position.xml',
        'views/register_tax_reference_view.xml',
        'data/register_tax_reference.xml',
        'views/account_invoice_view.xml',
        'data/ir_sequence_type_data.xml',
        'data/ir_sequence_data.xml',
        'wizard/analytic_history_movement_view.xml',
    ],
}
