# -*- coding:utf-8 -*-

import logging
from decimal import Decimal


from flask import Response
from flask.json import JSONEncoder


class StructEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Struct):
            return o.__dict__

        if isinstance(o, Response):
            return (o.data, o.status)

        return super(StructEncoder, self).default(o)


class Logger(object):
    def __init__(self, file_handler, logger_name):
        self._log = logging.getLogger(logger_name)
        self._log.addHandler(file_handler)
        self._log.setLevel(file_handler.level)

    def __getattr__(self, *args, **kwds):
        return getattr(self._log, *args, **kwds)


class Struct(object):
    def __init__(self, *agrs, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, dict):
                setattr(self, k, Struct(**v))
            elif isinstance(v, Decimal):
                setattr(self, k, float(v))
            elif isinstance(v, (list, tuple)):
                setattr(self, k, [Struct(**l) if isinstance(l, dict) else l for l in v])
            else:
                setattr(self, k, v)

    def __iter__(self):
        return iter(self.__dict__)

    def keys(self):
        return self.__dict__.keys()

    def __getitem__(self, attr):
        return getattr(self, attr)

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def items(self):
        return self.__dict__.items()

    def to_dict(self):
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Struct):
                result[key] = value.to_dict()
            elif isinstance(value, (list, tuple)):
                result[key] = [v.to_dict() for v in value]
            else:
                result[key] = value
        return result

    def __str__(self):
        return unicode(self.to_dict())

    def __unicode__(self):
        return unicode(self.to_dict())


def get_request_data(request):
    return dict(request.json or request.form.items() or {})
