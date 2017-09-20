# -*- coding:utf-8 -*-

import traceback
from functools import wraps
from datetime import datetime

from flask import jsonify, request, render_template, get_flashed_messages

from storm import app, log
from utils import get_request_data
from decorators import login_required
from models import ErrorLog, ClientLog
from controllers.bid import BidController
from controllers.pay import PayController
from controllers.index import IndexController
from controllers.login import LoginController
from controllers.logout import LogoutController
from controllers.manage_bids import (BidViewController, EditBidController, GeneratePayUrlController)
from controllers.support import SendSupportMessageController


def jsonify_result(func):
    @wraps(func)
    def wrapper(*args, **kwds):
        result = func(*args, **kwds)
        return jsonify(result)

    return wrapper


@app.route("/alive")
def alive():
    return "I'm alive"


@app.route("/")
def index():
    return IndexController(request).call()


@app.route("/bid", methods=["GET", "POST"])
@app.route("/bid/<int:service_id>", methods=["GET", "POST"])
def bid(service_id=None):
    return BidController(request).call(service_id)


@app.route("/support/send_message", methods=["POST"])
def send_support_message():
    return SendSupportMessageController(request).call()


@app.route("/error")
def common_error():
    return render_template("error.html", messages=get_flashed_messages())


@app.route("/pay/<bid_id>", methods=["GET"])
def pay(bid_id):
    return PayController(request).call(bid_id)


@app.route("/xdoor/bids", methods=["GET", "POST"])
@login_required
def bids(manager):
    return BidViewController(request, manager).call()


@app.route("/xdoor/bids/edit", methods=["GET", "POST"])
@login_required
def edit_bid(manager):
    return EditBidController(request, manager).call()


@app.route("/xdoor/login", methods=["GET", "POST"])
def login():
    return LoginController(request).call()


@app.route("/xdoor/logout")
@login_required
def logout(manager):
    return LogoutController(request, manager).call()


@app.route("/xdoor/pay_url", methods=["POST"])
@jsonify_result
@login_required
def generate_pay_url(manager):
    return GeneratePayUrlController(request, manager).call()


@app.route("/logs/<log_type>")
@jsonify_result
def logs(log_type):
    log_types = {'client': ClientLog, 'error': ErrorLog}
    model = log_types[log_type]
    return {"logs": [l.to_dict() for l in model.select().order_by(model.id.desc())]}


@app.errorhandler(404)
@app.errorhandler(405)
@app.errorhandler(500)
def handle_http_error(error):
    db_error = ErrorLog.create(
        error=error,
        request_ip=request.remote_addr,
        request_url=request.url,
        request_headers=request.headers,
        request_method=request.method,
        request_data=get_request_data(request),
        traceback=traceback.format_exc(),
        finished=datetime.now()
    )
    log.exception("Error for request => url: %s, data: %s, ip: %s, method: %s"
                  % (db_error.request_url,
                     db_error.request_data,
                     db_error.request_ip,
                     db_error.request_method))
    return str(error), error.code if hasattr(error, "code") else 500


@app.errorhandler(Exception)
def handle_exception(error):
    db_error = ErrorLog.create(
        error=error,
        request_ip=request.remote_addr,
        request_url=request.url,
        request_headers=request.headers,
        request_method=request.method,
        request_data=get_request_data(request),
        traceback=traceback.format_exc(),
        finished=datetime.now()
    )
    log.exception("Error for request => url: %s, data: %s, ip: %s, method: %s"
                  % (db_error.request_url,
                     db_error.request_data,
                     db_error.request_ip,
                     db_error.request_method))
    return error.message, 500
