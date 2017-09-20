# -*- coding:utf-8 -*-

from flask import redirect, url_for, flash

from constants import OperationType
from config import TELEGRAM_MANAGER_IDS
from controllers import TemplateController, ServiceException


class SendSupportMessageController(TemplateController):
    request_required = ("name", "email", "message")

    def __init__(self, request):
        super(SendSupportMessageController, self).__init__(request, OperationType.SupportMessage)

    def _call(self):
        form_data = self._verify_post_request(self.request_required)
        name = self._verify_form_name(form_data.name)
        email = self._verify_form_email(form_data.email)
        message = self._verify_form_message(form_data.message)

        telegram_msg = u"New support message:\nName: %s \nEmail: %s\nMessage: %s" % (name, email, message)
        for t_id in TELEGRAM_MANAGER_IDS:
            self._send_inform_message(t_id, telegram_msg)

        return redirect(url_for('index'))

    def _verify_form_name(self, name):
        if not name:
            raise ServiceException("name is required")

        return name

    def _verify_form_email(self, email):
        if not email:
            raise ServiceException("email is required")

        return email

    def _verify_form_message(self, msg):
        if not msg:
            raise ServiceException("message is required")

        return msg
