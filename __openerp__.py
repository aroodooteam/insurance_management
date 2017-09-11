# -*- coding: utf-8 -*-

{
    "name": "Insurance Management",
    "version": "0.1",
    "author": "Haritiana Rakotomalala <hmrakotomalala@aro.mg>",
    "category": "Tools",
    "complexity": "normal",
    "data": [
        # "data/templates.xml", # un comment to enable js, css code
        # "security/security.xml",
        # "security/ir.model.access.csv",
        "views/product_template_view.xml",
        "views/insurance_branch_view.xml",
        # "actions/act_window.xml",
        "views/menu.xml",
        # "data/data.xml",
    ],
    "depends": [
        "base",
        "account_analytic_analysis"
    ],
    "qweb": [
        # "static/src/xml/*.xml",
    ],
    "installable": True,
    "auto_install": False,
}
