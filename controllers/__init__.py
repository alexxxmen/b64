# -*- coding:utf-8 -*-

import re
import datetime
import traceback

from flask import flash, redirect, url_for

from storm import fh
from models import ClientLog
from utils import Logger, get_request_data, Struct


class ServiceException(Exception):
    def __init__(self, message, user_message=None):
        super(ServiceException, self).__init__()
        self.user_message = user_message or message
        self.message = message


class BaseController(object):
    def __init__(self, request):
        self.class_name = self.__class__.__name__
        self.log = Logger(fh, self.class_name)
        self.request = request
        self.error_view = request.full_path
        self.db_logger = ClientLog(request_ip=request.remote_addr,
                                   request_url=request.url,
                                   request_headers=request.headers,
                                   request_method=self.request.method,
                                   request_data=get_request_data(self.request))
        self.need_log = True

    def _call(self, *args, **kwds):
        raise NotImplementedError("%s._call" % self.class_name)

    def _verify_post_request(self, requires):
        request_data = get_request_data(self.request)
        for r in requires:
            if r not in request_data:
                raise ServiceException("Invalid request, '%s' is required" % r)

        return Struct(**request_data)

    def _verify_email(self, email):
        email = email.strip().lower()
        if not email:
            raise ServiceException("Email field is empty", u"Пожалуйста укажите свой email")

        if not re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email):
            raise ServiceException("Email does not match the regular expression (%s)" % email,
                                   u"Пожалуйста укажите корректный email")
        elif len(email) > 65:
            raise ServiceException("Unable registration. Email is to long.",
                                   u"Email не должен превышать 65 символов")
        return email



class TemplateController(BaseController):
    def call(self, *args, **kwds):
        result = None
        try:
            self.log.debug("Started process request: %s" % get_request_data(self.request))
            data = self._call(*args, **kwds)
            self.log.debug("Finished")
            result = data
        except ServiceException as ex:
            self.db_logger.error = ex.message
            self.log.warn(ex.message)
            flash(ex.user_message)
            result = redirect(self.error_view)

        except Exception as ex:
            self.db_logger.error = ex.message
            self.db_logger.traceback = traceback.format_exc()
            self.log.exception("Error during %s call" % self.class_name)
            flash(ex.message)
            result = redirect(url_for("common_error"))

        finally:
            if self.need_log or self.db_logger.error:
                self.db_logger.finished = datetime.datetime.now()
                self.db_logger.save()
            return result
