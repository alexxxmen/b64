# -*- coding:utf-8 -*-

from flask import redirect, url_for, flash

from constants import OperationType
from controllers import TemplateController


class SendSupportMessageController(TemplateController):
    def __init__(self, request):
        super(SendSupportMessageController, self).__init__(request, OperationType.SupportMessage)

    def _call(self):
        # todo send telegram msg to admin chat
        flash(u"Сообщение отправлено в службу поддержки.")
        return redirect(url_for('index'))
