# -*- coding: utf-8 -*-
from flask import redirect, url_for,render_template,request
from . import main
from flask_login import login_required
from .. import get_db
import json


#首页主函数
@main.route('/index', methods=['GET', 'POST'])
def index():
	return render_template('index.html')

