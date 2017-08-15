# -*- coding:utf-8 -*-

from flask import render_template, url_for

from models import Bid
from constants import OperationType
from controllers import TemplateController


class BidController(TemplateController):
    def __init__(self, request):
        super(BidController, self).__init__(request, OperationType.CreateBid)

    def _call(self):
        if self.request.method == 'GET':
            return render_template("bid/bid.html")

        self.error_view = self.request.full_path
        form_data = self._verify_post_request(("name", "email"))
        name = form_data.name
        email = self._verify_email(form_data.email)
        account = form_data.get("account", None)

        bid = Bid.new(name, email, account)
        self.db_logger.bid = bid.id
        # todo add send telegram msg with bid info
        return render_template("bid/success_bid.html", bid=bid)
