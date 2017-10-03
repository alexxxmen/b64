# -*- coding:utf-8 -*-

import hashlib
from flask import render_template

from config import PAY_URL, SHOP_ID, SHOP_SECRET
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
            shop_invoice_id=bid.id,
            amount=bid.amount,
            description=u"Оплата заявки № %s" % bid.id,
            currency=840
        )
        data['sign'] = self._get_sign(data, ("shop_id", "shop_invoice_id", "amount", "currency"), SHOP_SECRET)
        return render_template('pay/pay.html', data=data)

    def _get_sign(self, request, keys_required, secret):
        keys_sorted = sorted(keys_required)
        string_to_sign = ":".join([unicode(request[k]).encode("utf8") for k in keys_sorted]) + secret
        return hashlib.md5(string_to_sign).hexdigest()
