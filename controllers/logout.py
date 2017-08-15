# -*- coding: utf-8 -*-

from flask import session, url_for
from werkzeug.utils import redirect

from constants import OperationType
from controllers import TemplateController


class LogoutController(TemplateController):
    def __init__(self, request, manager):
        super(LogoutController, self).__init__(request, OperationType.Logout, manager)

    def _call(self):
        session.clear()
        return redirect(url_for('login', next=self.request.referrer))
