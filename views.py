# -*- coding:utf-8 -*-

import traceback
from functools import wraps
from datetime import datetime

from flask import jsonify, request, render_template, get_flashed_messages

from storm import app, log
from models import ClientLog
from utils import get_request_data
from controllers.bid import BidController
from controllers.pay import PayController
from controllers.index import IndexController
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
def bid():
    return BidController(request).call()


@app.route("/support/send_message")
def send_support_message():
    return SendSupportMessageController(request).call()


@app.route("/error")
def common_error():
    return render_template("error.html", messages=get_flashed_messages())


@app.route("/pay", methods=["GET", "POST"])
def pay():
    return PayController(request).call()


@app.route("/logs/client_logs")
@jsonify_result
def logs():
    return {"logs": [l.to_dict() for l in ClientLog.select().order_by(ClientLog.id.desc())]}


@app.errorhandler(404)
@app.errorhandler(405)
@app.errorhandler(500)
def handle_http_error(error):
    db_error = ClientLog.create(
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
    db_error = ClientLog.create(
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
