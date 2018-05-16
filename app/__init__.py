# -*- coding: utf-8 -*-
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
import urllib,json
from config import config,Config
from flask import _app_ctx_stack, current_app
import pymysql
import sqlalchemy.pool as pool

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'

bootstrap = Bootstrap()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    @app.teardown_appcontext
    def close_database_connection(error=None):
        con = getattr(_app_ctx_stack, 'database', None)
        if con:
            con.close()

    # 初始化数据库连接池，以后的连接不再重新连接数据库，而是从连接池中获取
    def getconn(db_conf=None):
        conn = pymysql.connect(host=current_app.config['IP'], user=current_app.config['USER'],passwd=current_app.config['PASSWD'],db=current_app.config['DB'], port=current_app.config['PORT'], charset='utf8')
        return conn

    mypool = pool.QueuePool(getconn, max_overflow=55, pool_size=30)
    app.db_pool = mypool

    login_manager.init_app(app)
    bootstrap.init_app(app)

    from .main import main
    app.register_blueprint(main,url_prefix='/main')

    from .auth import auth
    app.register_blueprint(auth, url_prefix='/auth')

    from .users import users
    app.register_blueprint(users, url_prefix='/users')

    from .assets import assets
    app.register_blueprint(assets, url_prefix='/assets')

    from .monitor import monitor
    app.register_blueprint(monitor, url_prefix='/monitor')

    return app


def get_db():
    ctx = _app_ctx_stack.top
    con = getattr(ctx, 'database', None)
    if con is None:
        con = current_app.db_pool.connect()
        ctx.database = con
    return con

import sys
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex

class prpcrypt():
	def __init__(self, key):
		length = 16
		count = len(key)
		add = length - (count % length)
		key = key + ('0' * add)
		self.key = key
		self.mode = AES.MODE_CBC

	# 加密函数，如果text不是16的倍数【加密文本text必须为16的倍数！】，那就补足为16的倍数
	def encrypt(self, text):
		cryptor = AES.new(self.key, self.mode, self.key)
		# 这里密钥key 长度必须为16（AES-128）、24（AES-192）、或32（AES-256）Bytes 长度.目前AES-128足够用
		length = 16
		count = len(text)
		add = length - (count % length)
		text = text + ('\0' * add)
		self.ciphertext = cryptor.encrypt(text)
		# 因为AES加密时候得到的字符串不一定是ascii字符集的，输出到终端或者保存时候可能存在问题
		# 所以这里统一把加密后的字符串转化为16进制字符串
		return b2a_hex(self.ciphertext)

	# 解密后，去掉补足的空格用strip() 去掉
	def decrypt(self, text):
		cryptor = AES.new(self.key, self.mode, self.key)
		plain_text = cryptor.decrypt(a2b_hex(text))
		return plain_text.rstrip('\0')
