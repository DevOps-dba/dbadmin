# -*- coding: utf-8 -*-
from flask import render_template, session, redirect, url_for, current_app, flash,abort,request,send_from_directory,g,_app_ctx_stack
from . import users
from flask_login import login_user, logout_user, login_required,current_user
from .. import login_manager
from time import strftime,localtime,time
from ..decorators import admin_required
from werkzeug.security import generate_password_hash
import json
import string
from random import choice
from .. import get_db

import sys
reload(sys)
sys.setdefaultencoding('utf8')


@users.before_request
def before_request():
	g.user = current_user

'''
  用户管理 -- 用户列表
'''
# 用户信息列表 - 页面视图
@users.route('/user_list', methods=['GET', 'POST'])
@login_required
@admin_required
def user_list():
	app = "用户管理"
	action = "用户列表"
	return render_template('users/user_list.html',app=app,action=action)

# 用户信息列表 - ajax视图
@users.route('/user_list_ajax', methods=['GET', 'POST'])
@login_required
@admin_required
def user_list_ajax():
	# 获取ajax中传递的request的data值
	page_dict = {'page_content': None, 'page_count': None,'per_page':None}
	# data = json.loads(request.form.get('data'))
	data = request.get_json()

	# 初始化对dbadmin系统后台数据库的访问
	con = get_db()
	cursor = con.cursor()

	# 对非空的条件进行SQL语句拼接
	page = int(data['page'])
	condition = 'WHERE 1=1'
	if data['userlist_keyword']:
		condition += " AND (A.name like '%{name}%' OR A.username like '%{name}%' OR B.departName like '%{name}%')".format(name=data['userlist_keyword'].strip())

	# 获取总数据行数
	userlist_count_sql = "SELECT COUNT(A.id) FROM dbadmin_auth_users A INNER JOIN dbadmin_auth_departments B ON A.deptId=B.id {condition};".format(condition=condition)
	cursor.execute(userlist_count_sql)
	userscount_result = cursor.fetchall()
	page_dict['page_count'] = userscount_result[0][0]
	# per_page = current_app.config['FLASKY_POSTS_PAGE']
	if int(data['data_length']) != 100:
		page_dict['per_page'] = int(data['data_length'])
		per_page = int(data['data_length'])
	else:
		page_dict['per_page'] = int(userscount_result[0][0])
		per_page = int(userscount_result[0][0])

	# 获取首页展示的数据
	userlist_select_sql = "SELECT A.id,A.username,A.name,B.departName,A.superAdmin,A.question,A.confirmed FROM dbadmin_auth_users A INNER JOIN dbadmin_auth_departments B ON A.deptId=B.id {condition} ORDER BY A.id DESC LIMIT {start},{per_page};".format(
		start=(page - 1) * per_page, condition=condition, per_page=per_page)
	cursor.execute(userlist_select_sql)
	userlist_result = cursor.fetchall()

	page_cont_str = ''
	for i in userlist_result:
		# 用户身份类型
		if int(i[4]) == 0:
			user_status = '<span class="label label-default" style="font-size:12px;">普通用户</span>'
		else:
			user_status = '<span class="label label-primary" style="font-size:12px;">超级管理员</span>'

		# 用户账号状态和操作类型
		if int(i[6]) == 0:
			account_status = '<span class="label label-warning-light" style="font-size:12px;">未启用</span>'
			op_type = '<a class="btn btn-xs btn-primary" href="/users/user_toggle/{id}/{status}">启用</a>'.format(id=int(i[0]),status=int(i[6]))
		else:
			account_status = '<span class="label label-primary" style="font-size:12px;">已启用</span>'
			op_type = '<a class="btn btn-xs btn-danger" href="/users/user_toggle/{id}/{status}">禁用</a>'.format(id=int(i[0]),status=int(i[6]))

		page_cont_str += '''
					<tr class="gradeX">
						<td class="text-center">
							<input type="checkbox" name="checked" value="{id}" class="ipt_check">
						</td>
						<td class="text-center">{id}</td>
						<td class="text-center"><a href="/users/user_list/{id}">{username}</a></td>
						<td class="text-center" title="">{name}</td>
						<td class="text-center">{deptname}</td>
						<td class="text-center" >{user_status}</td>
						<td class="text-center">{question}</td>
						<td class="text-center">{account_status}</td>
						<td class="text-center">
							<a href="/users/user_edit/{id}" class="btn btn-xs btn-info">编辑</a>
							{op_type}
							<a onClick="return confirm('确认要删除 {username} 这个用户？')" href="/users/user_delete/{id}" class="btn btn-xs btn-danger del">删除</a>
						</td>
					</tr>
					'''.format(id=int(i[0]),username=i[1],name=i[2],deptname=i[3],user_status=user_status,question=i[5],account_status=account_status,op_type=op_type)
	page_dict['page_content'] = page_cont_str

	return json.dumps(page_dict)

