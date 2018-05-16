from functools import wraps
from flask import render_template
from flask_login import current_user


def permission_required():
	def decorator(f):
		@wraps(f)
		def decorated_function(*args, **kwargs):
			if current_user:
				if not current_user.can():
					return render_template('403.html')
				return f(*args, **kwargs)
		return decorated_function
	return decorator

def admin_required(f):
	"""

	:rtype:
	"""
	return permission_required()(f)

# def administrator_required():
# 	def decorator(f):
# 		@wraps(f)
# 		def decorated_function(*args, **kwargs):
# 			if not current_user.id_developer():
# 				return render_template('auth/maintenance.html')
# 			return f(*args, **kwargs)
# 		return decorated_function
# 	return decorator
#
# def developer_required(f):
# 	return administrator_required()(f)