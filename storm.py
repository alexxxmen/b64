# -*- coding:utf-8 -*-

import os
import logging

from flask import Flask

import config
from utils import StructEncoder, Logger

app = Flask(__name__)

app.config.from_object('config')
app.json_encoder = StructEncoder

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

import views
