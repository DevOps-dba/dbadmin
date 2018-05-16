# -*- coding: utf-8 -*-
from flask import render_template, session, redirect, url_for, current_app, flash,abort,request,send_from_directory,g,_app_ctx_stack
from . import auth
from flask_login import login_user, logout_user, login_required,current_user
from .forms import LoginForm #,RegistrationForm,changePasswdForm,manageForm,dbMangementForm
from models import User
from .. import login_manager
from time import strftime,localtime,time
from werkzeug.security import generate_password_hash,check_password_hash
from ..decorators import admin_required
from flask_paginate import Pagination
from .. import get_db

import sys
reload(sys)
sys.setdefaultencoding('utf8')

@login_manager.user_loader
def load_user(user_id):
	return User.get(user_id)

@auth.before_request
def before_request():
	g.user = current_user

# 登录视图，实现用户名校验，密码校验等功能。
@auth.route('/login',methods=['GET', 'POST'])
def login():
	logout_user()
	error_code = 3
	if request.method == 'POST':
		con = get_db()
		cursor = con.cursor()
		username = request.form['username']
		password = request.form['password']
		remeberme = request.form.get('remeberme')

		user = User(username)
		checkusersql = "SELECT id,password_hash,confirmed,superAdmin FROM dbadmin_auth_users WHERE username = '{username}';".format(username=username)
		cursor.execute(checkusersql)
		checkresult = cursor.fetchall()
		# 首先校验是否有该用户
		if checkresult:
			# 校验密码是否正确
			if check_password_hash(checkresult[0][1], password):
				login_user(user, False)
				# 校验账号是否经过管理员确认
				if int(checkresult[0][2]) == 0:
					error_code = 2
					return render_template('auth/login.html', error_code=error_code)
				else:
					g.user = current_user
					# 记录登录日志
					try:
						login_record_sql = "INSERT INTO dbadmin_auth_record(ipaddress,username,agent,loginTime) VALUES ('{ipaddress}','{username}','{agent}','{loginTime}');".format(
										ipaddress=request.remote_addr,username=username,agent=request.user_agent,loginTime=strftime("%Y-%m-%d %H:%M:%S"))
						cursor.execute(login_record_sql)
						cursor.execute("COMMIT;")
					except Exception as e:
						print(e)
					if request.args.get('next'):
						return redirect(request.args.get('next'))
					else:
						return redirect(url_for('main.index'))
			else:
				error_code = 1
				return render_template('auth/login.html', error_code=error_code)
		else:
			# error_code 的各种含义为：0，无该用户，1，密码错误，2，账号未确认
			error_code = 0
			return render_template('auth/login.html', error_code=error_code)

	return render_template('auth/login.html', error_code=error_code)

@auth.route('/logout')
@login_required
def logout():
	return redirect(url_for('auth.login'))

# 注册视图，实现用户的自助式注册功能
@auth.route('/register', methods=['GET', 'POST'])
def register():
	con = get_db()
	cursor = con.cursor()
	get_department_sql = "SELECT id,departName FROM dbadmin_auth_departments WHERE status = 0;"
	cursor.execute(get_department_sql)
	departForm = cursor.fetchall()
	error_code = 0
	if request.method == 'POST':
		register_username = request.form['register_username']
		register_password = request.form['register_password']
		register_department = request.form['register_department']
		register_name = request.form['register_name']
		register_question = request.form['register_question']

		checkUserSql = "SELECT 1 FROM dbadmin_auth_users WHERE username = '{username}';".format(username=register_username)
		cursor.execute(checkUserSql)
		checkresult = cursor.fetchall()
		if checkresult:
			error_code = 1
			return render_template('auth/register.html', departForm=departForm, error_code=error_code)
		if len(register_password) < 6:
			error_code = 3
			return render_template('auth/register.html', departForm=departForm, error_code=error_code)

		# 将用户输入的密码进行加盐处理，从数据库中可看到相同的字符串密码的hash值并不一致
		pwhash = generate_password_hash(register_password)
		currentTime = strftime("%Y-%m-%d %H:%M:%S")
		insertNewUsersql = "INSERT INTO dbadmin_auth_users(username,password_hash,deptId,name,question,register_time,update_time) VALUES('{username}','{pwhash}',{deptId},'{name}','{question}','{register_time}','{update_time}');".format(
			username=register_username, pwhash=pwhash, deptId=int(register_department),name=register_name,question=register_question,register_time=currentTime,update_time=currentTime)
		try:
			cursor.execute(insertNewUsersql)
			cursor.execute("COMMIT;")
		except Exception as e:
			print(e)
			error_code = 2
			return render_template('auth/register.html', departForm=departForm, error_code=error_code)
		return redirect(url_for('auth.login'))

	return render_template('auth/register.html',departForm=departForm,error_code=error_code)

