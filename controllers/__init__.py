# -*- coding:utf-8 -*-

import re
import math
import urllib
import random
import requests
import datetime
import traceback

from flask import flash, redirect, url_for

from storm import fh, mail, recaptcha
from config import ENCODE_NUM, TELEGRAM_BOT_TOKEN as bot_token, TELEGRAM_BOT_URL as bot_api_url
from models import ClientLog, ErrorLog, Bid
from utils import Logger, get_request_data, Struct


class ServiceException(Exception):
    def __init__(self, message, user_message=None):
        super(ServiceException, self).__init__()
        self.user_message = user_message or message
        self.message = message


class IncorrectCaptchaException(Exception):
    def __init__(self, message):
        super(IncorrectCaptchaException, self).__init__()
        self.message = message


class ControllerResult(Struct):
    def __init__(self, result=True, data=None, message="Ok", error=None):
        self.result = result
        self.data = data
        self.message = message
        self.error = error


class BaseController(object):
    def __init__(self, request, operation_type, manager=None):
        self.class_name = self.__class__.__name__
        self.log = Logger(fh, self.class_name)
        self.request = request
        self.operation_type = operation_type
        self.error_view = url_for("common_error")
        self.db_logger = ClientLog(request_ip=request.remote_addr,
                                   request_url=request.url,
                                   request_headers=request.headers,
                                   request_method=self.request.method,
                                   request_data=get_request_data(self.request),
                                   operation_type=self.operation_type,
                                   manager_id=manager['id'] if manager else None,
                                   created=datetime.datetime.now())
        self.need_log = True
        self.confidential_fields = ()

    def _call(self, *args, **kwds):
        raise NotImplementedError("%s._call" % self.class_name)

    def _verify_post_request(self, requires):
        request_data = get_request_data(self.request)
        for r in requires:
            if r not in request_data:
                raise ServiceException("Invalid request, '%s' is required" % r)

        return Struct(**request_data)

    def get_cleaned_request_data(self):
        request_data = get_request_data(self.request)
        for field in self.confidential_fields:
            request_data.pop(field, None)
        return request_data

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

    def _verify_bid(self, bid_id):
        if not bid_id:
            raise ServiceException("'bid' is required")

        if not str(bid_id).isdigit():
            raise ServiceException("Invalid 'bid=%s'" % bid_id)

        bid = Bid.get_by_id(int(bid_id))
        if not bid:
            raise ServiceException("Bid (id=%s) doesn't exist" % bid_id)

        return bid

    def _send_email(self, msg):
        try:
            msg.sender = "Team Profinsta <{}>".format(msg.sender)
            mail.send(msg)

        except Exception as ex:
            self.log.exception("Error while sending email to %s" % msg.recipients)
            ErrorLog.create(request_data=get_request_data(self.request),
                            request_ip=self.request.remote_addr,
                            request_url=self.request.url,
                            request_method=self.request.method,
                            error=str(ex),
                            traceback=traceback.format_exc(),
                            request_headers=self.request.headers)

    def _send_inform_message(self, chat_id, text):
        url = bot_api_url + bot_token + '/sendMessage?' + urllib.urlencode(dict(chat_id=chat_id, text=str(text)))
        try:
            response = requests.get(url)
        except Exception as ex:
            self.log.warn("Error during send telegram msg: %s" % ex.message)
            ErrorLog.create(request_data=get_request_data(self.request),
                            request_ip=self.request.remote_addr,
                            request_url=self.request.url,
                            request_method=self.request.method,
                            error=str(ex),
                            traceback=traceback.format_exc(),
                            request_headers=self.request.headers)
            return False

        if response.status_code == 200:
            return True

        self.log.debug("Error during send alarm msg. Error description = %s" %
                       response.json().get('description', ''))

    def _verify_recaptcha(self):
        if not recaptcha.verify():
            raise IncorrectCaptchaException("Recaptcha verification failed")

    def _log_result(self, new_val, old_val=None):
        result = {"new_val": new_val}
        if old_val is not None:
            result.update({"old_val": old_val})
        self.db_logger.operation_result = result


