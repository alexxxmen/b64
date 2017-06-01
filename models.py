# -*- coding:utf-8 -*-

from peewee import Model, CharField, DateTimeField, TextField, datetime as peewee_datetime
from playhouse.pool import PooledPostgresqlExtDatabase

from config import DB_CONFIG

peewee_now = peewee_datetime.datetime.now

db = PooledPostgresqlExtDatabase(**DB_CONFIG)
db.commit_select = True
db.autorollback = True


class _Model(Model):
    class Meta:
        database = db


class Event(Model):
    class Meta:
        db_table = 'events'

    title = CharField()
    start = DateTimeField()
    description = TextField(null=True)
    created = DateTimeField(default=peewee_now)
