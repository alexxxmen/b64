# -*- coding:utf-8 -*-

import hashlib

from flask import redirect, render_template, url_for, session

from config import MANAGERS
from decorators import get_manager
from constants import OperationType
from controllers import TemplateController, ServiceException


class LoginController(TemplateController):
    def __init__(self, request):
        super(LoginController, self).__init__(request, OperationType.Login)
        self.confidential_fields = ('password',)

    def _call(self):
        if self.request.method == "GET":
            if get_manager():
                return redirect(url_for("index"))
            return render_template("login.html", next=self.request.args.get("next"))

        self.error_view = self.request.full_path
        self._verify_recaptcha()
        form_data = self._verify_post_request(('password', 'login'))
        manager = self._verify_manager(form_data.login)
        self._check_hashed_password(manager, form_data.password)

        self._login_manager(manager)
        next_ = self.request.args.get('next', url_for('index'))
        return redirect(next_)

    def _verify_manager(self, login):
        for aid, acc in MANAGERS.items():
            if acc['login'] == login:
                return dict(id=aid, login=acc['login'], password=acc['password'])
        raise ServiceException("Manager with login=%s doesn't exist", u"Неверный Логин или Пароль.")

    def _check_hashed_password(self, manager, passwd):
        hashed_passwd = hashlib.sha256('%s%s' % (manager['login'], passwd.encode('utf-8'))).hexdigest()
        if hashed_passwd != manager['password']:
            raise ServiceException("Invalid password", u"Неверный Логин или Пароль.")

    def _login_manager(self, manager):
        session["manager_id"] = manager['id']
        session['ip'] = self.request.remote_addr
