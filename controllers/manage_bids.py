# -*- coding:utf-8 -*-

from datetime import datetime

from flask import render_template, flash, url_for

from models import Bid
from utils import format_datetime
from constants import OperationType, BidStatus
from controllers import TemplateController, ServiceException, JsonController, BidIDCoder


class BidViewController(TemplateController):
    def __init__(self, request, manager):
        super(BidViewController, self).__init__(request, OperationType.ViewBid, manager)

    def _call(self):
        if self.request.method == 'GET':
            return render_template("bid/view_bid.html")

        self.error_view = self.request.full_path
        form_data = self._verify_post_request(("bid",))
        bid = self._verify_bid(form_data.bid)
        statuses = BidStatus.to_dict()

        data = self._prepare_data(bid)
        return render_template("bid/bid_preview.html", bid=data, statuses=statuses)

    def _verify_bid(self, bid_id):
        if not bid_id:
            raise ServiceException("'bid' is required", u"Введите id заявки")

        if not str(bid_id).isdigit():
            raise ServiceException("Invalid 'bid=%s'" % bid_id, u"Некорректный номер заявки")

        bid = Bid.get_by_id(int(bid_id))
        if not bid:
            raise ServiceException("Bid (id=%s) doesn't exist" % bid_id,
                                   u"Заявка под номером = %s не существует" % bid_id)
        return bid

    def _prepare_data(self, bid):
        bid.status_alias = BidStatus.get_desc(bid.status)
        bid.created = format_datetime(bid.created)
        bid.updated = format_datetime(bid.updated)
        return bid


class EditBidController(TemplateController):
    def __init__(self, request, manager):
        super(EditBidController, self).__init__(request, OperationType.EditBid, manager)
        self.error_view = url_for('bids')

    def _call(self):
        form_data = self._verify_post_request(("bid", "amount", "status", "account"))
        bid = self._verify_bid(form_data.bid)
        amount = self._verify_form_amount(form_data.amount)
        status = self._verify_form_status(form_data.status)
        account = self._verify_form_account(form_data.account)

        bid.account = account or bid.account
        bid.amount = amount or bid.amount
        bid.status = status or bid.status
        bid.updated = datetime.now()
        bid.save()

        statuses = BidStatus.to_dict()
        data = self._prepare_data(bid)

        flash(u"Заявка %s успешно сохранена" % bid.id)
        return render_template("bid/bid_preview.html", bid=data, statuses=statuses)

    def _verify_form_amount(self, amount):
        if not amount:
            return None

        try:
            float(amount)
        except Exception:
            raise ServiceException("Invalid amount format=%s" % amount)

        return float(amount)

    def _verify_form_status(self, status):
        if not status:
            return None

        if int(status) not in BidStatus.to_dict():
            raise ServiceException("Invalid bid status=%s" % status)

        return int(status)

    def _verify_bid(self, bid_id):
        if not bid_id:
            raise ServiceException("'bid' is required")

        if not str(bid_id).isdigit():
            raise ServiceException("Invalid 'bid=%s'" % bid_id)

        bid = Bid.get_by_id(int(bid_id))
        if not bid:
            raise ServiceException("Bid (id=%s) doesn't exist" % bid_id)

        return bid

    def _verify_form_account(self, account):
        return account or None

    def _prepare_data(self, bid):
        bid.status_alias = BidStatus.get_desc(bid.status)
        bid.created = format_datetime(bid.created)
        bid.updated = format_datetime(bid.updated)
        return bid


class GeneratePayUrlController(JsonController):
    request_required = ("bid_id",)

    def __init__(self, request, manager):
        super(GeneratePayUrlController, self).__init__(request, OperationType.Pay, manager)

    def _call(self):
        form_data = self._verify_post_request(self.request_required)

        bid = self._verify_bid(form_data.bid_id)
        if bid.status != BidStatus.WaitingPayment:
            raise ServiceException("Incorrect Bid status = %s, expected = %s" %
                                   (bid.status, BidStatus.WaitingPayment))
        encoded_id = BidIDCoder().encode_bid_id(bid.id)
        return {'url': url_for('pay', bid_id=encoded_id, _external=True)}
