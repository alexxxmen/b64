# -*- coding:utf-8 -*-

from flask import url_for, render_template

from models import Bid
from constants import BidStatus
from controllers import TemplateController, ServiceException


class PayController(TemplateController):
    def __init__(self, request):
        super(PayController, self).__init__(request)
        self.error_view = url_for("common_error")

    def _call(self):
        if self.request.method == 'GET':
            return render_template("pay/pay.html")

        self.error_view = self.request.full_path
        form_data = self._verify_post_request(("bid", "email"))
        email = self._verify_email(form_data.email)
        bid = self._verify_bid(form_data.bid, email)
        # todo generate url for tip service
        pay_url = ''
        return render_template("pay/pay_confirm.html", bid=bid, pay_url=pay_url)

    def _verify_bid(self, bid_id, email):
        if not str(bid_id).isdigit():
            raise ServiceException("Invalid bid_id = '%s'" % bid_id, u"Неверный номер заявки")

        bid = Bid.get_by_id(int(bid_id))
        if not bid:
            raise ServiceException("Bid (id=%s) doesn't exist" % bid_id,
                                   u"Заявка с такими данными не существует")

        if bid.email != email:
            raise ServiceException("Bid (id=%s) with email=%s doesn't exist" % (bid_id, email),
                                   u"Заявка с такими данными не существует")

        if bid.status != BidStatus.Verified:
            raise ServiceException("Bid (id=%s) doesn't verified" % bid_id,
                                   u"Заявка проверяется менеджером. "
                                   u"Попробуйте еще раз через некоторое время или обратитесь в службу поддержки.")

        return bid
