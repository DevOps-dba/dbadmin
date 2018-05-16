# import os
# -*- coding: UTF-8 -*-

class Config:
	IP = "192.168.28.128"
	USER = "dbadmin"
	PASSWD = "dbadmin"
	DB = "dbadmin"
	PORT = 3306
	FLASKY_POSTS_PAGE = 10
	DEBUG = True
	SECRET_KEY = 'you-will-never-guess'
	ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
	UPLOADED_PHOTOS_DEST="/remote_backup/upload"
	PER_PAGE = 10

	@staticmethod
	def init_app(app):
		pass


config = {'default': Config}