# 修改密码视图，结合验证问题实现密码的更新和重置
@auth.route('/modifyPasswd', methods=['GET', 'POST'])
def modifyPasswd():
	con = get_db()
	cursor = con.cursor()
	error_code = 0
	if request.method == 'POST':
		modify_username = request.form['modify_username']
		modify_password = request.form['modify_password']
		modify_password_again = request.form['modify_password_again']
		modify_question = request.form['modify_question']
		modify_question_new = request.form.get('modify_question_new')

		get_question_sql = "SELECT question FROM dbadmin_auth_users WHERE username='{username}';".format(username=modify_username)
		cursor.execute(get_question_sql)
		question = cursor.fetchall()
		if question[0][0] != modify_question:
			error_code = 1
			return render_template('auth/modifyPasswd.html', error_code=error_code)
		if modify_password != modify_password_again:
			error_code = 2
			return render_template('auth/modifyPasswd.html', error_code=error_code)
		if len(modify_password) < 6:
			error_code = 3
			return render_template('auth/modifyPasswd.html', error_code=error_code)
		if not modify_question_new:
			modify_question_new = modify_question
		# 更新对应用户的密码
		currentTime = strftime("%Y-%m-%d %H:%M:%S")
		pwhash = generate_password_hash(modify_password)
		update_password_sql = "UPDATE dbadmin_auth_users SET password_hash='{pwhash}',question='{question}',update_time='{update_time}' WHERE username='{username}';".format(
			pwhash=pwhash,username=modify_username,question=modify_question_new,update_time=currentTime)
		try:
			cursor.execute(update_password_sql)
			cursor.execute("COMMIT;")
		except Exception as e:
			print(e)
			error_code = 4
			return render_template('auth/modifyPasswd.html', error_code=error_code)
		return redirect(url_for('auth.login'))

	return render_template('auth/modifyPasswd.html',error_code=error_code)

# 个人信息展示视图
@auth.route('/user_profile', methods=['GET', 'POST'])
@login_required
def user_profile():
	con = get_db()
	cursor = con.cursor()
	get_userinfo_sql = "SELECT A.id,A.username,A.name,B.departName,A.confirmed,A.register_time,A.update_time,A.last_access,A.superAdmin,A.question,A.weixin_num,A.dingding_num,A.mail_num,A.phone_num FROM dbadmin_auth_users A INNER JOIN dbadmin_auth_departments B ON A.deptId=B.id WHERE A.username='{username}';".format(username=g.user.username)
	cursor.execute(get_userinfo_sql)
	userinfo_result = cursor.fetchall()
	action = "个人信息"

	return render_template('auth/user_profile.html',userinfo_result=userinfo_result,action=action)

# 个人信息编辑视图
@auth.route('/user_profile_edit', methods=['GET', 'POST'])
@login_required
def user_profile_edit():
	con = get_db()
	cursor = con.cursor()
	get_department_sql = "SELECT id,departName FROM dbadmin_auth_departments WHERE status=0;"
	cursor.execute(get_department_sql)
	departForm = cursor.fetchall()

	get_userinfo_sql = "SELECT A.id,A.username,A.name,A.weixin_num,A.dingding_num,A.mail_num,A.phone_num,A.question,A.deptId FROM dbadmin_auth_users A  WHERE A.username='{username}';".format(username=g.user.username)
	cursor.execute(get_userinfo_sql)
	userinfo_result = cursor.fetchall()
	action = "编辑个人信息"
	if request.method == 'POST':
		name = request.form['name']
		weixin_num = request.form.get('weixin_num')
		dingding_num = request.form.get('dingding_num')
		mail_num = request.form.get('mail_num')
		phone_num = request.form.get('phone_num')
		question = request.form['question']
		deptId = request.form['deptId']
		currentTime = strftime("%Y-%m-%d %H:%M:%S")
		update_userinfo_sql = "UPDATE dbadmin_auth_users SET name='{name}',weixin_num='{weixin_num}',dingding_num='{dingding_num}',mail_num='{mail_num}',phone_num='{phone_num}',question='{question}',deptId={deptId},update_time='{update_time}' WHERE id={id};".format(
			id=userinfo_result[0][0],name=name,weixin_num=weixin_num,dingding_num=dingding_num,mail_num=mail_num,phone_num=phone_num,question=question,deptId=deptId,update_time=currentTime)
		cursor.execute(update_userinfo_sql)
		cursor.execute("COMMIT;")
		return redirect(url_for('auth.user_profile_edit'))

	return render_template('auth/user_profile_edit.html',departForm=departForm,userinfo_result=userinfo_result,action=action)