class TemplateController(BaseController):
    def call(self, *args, **kwds):
        result = None
        try:
            self.log.debug("Started process request: %s" % self.get_cleaned_request_data())
            data = self._call(*args, **kwds)
            self.log.debug("Finished")
            result = data
        except ServiceException as ex:
            self.db_logger.error = ex.message
            self.log.warn(ex.message)
            flash(ex.user_message)
            result = redirect(self.error_view)

        except IncorrectCaptchaException, ex:
            self.need_log = False
            flash(ex.message)
            self.log.warn("[operation_type: {0}, request_ip: {1}, request_headers: {2}, error: {3}]"
                          .format(self.operation_type,
                                  self.request.remote_addr,
                                  dict(self.request.headers.items())['User-Agent'],
                                  ex.message))
            result = redirect(self.error_view)

        except Exception as ex:
            self.db_logger.error = ex.message
            self.db_logger.traceback = traceback.format_exc()
            self.log.exception("Error during %s call" % self.class_name)
            flash(ex.message)
            ErrorLog.create(
                request_data=get_request_data(self.request),
                request_ip=self.request.remote_addr,
                request_url=self.request.url,
                request_method=self.request.method,
                error=ex.message,
                traceback=traceback.format_exc(),
                request_headers=self.request.headers
            )
            result = redirect(url_for("common_error"))

        finally:
            if self.need_log or self.db_logger.error:
                self.db_logger.finished = datetime.datetime.now()
                self.db_logger.save()
            return result


class JsonController(BaseController):
    def call(self, *args, **kwds):
        result = None
        try:
            self.log.debug("Started process request: %s" % self.get_cleaned_request_data())
            data = self._call(*args, **kwds)
            self.log.debug("Finished with data: %s" % data)
            result = ControllerResult(data=data)
        except ServiceException as ex:
            self.db_logger.error = ex.message
            self.log.warn(ex.message)
            result = ControllerResult(result=False, message=ex.user_message, error=ex.message)
        except Exception as ex:
            self.db_logger.error = ex.message
            self.log.exception("Error during %s call" % self.class_name)
            ErrorLog.create(
                request_data=get_request_data(self.request),
                request_ip=self.request.remote_addr,
                request_url=self.request.url,
                request_method=self.request.method,
                error=ex.message,
                traceback=traceback.format_exc(),
                request_headers=self.request.headers
            )
            result = ControllerResult(result=False, message="Unexpected error occurred", error=ex.message)
        finally:
            if self.need_log or self.db_logger.error:
                self.db_logger.finished = datetime.datetime.now()
                self.db_logger.save()

            return result


class BidIDCoder(object):

    encode_map = {"0": "p",
                  "1": "r",
                  "2": "o",
                  "3": "f",
                  "4": "i",
                  "5": "n",
                  "6": "s",
                  "7": "t",
                  "8": "a",
                  "9": "v"}

    decode_map = dict(((v, k) for k, v in encode_map.items()))

    def encode_bid_id(self, bid_id, num=ENCODE_NUM):
        noise_len = 12
        random_items = [i for i in xrange(97, 123) if chr(i) not in self.encode_map.values()]
        random.seed()
        mapped = [self.encode_map[c] for c in str(bid_id * num)] + [""] * noise_len
        noise = random.sample(random_items, noise_len)
        places_to_insert = random.sample(xrange(len(mapped)), noise_len - 1)
        places_to_insert.append(0)
        for i in xrange(len(places_to_insert)):
            mapped.insert(places_to_insert[i], chr(noise[i]))

        upper_noise = random.sample(mapped, 4)
        mapped = "".join(mapped)
        for c in upper_noise:
            mapped = mapped.replace(c, c.upper(), 1)

        return mapped

    def decode(self, encoded, num=ENCODE_NUM):
        encoded = encoded.lower()
        cleaned = [c for c in encoded if c in self.decode_map]
        res = "".join([str(self.decode_map[c.lower()]) for c in cleaned])
        if math.fmod(int(res), num):
            raise ValueError("Invalid encoded data")
        return int(res) / num
