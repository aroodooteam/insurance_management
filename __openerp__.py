# -*- coding: utf-8 -*-

{
    "name": "Insurance Management",
    "version": "0.1",
    "author": "Haritiana Rakotomalala <hmrakotomalala@aro.mg>",
    "category": "Tools",
    "complexity": "normal",
    "data": [
        # "data/templates.xml", # un comment to enable js, css code
        "data/insurance_branch_data.xml",
        "data/insurance_fraction_data.xml",
        "data/insurance_product_data.xml",
        # "security/security.xml",
        # "security/ir.model.access.csv",
        "views/product_template_view.xml",
        "views/insurance_branch_view.xml",
        "views/insurance_fraction_view.xml",
        "views/account_analytic_account_view.xml",
        "views/account_analytic_account_warranty_view.xml",
        # "actions/act_window.xml",
        "views/menu.xml",
        "views/insurance_product_view.xml",
        # "data/data.xml",
    ],
    "depends": [
        "base",
        "account",
        "account_analytic_analysis",
    ],
    "qweb": [
        # "static/src/xml/*.xml",
    ],
    "installable": True,
    "auto_install": False,
}
