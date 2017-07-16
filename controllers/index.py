# -*- coding:utf-8 -*-

from flask import render_template

from controllers import TemplateController


class IndexController(TemplateController):
    def __init__(self, request):
        super(IndexController, self).__init__(request)

    def _call(self):
        return render_template('index.html')
