# -*- coding: utf-8 -*-
from openerp import api, exceptions, fields, models, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.v7
    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        res = super(SaleOrderLine, self)._prepare_order_line_invoice_line(cr, uid, line, account_id, context)
        if line.order_id.amount_total < 0:
            res['price_unit'] = (-1) * res['price_unit']
        return res


