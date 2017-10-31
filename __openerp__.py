# -*- coding: utf-8 -*-

{
    "name": "Insurance Management",
    "version": "0.1",
    "author": "Haritiana Rakotomalala <hmrakotomalala@aro.mg>",
    "category": "Tools",
    "complexity": "normal",
    "data": [
        # "data/templates.xml", # un comment to enable js, css code
        'security/ir.model.access.csv',
        "data/insurance_branch_data.xml",
        "data/insurance_fraction_data.xml",
        "data/insurance_product_data.xml",
        "data/insurance_type_risk_data.xml",
        "data/insurance_type_risk_description_data.xml",
        "data/insurance_type_risk_clause_data.xml",
        "data/analytic_history_stage_data.xml",
        "data/product_template_data.xml",
        # "security/security.xml",
        # "security/ir.model.access.csv",
        "views/menu.xml",
        "views/product_template_view.xml",
        "views/insurance_branch_view.xml",
        "views/insurance_fraction_view.xml",
        "views/insurance_type_risk_view.xml",
        "views/insurance_type_risk_description_view.xml",
        "views/insurance_type_risk_clause_view.xml",
        "views/analytic_history_view.xml",
        "views/account_analytic_account_view.xml",
        "views/account_analytic_account_warranty_view.xml",
        # "actions/act_window.xml",
        "views/insurance_product_view.xml",
        # "data/data.xml",
        "views/analytic_history_wiz_view.xml",
        "views/website_templates.xml",
    ],
    "depends": [
        "base",
        "account",
        "web", "website",
        "account_analytic_analysis",
    ],
    "qweb": [
        # "static/src/xml/*.xml",
    ],
    "installable": True,
    "auto_install": False,
}