# 用户信息列表 - 删除功能视图
@users.route('/user_delete/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user_delete(id):
	con = get_db()
	cursor = con.cursor()
	delete_user_sql = "DELETE FROM dbadmin_auth_users WHERE id='{id}';".format(id=id)
	cursor.execute(delete_user_sql)
	cursor.execute('COMMIT;')

	return redirect(url_for('users.user_list'))

# 用户信息列表 - 启用禁用功能视图
@users.route('/user_toggle/<int:id>/<int:status>', methods=['GET', 'POST'])
@login_required
@admin_required
def user_toggle(id,status):
	con = get_db()
	cursor = con.cursor()
	if status == 1:
		user_profile_status = 0
	else:
		user_profile_status = 1
	currentTime = strftime("%Y-%m-%d %H:%M:%S")
	update_user_profile_sql = "UPDATE dbadmin_auth_users SET confirmed={confirmed},update_time='{update_time}' WHERE id={id};".format(confirmed=user_profile_status,id=id,update_time=currentTime)
	try:
		cursor.execute(update_user_profile_sql)
		cursor.execute('COMMIT;')
	except Exception as e:
		print(e)

	return redirect(url_for('users.user_list'))

# 用户信息列表 - 编辑功能视图
@users.route('/user_edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user_edit(id):
	con = get_db()
	cursor = con.cursor()
	get_department_sql = "SELECT id,departName FROM dbadmin_auth_departments;"
	cursor.execute(get_department_sql)
	departForm = cursor.fetchall()

	get_userinfo_sql = "SELECT A.id,A.username,A.name,A.weixin_num,A.dingding_num,A.mail_num,A.phone_num,A.question,A.deptId FROM dbadmin_auth_users A  WHERE A.id='{id}';".format(id=id)
	cursor.execute(get_userinfo_sql)
	userinfo_result = cursor.fetchall()
	app = "用户管理"
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
			id=id,name=name,weixin_num=weixin_num,dingding_num=dingding_num,mail_num=mail_num,phone_num=phone_num,question=question,deptId=deptId,update_time=currentTime)
		try:
			cursor.execute(update_userinfo_sql)
			cursor.execute("COMMIT;")
		except Exception as e:
			print(e)
		return redirect(url_for('users.user_edit',id=id))

	return render_template('users/user_profile_edit.html',departForm=departForm,userinfo_result=userinfo_result,app=app,action=action)

# 用户信息列表 - 批量操作功能视图
@users.route('/user_list_bulk_ajax', methods=['GET', 'POST'])
@login_required
@admin_required
def user_list_bulk_ajax():
	data = request.get_json()
	bulk_ids = []
	result = {"status": 0, "msg": ''}
	if data['user_update_array']:
		for i in data['user_update_array']:
			bulk_ids.append(int(i))
		bulk_ids.append(0)
		bulk_id_tuple = tuple(bulk_ids)
		currentTime = strftime("%Y-%m-%d %H:%M:%S")
		if data['type'] != 'delete':
			bulk_type = 1
			if data['type'] == 'active':
				bulk_type = 1
			elif data['type'] == 'deactive':
				bulk_type = 0
			bulk_users_sql = "UPDATE dbadmin_auth_users SET confirmed={confirmed},update_time='{update_time}' WHERE id IN {bulk_id_tuple} AND confirmed != {confirmed};".format(confirmed=bulk_type,bulk_id_tuple=bulk_id_tuple,update_time=currentTime)
		else:
			bulk_users_sql = "DELETE FROM dbadmin_auth_users WHERE id IN {bulk_id_tuple};".format(bulk_id_tuple=bulk_id_tuple)

		con = get_db()
		cursor = con.cursor()
		try:
			cursor.execute(bulk_users_sql)
			cursor.execute('COMMIT;')
		except Exception as e:
			result['status'] = 1
			result['msg'] = str(e)
			print(e)
	else:
		result['status'] = 1
		result['msg'] = "未选中任何用户!"

	return json.dumps(result)

# 用户列表 -个人信息展示视图
@users.route('/user_list/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user_profile(id):
	con = get_db()
	cursor = con.cursor()
	get_userinfo_sql = "SELECT A.id,A.username,A.name,B.departName,A.confirmed,A.register_time,A.update_time,A.last_access,A.superAdmin,A.question,A.weixin_num,A.dingding_num,A.mail_num,A.phone_num FROM dbadmin_auth_users A INNER JOIN dbadmin_auth_departments B ON A.deptId=B.id WHERE A.id='{id}';".format(id=id)
	cursor.execute(get_userinfo_sql)
	userinfo_result = cursor.fetchall()
	app = "用户管理"
	action = "个人信息"

	return render_template('users/user_profile.html',userinfo_result=userinfo_result,app=app,action=action)

# 个人信息 - 个人状态启用和禁用视图
@users.route('/user_profile_update_ajax', methods=['GET', 'POST'])
@login_required
@admin_required
def user_profile_update_ajax():

	data = request.get_json()
	con = get_db()
	cursor = con.cursor()
	result = {"status": 0}
	# 判断前端传入的激活按钮的状态,从而决定需要更新的目标用户状态
	if data['checked']:
		user_profile_status = 1
	else:
		user_profile_status = 0
	currentTime = strftime("%Y-%m-%d %H:%M:%S")
	update_user_profile_sql = "UPDATE dbadmin_auth_users SET confirmed={confirmed},update_time='{update_time}' WHERE id={id};".format(confirmed=user_profile_status,id=int(data['id']),update_time=currentTime)
	try:
		cursor.execute(update_user_profile_sql)
		cursor.execute('COMMIT;')
	except Exception as e:
		result = {"status": 1, "msg": str(e)}
		print(e)

	return json.dumps(result)

# 个人信息 - 生成随机密码视图
@users.route('/user_profile_autopwd_ajax', methods=['GET', 'POST'])
@login_required
@admin_required
def user_profile_autopwd_ajax():
	passwd_length = 12
	passwd_seed = string.digits + string.ascii_letters + "!@#$%^&*"
	newpasswd = ''
	while (len(newpasswd) < passwd_length):
		if len(newpasswd) == 0:
			newpasswd = choice(string.ascii_letters)
		elif len(newpasswd) == 11:
			newpasswd += choice(string.ascii_letters + string.digits)
		else:
			newpasswd += choice(passwd_seed)
	return json.dumps(newpasswd)

# 个人信息 - 更新密码视图
@users.route('/user_profile_updatepwd_ajax', methods=['GET', 'POST'])
@login_required
@admin_required
def user_profile_updatepwd_ajax():
	data = request.get_json()
	pwhash = generate_password_hash(data['newpwd'])
	currentTime = strftime("%Y-%m-%d %H:%M:%S")
	update_password_sql = "UPDATE dbadmin_auth_users SET password_hash='{pwhash}',update_time='{update_time}' WHERE id={id};".format(pwhash=pwhash,id=int(data['id']),update_time=currentTime)
	con = get_db()
	cursor = con.cursor()
	try:
		cursor.execute(update_password_sql)
		cursor.execute('COMMIT;')
	except Exception as e:
		print(e)

	return json.dumps('')


'''
用户管理 -- 部门列表
'''
# 部门信息列表 - 页面视图
@users.route('/dept_list', methods=['GET', 'POST'])
@login_required
@admin_required
def dept_list():
	app = "用户管理"
	action = "部门列表"
	return render_template('users/dept_list.html',app=app,action=action)

# 部门列表 -个人信息展示视图
@users.route('/dept_list/<username>', methods=['GET', 'POST'])
@login_required
@admin_required
def dept_user_profile(username):
	con = get_db()
	cursor = con.cursor()
	get_userinfo_sql = "SELECT A.id,A.username,A.name,B.departName,A.confirmed,A.register_time,A.update_time,A.last_access,A.superAdmin,A.question,A.weixin_num,A.dingding_num,A.mail_num,A.phone_num FROM dbadmin_auth_users A INNER JOIN dbadmin_auth_departments B ON A.deptId=B.id WHERE A.username='{username}';".format(username=username)
	cursor.execute(get_userinfo_sql)
	userinfo_result = cursor.fetchall()
	app = "用户管理"
	action = "个人信息"

	return render_template('users/user_profile.html',userinfo_result=userinfo_result,app=app,action=action)

# 用于将列表中的用户名进行字符串拼接
def generate_href(username):
	return '<a href="/users/dept_list/{username}">{username}</a>'.format(username=username)

# 部门信息列表 - ajax视图
@users.route('/dept_list_ajax', methods=['GET', 'POST'])
@login_required
@admin_required
def dept_list_ajax():
	# 获取ajax中传递的request的data值
	page_dict = {'page_content': None, 'page_count': None,'per_page':None}
	data = request.get_json()

	# 初始化对dbadmin系统后台数据库的访问
	con = get_db()
	cursor = con.cursor()

	# 对非空的条件进行SQL语句拼接
	page = int(data['page'])
	condition = 'WHERE 1=1'
	if data['deptlist_keyword']:
		condition += " AND A.departName like '%{name}%'".format(name=data['deptlist_keyword'].strip())

	# 获取总数据行数
	deptlist_count_sql = "SELECT COUNT(A.id) FROM dbadmin_auth_departments A  {condition};".format(condition=condition)
	cursor.execute(deptlist_count_sql)
	deptcount_result = cursor.fetchall()
	page_dict['page_count'] = deptcount_result[0][0]
	# per_page = current_app.config['FLASKY_POSTS_PAGE']
	if int(data['dept_data_length']) != 100:
		page_dict['per_page'] = int(data['dept_data_length'])
		per_page = int(data['dept_data_length'])
	else:
		page_dict['per_page'] = int(deptcount_result[0][0])
		per_page = int(deptcount_result[0][0])

	# 获取首页展示的数据
	deptlist_select_sql = "SELECT  A.id,A.departName,COUNT(distinct(B.id)),group_concat(DISTINCT B.username),A.status FROM dbadmin_auth_departments A LEFT JOIN dbadmin_auth_users B ON A.id=B.deptId {condition} GROUP BY A.id ORDER BY A.id DESC LIMIT {start},{per_page};".format(
		start=(page - 1) * per_page, condition=condition, per_page=per_page)
	cursor.execute(deptlist_select_sql)
	deptlist_result = cursor.fetchall()

	page_cont_str = ''
	for i in deptlist_result:
		# 部门所包含用户
		if i[3]:
			users_list = i[3].split(',')
			users = ','.join(map(generate_href,users_list))
		else:
			users = ''

		# 部门启用状态类型
		if int(i[4]) == 0:
			dept_status = '<span class="label label-info" style="font-size:12px;">已启用</span>'
			op_type = '<a class="btn btn-xs btn-danger" href="/users/dept_toggle/{id}/{status}">禁用</a>'.format(id=int(i[0]), status=int(i[4]))
		else:
			dept_status = '<span class="label label-warning" style="font-size:12px;">未启用</span>'
			op_type = '<a class="btn btn-xs btn-primary" href="/users/dept_toggle/{id}/{status}">启用</a>'.format(id=int(i[0]),status=int(i[4]))

		page_cont_str += '''
					<tr class="gradeX">
						<td class="text-center">{id}</td>
						<td class="text-center">{deptname}</td>
						<td class="text-center">{users_count}</td>
						<td style=" word-wrap:break-word;word-break:break-all;" width="500">{users}</td>
						<td class="text-center" >{dept_status}</td>
						<td class="text-center">
							<a href="/users/dept_edit/{id}" class="btn btn-xs btn-info">编辑</a>
							{op_type}
							<a onClick="return confirm('确认要删除 {deptname} 这个部门？')" href="/users/dept_delete/{id}" class="btn btn-xs btn-danger del">删除</a>
						</td>
					</tr>
					'''.format(id=int(i[0]),deptname=i[1],users_count=i[2],users=users,dept_status=dept_status,op_type=op_type)
	page_dict['page_content'] = page_cont_str

	return json.dumps(page_dict)

# 部门信息列表 - 启用禁用功能视图
@users.route('/dept_toggle/<int:id>/<int:status>', methods=['GET', 'POST'])
@login_required
@admin_required
def dept_toggle(id,status):
	con = get_db()
	cursor = con.cursor()
	if status == 1:
		dept_status = 0
	else:
		dept_status = 1
	update_deptinfo_sql = "UPDATE dbadmin_auth_departments SET status={status} WHERE id={id};".format(status=dept_status,id=id)
	try:
		cursor.execute(update_deptinfo_sql)
		cursor.execute('COMMIT;')
	except Exception as e:
		print(e)

	return redirect(url_for('users.dept_list'))

# 部门信息列表 - 删除功能视图
@users.route('/dept_delete/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def dept_delete(id):
	con = get_db()
	cursor = con.cursor()
	delete_dept_sql = "DELETE FROM dbadmin_auth_departments WHERE id='{id}';".format(id=id)
	cursor.execute(delete_dept_sql)
	cursor.execute('COMMIT;')

	return redirect(url_for('users.dept_list'))

# 部门信息列表 - 编辑功能视图
@users.route('/dept_edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def dept_edit(id):
	con = get_db()
	cursor = con.cursor()
	get_deptinfo_sql = "SELECT A.departName,A.status FROM dbadmin_auth_departments A  WHERE A.id='{id}';".format(id=id)
	cursor.execute(get_deptinfo_sql)
	dept_result = cursor.fetchall()
	app = "用户管理"
	action = "编辑部门信息"
	if request.method == 'POST':
		dept_name = request.form['dept_name']
		dept_status = request.form.get('dept_status')
		if dept_status:
			dept_status = 0
		else:
			dept_status = 1
		update_deptinfo_sql = "UPDATE dbadmin_auth_departments SET departName='{departName}',status={status} WHERE id={id};".format(id=id,departName=dept_name,status=dept_status)
		try:
			cursor.execute(update_deptinfo_sql)
			cursor.execute("COMMIT;")
		except Exception as e:
			print(e)
		return redirect(url_for('users.dept_edit',id=id))

	return render_template('users/dept_edit.html',dept_result=dept_result,app=app,action=action)

# 部门信息列表 - 新建功能视图
@users.route('/dept_create', methods=['GET', 'POST'])
@login_required
@admin_required
def dept_create():
	app = "用户管理"
	action = "新建部门信息"
	if request.method == 'POST':
		con = get_db()
		cursor = con.cursor()

		dept_name = request.form['dept_name']
		dept_status = request.form.get('dept_status')
		if dept_status:
			dept_status = 0
		else:
			dept_status = 1
		insert_deptinfo_sql = "INSERT INTO dbadmin_auth_departments(departName,status) VALUES('{departName}',{status});".format(departName=dept_name,status=dept_status)
		try:
			cursor.execute(insert_deptinfo_sql)
			cursor.execute("COMMIT;")
		except Exception as e:
			print(e)
		return redirect(url_for('users.dept_list'))

	return render_template('users/dept_create.html',app=app,action=action)

'''
用户管理 -- 权限管理列表
'''
# 权限管理列表 - 页面视图
@users.route('/user_priv_list', methods=['GET', 'POST'])
@login_required
@admin_required
def user_priv_list():
	app = "用户管理"
	action = "权限管理"
	return render_template('users/user_priv_list.html',app=app,action=action)

# 用户信息列表 - ajax视图
@users.route('/user_priv_list_ajax', methods=['GET', 'POST'])
@login_required
@admin_required
def user_priv_list_ajax():
	# 获取ajax中传递的request的data值
	page_dict = {'page_content': None, 'page_count': None,'per_page':None}
	data = request.get_json()

	# 初始化对dbadmin系统后台数据库的访问
	con = get_db()
	cursor = con.cursor()

	# 对非空的条件进行SQL语句拼接
	page = int(data['page'])
	condition = 'WHERE 1=1'
	if data['user_priv_keyword']:
		condition += " AND (A.username like '%{name}%')".format(name=data['user_priv_keyword'].strip())

	# 获取总数据行数
	userprivlist_count_sql = "SELECT COUNT(DISTINCT A.id) FROM dbadmin_auth_users A LEFT JOIN dbadmin_assets_users_rel B ON A.id=B.userid AND B.priv_type=0 LEFT JOIN dbadmin_assets_users_rel C ON A.id=C.userid AND C.priv_type=1 LEFT JOIN dbadmin_assets_users_rel D ON A.id=D.userid AND D.priv_type=2  {condition} AND (B.id IS NOT NULL OR C.id IS NOT NULL OR D.id IS NOT NULL);".format(condition=condition)
	cursor.execute(userprivlist_count_sql)
	usersprivcount_result = cursor.fetchall()
	page_dict['page_count'] = usersprivcount_result[0][0]
	if int(data['user_priv_table_length']) != 100:
		page_dict['per_page'] = int(data['user_priv_table_length'])
		per_page = int(data['user_priv_table_length'])
	else:
		page_dict['per_page'] = int(usersprivcount_result[0][0])
		per_page = int(usersprivcount_result[0][0])

	# 获取首页展示的数据
	userprivlist_select_sql = "SELECT A.id,A.username,group_concat(DISTINCT E.name),group_concat(DISTINCT F.name),group_concat(DISTINCT G.name) FROM dbadmin_auth_users A LEFT JOIN dbadmin_assets_users_rel B ON A.id=B.userid AND B.priv_type=0 LEFT JOIN dbadmin_assets_mysqldb E ON B.assetid=E.id LEFT JOIN dbadmin_assets_users_rel C ON A.id=C.userid AND C.priv_type=1 LEFT JOIN dbadmin_assets_mysqldb F ON C.assetid=F.id  LEFT JOIN dbadmin_assets_users_rel D ON A.id=D.userid AND D.priv_type=2 LEFT JOIN dbadmin_assets_mysqldb G ON D.assetid=G.id  {condition} AND (B.id IS NOT NULL OR C.id IS NOT NULL OR D.id IS NOT NULL) GROUP BY A.id ORDER BY A.id DESC LIMIT {start},{per_page};".format(
		start=(page - 1) * per_page, condition=condition, per_page=per_page)
	cursor.execute(userprivlist_select_sql)
	userprivlist_result = cursor.fetchall()

	page_cont_str = ''
	for i in userprivlist_result:

		if not i[2]:
			priv_all = ''
		else:
			priv_all = i[2]
		if not i[3]:
			priv_ddl = ''
		else:
			priv_ddl = i[3]
		if not i[4]:
			priv_dml = ''
		else:
			priv_dml = i[4]

		page_cont_str += '''
					<tr class="gradeX">
						<td class="text-center">
							<input type="checkbox" name="checked" value="{id}" class="ipt_check">
						</td>
						<td class="text-center"><a href="/users/user_priv_edit/{id}">{username}</a></td>
						<td style=" word-wrap:break-word;word-break:break-all;">{priv_all}</td>
						<td style=" word-wrap:break-word;word-break:break-all;">{priv_ddl}</td>
						<td style=" word-wrap:break-word;word-break:break-all;">{priv_dml}</td>
						<td class="text-center" style="width:10%">
							<a href="/users/user_priv_edit/{id}" class="btn btn-xs btn-info del">授权</a>
							<a onClick="return confirm('确认要删除 {username} 这个用户权限？')" href="/users/user_priv_delete/{id}" class="btn btn-xs btn-danger del">删除</a>
						</td>
					</tr>
					'''.format(id=int(i[0]),username=i[1],priv_all=priv_all,priv_ddl=priv_ddl,priv_dml=priv_dml)
	page_dict['page_content'] = page_cont_str

	return json.dumps(page_dict)

# 权限管理列表 - 新增用户权限视图
@users.route('/user_priv_create', methods=['GET', 'POST'])
@login_required
@admin_required
def user_priv_create():
	app = "用户管理"
	action = "新增用户权限"
	return render_template('users/user_priv_create.html',app=app,action=action)

# 权限管理列表 - 新增用户权限ajax视图
@users.route('/user_priv_create_ajax', methods=['GET', 'POST'])
@login_required
@admin_required
def user_priv_create_ajax():
	data = request.get_json()
	# 校验新建用户是否已存在
	check_users_exists_sql = "SELECT A.id FROM dbadmin_auth_users A INNER JOIN dbadmin_assets_users_rel B ON A.id=B.userid WHERE A.username='{username}';".format(username=data['users_name'].strip())
	con = get_db()
	cursor = con.cursor()
	cursor.execute(check_users_exists_sql)
	check_users_exists_result = cursor.fetchall()
	if check_users_exists_result:
		result = {"status": 1, "msg": "'{username}'用户已存在,无法再新建,请在列表中进行授权操作!".format(username=data['users_name'].strip())}
		return json.dumps(result)
	else:
		# 校验是否已选择任何数据库
		if not data['selected_db_id']:
			result = {"status": 1, "msg": '未选择任何数据库,请重新选择!'}
			return json.dumps(result)
		else:
			try:
				# 获取该用户的id信息
				get_user_id_sql = "SELECT A.id FROM dbadmin_auth_users A WHERE A.username='{username}';".format(username=data['users_name'].strip())
				cursor.execute(get_user_id_sql)
				get_user_id_result = cursor.fetchall()
				if not get_user_id_result:
					result = {"status": 1,"msg": "'{username}'用户不存在,无法新建!".format(username=data['users_name'].strip())}
					return json.dumps(result)
				user_id = int(get_user_id_result[0][0])

				addition = ''
				currentTime = strftime("%Y-%m-%d %H:%M:%S")
				# 拼接insert语句，将信息写入用户权限关系表dbadmin_assets_users_rel中
				insert_users_sql = "INSERT INTO dbadmin_assets_users_rel(userid,assetid,priv_type,createTime) VALUES "
				length = len(data['selected_db_id'])
				for i,element in enumerate(data['selected_db_id']):
					addition += "({user_id},{assetid},{priv_type},'{currentTime}')".format(user_id=user_id,assetid=int(element['db_id']),priv_type=int(element['db_priv_type']),currentTime=currentTime)
					if i == length-1:
						addition += ";"
					else:
						addition += ","
				insert_users_sql += addition
				cursor.execute(insert_users_sql)
				cursor.execute('COMMIT;')
				result = {"status": 0, "msg": "新建'{username}'用户权限成功!".format(username=data['users_name'].strip())}
			except Exception as e:
				result = {"status": 1, "msg": "新建'{username}'用户权限失败,报错信息:'{e}'!".format(username=data['users_name'].strip(),e=str(e))}
				print(e)

	return json.dumps(result)

# 权限管理列表 - autocomplete获取未添加权限用户名视图
@users.route('/get_autocomplete_users_ajax', methods=['GET', 'POST'])
@login_required
@admin_required
def get_autocomplete_users_ajax():
	get_unused_users_sql = "SELECT A.username FROM dbadmin_auth_users A LEFT JOIN dbadmin_assets_users_rel B ON A.id=B.userid WHERE B.id is NULL;"
	con = get_db()
	cursor = con.cursor()
	unused_users_list = []
	try:
		cursor.execute(get_unused_users_sql)
		get_unused_users_result = cursor.fetchall()
		for i in get_unused_users_result:
			unused_users_list.append(i[0])
	except Exception as e:
		print(e)

	return json.dumps(unused_users_list)

# 权限管理列表 - 获取未添加的数据库列表视图
@users.route('/get_all_db_ajax', methods=['GET', 'POST'])
@login_required
@admin_required
def get_all_db_ajax():
	data = request.get_json()
	bulk_ids = []
	condition = "WHERE 1=1"
	if data['existed_db_array']:
		for i in data['existed_db_array']:
			bulk_ids.append(int(i))
		bulk_ids.append(0)
		bulk_id_tuple = tuple(bulk_ids)
		condition += ' AND A.id not in {bulk_id_tuple}'.format(bulk_id_tuple=bulk_id_tuple)
	con = get_db()
	cursor = con.cursor()
	get_all_db_sql = "SELECT A.name,B.ipaddress,A.id FROM dbadmin_assets_mysqldb A INNER JOIN dbadmin_assets_hosts B ON A.hostid=B.id {condition} ORDER BY B.id,A.name;".format(condition=condition)
	cursor.execute(get_all_db_sql)
	get_all_db_result = cursor.fetchall()
	page_dict = {'page_content': None}
	page_cont_str = ''
	for i in get_all_db_result:
		page_cont_str += '''
						<tr class="gradeX">
							<td class="text-center">
								<input type="checkbox" name="checked" value="{id}" class="ipt_check">
							</td>
							<td style=" word-wrap:break-word;word-break:break-all;">{name}</td>
							<td class="text-center" title="">{ipaddress}</td>
						</tr>
						'''.format(name=i[0], ipaddress=i[1],id=int(i[2]))
	page_dict['page_content'] = page_cont_str

	return json.dumps(page_dict)

# 权限管理列表 - 删除用户权限功能视图
@users.route('/user_priv_delete/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user_priv_delete(id):
	con = get_db()
	cursor = con.cursor()

	delete_user_priv_sql = "DELETE FROM dbadmin_assets_users_rel WHERE userid={userid};".format(userid=id)
	cursor.execute(delete_user_priv_sql)
	cursor.execute('COMMIT;')

	return redirect(url_for('users.user_priv_list'))

# 权限管理列表 - 编辑用户权限ajax视图
@users.route('/user_priv_edit_ajax', methods=['GET', 'POST'])
@login_required
@admin_required
def user_priv_edit_ajax():
	data = request.get_json()
	result = {"status": 0,"msg":0}
	new_ids = []
	for i in data['selected_db_id']:
		new_ids.append(int(i['db_id']))
	old_ids = []
	con = get_db()
	cursor = con.cursor()
	get_old_ids_sql = "SELECT A.assetid,B.id FROM dbadmin_assets_users_rel A INNER JOIN dbadmin_auth_users B ON A.userid=B.id WHERE B.username='{username}';".format(username=data['users_name'])
	cursor.execute(get_old_ids_sql)
	get_old_ids_result = cursor.fetchall()
	current_user_id = int(get_old_ids_result[0][1])
	for j in get_old_ids_result:
		old_ids.append(int(j[0]))
	add_ids = list(set(new_ids).difference(set(old_ids)))
	delete_ids = list(set(old_ids).difference(set(new_ids)))
	update_ids = list(set(new_ids).difference(set(add_ids)))
	if not data['selected_db_id']:
		result = {"status": 1, "msg": '未选择任何数据库,请重新选择!'}
		return json.dumps(result)
	else:
		try:
			# 存在新增数据库时，拼接insert语句，写入数据库
			if add_ids:
				add_selected_db = []
				for i in data['selected_db_id']:
					if int(i['db_id']) in add_ids:
						add_selected_db.append(i)
				addition = ''
				currentTime = strftime("%Y-%m-%d %H:%M:%S")
				# 拼接insert语句，将新增信息写入用户权限关系表dbadmin_assets_users_rel中
				insert_users_priv_sql = "INSERT INTO dbadmin_assets_users_rel(userid,assetid,priv_type,createTime) VALUES "
				length = len(add_selected_db)
				for i,element in enumerate(add_selected_db):
					addition += "({user_id},{assetid},{priv_type},'{currentTime}')".format(user_id=current_user_id,assetid=int(element['db_id']),priv_type=int(element['db_priv_type']),currentTime=currentTime)
					if i == length-1:
						addition += ";"
					else:
						addition += ","
				insert_users_priv_sql += addition
				cursor.execute(insert_users_priv_sql)
				cursor.execute('COMMIT;')
			if delete_ids:
				if len(delete_ids) == 1:
					delete_ids.append(0)
				delete_users_priv_sql = "DELETE FROM dbadmin_assets_users_rel WHERE userid={userid} AND assetid IN {delete_ids};".format(userid=current_user_id,delete_ids=tuple(delete_ids))
				cursor.execute(delete_users_priv_sql)
				cursor.execute('COMMIT;')
			if update_ids:
				update_selected_db = []
				for i in data['selected_db_id']:
					if int(i['db_id']) in update_ids:
						update_selected_db.append(i)
				for i, element in enumerate(update_selected_db):
					update_priv_type_sql = "UPDATE dbadmin_assets_users_rel SET priv_type={priv_type} WHERE userid={userid} AND assetid={assetid};".format(userid=current_user_id,priv_type=int(element['db_priv_type']),assetid=int(element['db_id']))
					cursor.execute(update_priv_type_sql)
				cursor.execute('COMMIT;')
			result = {"status": 0, "msg": "编辑'{username}'用户权限成功!".format(username=data['users_name'].strip())}
		except Exception as e:
			result = {"status": 1, "msg": "编辑'{username}'用户权限失败,报错信息:'{e}'!".format(username=data['users_name'].strip(),e=str(e))}
			print(e)

	return json.dumps(result)

# 权限管理列表 - 编辑权限功能视图
@users.route('/user_priv_edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user_priv_edit(id):
	con = get_db()
	cursor = con.cursor()
	get_username_sql = "SELECT A.username FROM dbadmin_auth_users A  WHERE A.id='{id}';".format(id=id)
	cursor.execute(get_username_sql)
	get_username_result = cursor.fetchall()
	app = "用户管理"
	action = "编辑用户权限"
	get_user_priv_sql = "SELECT B.id,B.name,C.ipaddress,A.priv_type FROM dbadmin_assets_users_rel A INNER JOIN dbadmin_assets_mysqldb B ON A.assetid=B.id INNER JOIN dbadmin_assets_hosts C ON B.hostid=C.id where A.userid={userid};".format(userid=id)
	cursor.execute(get_user_priv_sql)
	get_user_priv_result = cursor.fetchall()

	return render_template('users/user_priv_edit.html',get_username_result=get_username_result,get_user_priv_result=get_user_priv_result,app=app,action=action)

'''
用户管理 -- 用户登录列表
'''
# 用户登录列表 - 页面视图
@users.route('/login_record_list', methods=['GET', 'POST'])
@login_required
@admin_required
def login_record_list():
	app = "用户管理"
	action = "用户登录列表"
	return render_template('users/login_record_list.html',app=app,action=action)

# 用户登录列表 - ajax视图
@users.route('/login_record_list_ajax', methods=['GET', 'POST'])
@login_required
@admin_required
def login_record_list_ajax():
	# 获取ajax中传递的request的data值
	page_dict = {'page_content': None, 'page_count': None,'per_page':None}
	data = request.get_json()

	# 初始化对dbadmin系统后台数据库的访问
	con = get_db()
	cursor = con.cursor()

	# 对非空的条件进行SQL语句拼接
	page = int(data['page'])
	condition = 'WHERE 1=1'
	if data['loginlist_username']:
		condition += " AND A.username like '%{username}%'".format(username=data['loginlist_username'].strip())
	if data['loginlist_starttime']:
		condition += " AND A.loginTime >= '{loginTime}'".format(loginTime=(data['loginlist_starttime'].strip()+":00"))
	if data['loginlist_stoptime']:
		condition += " AND A.loginTime <= '{loginTime}'".format(loginTime=(data['loginlist_stoptime'].strip()+":00"))

	# 获取总数据行数
	loginlist_count_sql = "SELECT COUNT(A.id) FROM dbadmin_auth_record A  {condition};".format(condition=condition)
	cursor.execute(loginlist_count_sql)
	logincount_result = cursor.fetchall()
	page_dict['page_count'] = logincount_result[0][0]
	if int(data['loginlist_data_length']) != 100:
		page_dict['per_page'] = int(data['loginlist_data_length'])
		per_page = int(data['loginlist_data_length'])
	else:
		page_dict['per_page'] = int(logincount_result[0][0])
		per_page = int(logincount_result[0][0])

	# 获取首页展示的数据
	loginlist_select_sql = "SELECT A.id,A.username,A.ipaddress,A.agent,A.loginTime,B.id FROM dbadmin_auth_record A  INNER JOIN dbadmin_auth_users B ON A.username=B.username {condition} ORDER BY A.id DESC LIMIT {start},{per_page};".format(
		start=(page - 1) * per_page, condition=condition, per_page=per_page)
	cursor.execute(loginlist_select_sql)
	loginlist_result = cursor.fetchall()

	page_cont_str = ''
	for i in loginlist_result:

		page_cont_str += '''
					<tr class="gradeX">
						<td class="text-center">{id}</td>
						<td class="text-center"><a href="/users/user_list/{user_id}">{username}</a></td>
						<td class="text-center" title="">{ipaddress}</td>
						<td width="500">{agent}</td>
						<td class="text-center" >{loginTime}</td>
					</tr>
					'''.format(id=int(i[0]),username=i[1],ipaddress=i[2],agent=i[3],loginTime=i[4],user_id=int(i[5]))
	page_dict['page_content'] = page_cont_str

	return json.dumps(page_dict)
