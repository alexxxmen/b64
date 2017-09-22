# -*- coding:utf-8 -*-

from flask import render_template

from models import Bid
from config import TELEGRAM_MANAGER_IDS
from constants import OperationType, Services
from controllers import TemplateController, ServiceException


class BidController(TemplateController):
    def __init__(self, request):
        super(BidController, self).__init__(request, OperationType.CreateBid)

    def _call(self, service_id):
        services = Services.to_dict()
        if self.request.method == 'GET':
            service_id = self._verify_service(services, service_id) if service_id else Services.Basic
            return render_template("bid/bid.html", service_id=service_id, services=services)

        self.error_view = self.request.full_path
        self._verify_recaptcha()
        form_data = self._verify_post_request(("name", "email"))
        name = form_data.name
        email = self._verify_email(form_data.email)
        account = form_data.get("account", None)
        if account:
            account = account

        form_service = self._verify_service(services, form_data.service)
        bid = Bid.new(name, email, account, form_service)
        self.db_logger.bid = bid.id

        without_inform = []
        msg = u"New bid #{id}\nName: {name}\nEmail: {email}\nInstagram account: {account}\nService: {service}".format(
            id=bid.id,
            name=bid.name,
            email=bid.email,
            account=bid.account or '',
            service=Services.get_desc(int(form_service))
        )
        for t_id in TELEGRAM_MANAGER_IDS:
            r = self._send_inform_message(t_id, msg)
            if not r:
                without_inform.append(t_id)

        if without_inform:
            self._send_email("Didn't send telegram msg to %s" % without_inform)

        return render_template("bid/success_bid.html", bid=bid)

    def _verify_service(self, services, service_id):
        if not service_id or not services.get(int(service_id)):
            raise ServiceException("Unable add bid. Invalid service_id=%s" % service_id, u"Выберите услугу")
        return int(service_id)
