# -*- coding:utf-8 -*-

from storm import app


@app.route("/alive")
def alive():
    return "I'm alive"

