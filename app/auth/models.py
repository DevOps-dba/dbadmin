from flask import current_app
from flask_login import UserMixin
from .. import get_db

class User(UserMixin):
	def __init__(self, username):
		self.username = username
		self.id = self.get_id()

	def get_id(self):
		if self.username is not None:
			con = get_db()
			cursor = con.cursor()
			getsql = "SELECT id FROM dbadmin_auth_users WHERE username = '{account}';".format(account=self.username)
			cursor.execute(getsql)
			getresult = cursor.fetchall()
			if getresult:
				return unicode(getresult[0][0])
			else:
				return None
		return None

	def can(self):
		con = get_db()
		cursor = con.cursor()
		getsql = "SELECT superAdmin FROM dbadmin_auth_users WHERE username = '{account}';".format(account=self.username)
		cursor.execute(getsql)
		getresult = cursor.fetchall()
		if int(getresult[0][0]) == 1:
			return True
		else:
			return False

	def id_developer(self):
		con = get_db()
		cursor = con.cursor()
		getsql = "SELECT id FROM dbadmin_auth_users WHERE username = '{account}';".format(account=self.username)
		cursor.execute(getsql)
		getresult = cursor.fetchall()
		if int(getresult[0][0]) == 1:
			return True
		else:
			return False

	@staticmethod
	def get(user_id):
		if not user_id:
			return None
		con = get_db()
		cursor = con.cursor()
		getIdsql = "SELECT username FROM dbadmin_auth_users WHERE id = '{user_id}';".format(user_id=user_id)
		cursor.execute(getIdsql)
		getresult = cursor.fetchall()
		if getresult:
			return User(getresult[0][0])
		return None

	def __repr__(self):
		return '<User %r>' % self.username


