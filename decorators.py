# -*- coding:utf-8 -*-

from functools import wraps

from flask import session, request, redirect, url_for, flash, g

from config import ADMINS


def get_manager():
    manager_id = session.get("manager_id")
    if not manager_id:
        return None

    manager = ADMINS.get(int(manager_id), None)
    return manager


def logout():
    session.clear()


def is_valid_session_ip():
    return session.get("ip") == request.remote_addr


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        manager = get_manager()
        if not manager:
            return redirect(url_for('login', next=request.path))

        if not is_valid_session_ip():
            logout()
            flash(u"Ваша сессия устарела")
            return redirect(url_for('login', next=request.path))

        g.manager = manager
        return f(manager, *args, **kwargs)

    return decorated_function
