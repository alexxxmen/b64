# -*- coding:utf-8 -*-

from flask import render_template

from models import Bid
from storm import recaptcha
from constants import OperationType
from config import TELEGRAM_MANAGER_IDS
from controllers import TemplateController, IncorrectCaptchaException


class BidController(TemplateController):
    def __init__(self, request):
        super(BidController, self).__init__(request, OperationType.CreateBid)

    def _call(self):
        if self.request.method == 'GET':
            return render_template("bid/bid.html")

        self.error_view = self.request.full_path
        self._verify_recaptcha()
        form_data = self._verify_post_request(("name", "email"))
        name = form_data.name
        email = self._verify_email(form_data.email)
        account = form_data.get("account", None)

        bid = Bid.new(name, email, account)
        self.db_logger.bid = bid.id

        without_inform = []
        msg = "New bid #{id}\nName: {name}\nEmail: {email}\nInstaram account: {account}\n".format(
            id=bid.id, name=bid.name, email=bid.email, account=bid.account or ''
        )
        for t_id in TELEGRAM_MANAGER_IDS:
            r = self._send_inform_message(t_id, msg)
            if not r:
                without_inform.append(t_id)

        if without_inform:
            self._send_email("Didn't send telegram msg to %s" % without_inform)

        return render_template("bid/success_bid.html", bid=bid)

    def _verify_recaptcha(self):
        if not recaptcha.verify():
            raise IncorrectCaptchaException("Recaptcha verification failed")
