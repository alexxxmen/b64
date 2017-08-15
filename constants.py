# -*- coding:utf-8 -*-


class BaseConstants(object):
    @classmethod
    def get_desc(cls, id):
        return cls.to_dict().get(id, "Unknown")

    @classmethod
    def to_dict(cls):
        return {i: desc for desc, i in cls.__dict__.items() if not desc.startswith("__")}


class BidStatus(BaseConstants):
    New = 1
    Verified = 2


class OperationType:
    Login = 1
    Logout = 2
    IndexView = 3
    Pay = 4
    SupportMessage = 5
    CreateBid = 6
    ViewBid = 7
    EditBid = 8
