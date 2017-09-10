# -*- coding:utf-8 -*-

from flask import render_template

from config import PAY_URL, SHOP_ID
from constants import OperationType
from controllers import TemplateController, ServiceException, BidIDCoder


class PayController(TemplateController):
    def __init__(self, request):
        super(PayController, self).__init__(request, OperationType.Pay)

    def _call(self, encoded_id):
        try:
            bid_id = BidIDCoder().decode(encoded_id)
        except ValueError:
            self.log.exception("Error during decode bid_id")
            raise ServiceException("Invalid encoded_id=%s" % encoded_id, u"Неверный url")

        bid = self._verify_bid(bid_id)

        data = dict(
            url=PAY_URL,
            shop_id=SHOP_ID,
            partner_invoice_id=bid.id,
            amount=bid.amount,
            sign='',  # todo generate
            description=u"Оплата заявки № %s" % bid.id,
        )
        return render_template('pay/pay.html', data=data)
