# -*- coding:utf-8 -*-

from functools import wraps

from flask import jsonify

from storm import app


def jsonify_result(func):
    @wraps(func)
    def wrapper(*args, **kwds):
        result = func(*args, **kwds)
        return jsonify(result)

    return wrapper


@app.route("/alive")
def alive():
    return "I'm alive"

