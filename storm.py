# -*- coding:utf-8 -*-

import os
import logging

from flask import Flask
from flask_recaptcha import ReCaptcha
from flask_wtf.csrf import CsrfProtect

import config
from models import db
from utils import StructEncoder, Logger

app = Flask(__name__)

app.config.from_object('config')
app.json_encoder = StructEncoder

csrf = CsrfProtect()
csrf.init_app(app)
recaptcha = ReCaptcha(app)
recaptcha.init_app(app)

if not os.path.exists(config.LOG_TO):
    os.makedirs(config.LOG_TO)

fh = logging.FileHandler(os.path.join(config.LOG_TO, config.LOGGER.file))
fh.setLevel(config.LOGGER.level)
fh.setFormatter(config.LOGGER.formatter)

pw_fh = logging.FileHandler(os.path.join(config.LOG_TO, config.LOGGER.peewee_file))
pw_fh.setLevel(config.LOGGER.level)
pw_fh.setFormatter(config.LOGGER.formatter)

peewee_log = Logger(pw_fh, "peewee")
log = Logger(fh, "Cebero")

log.info("Storm service started!")


# This hook ensures that the connection is closed when we've finished
# processing the request.
@app.teardown_request
def _db_close(exc):
    if not db.is_closed():
        db.close()


@app.before_request
def before():
    db.connect()

import views
