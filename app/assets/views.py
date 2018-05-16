# -*- coding: utf-8 -*-
from flask import render_template, session, redirect, url_for, current_app, flash,abort,request,send_from_directory,g,_app_ctx_stack
from . import assets
from flask_login import login_user, logout_user, login_required,current_user
from .. import login_manager
from time import strftime,strptime,mktime,localtime,time
from ..decorators import admin_required
import json,string,pymysql,re
from random import choice
from .. import get_db,prpcrypt

import sys
reload(sys)
sys.setdefaultencoding('utf8')


@assets.before_request
def before_request():
	g.user = current_user
	# g.connect_db = get_db()


'''
资产管理 -- 资产列表
'''

# 资产信息列表 - 页面视图
@assets.route('/asset_list', methods=['GET', 'POST'])
@login_required
@admin_required
def asset_list():
	app = "资产管理"
	action = "资产列表"
	return render_template('assets/asset_list.html',app=app,action=action)

# 资产信息列表 - 新增资产视图
@assets.route('/asset_create', methods=['GET', 'POST'])
@login_required
@admin_required
def asset_create():
	app = "资产管理"
	action = "新增资产"
	if request.method == 'POST':
		con = get_db()
		cursor = con.cursor()

		assets_host_ip = request.form['assets_host_ip']
		assets_host_dbtype = request.form['assets_host_dbtype']
		assets_host_dbaccount = request.form['assets_host_dbaccount']
		assets_host_dbpasswd = request.form['assets_host_dbpasswd']
		assets_host_dbport = request.form['assets_host_dbport']
		assets_host_note = request.form.get('assets_host_note')
		assets_host_status = request.form.get('assets_host_status')
		currentTime = strftime("%Y-%m-%d %H:%M:%S")
		currentTimeStamp = int(mktime(strptime(currentTime,"%Y-%m-%d %H:%M:%S")))
		if assets_host_status:
			assets_host_status = 0
		else:
			assets_host_status = 1
		pc = prpcrypt(str(currentTimeStamp))
		pwhash = pc.encrypt(assets_host_dbpasswd)
		insert_assetinfo_sql = "INSERT INTO dbadmin_assets_hosts(ipaddress,dbtype,db_account,db_password,db_port,status,createTime,updateTime,note) VALUES('{ipaddress}',{dbtype},'{db_account}','{db_password}',{db_port},{status},'{createTime}','{updateTime}','{note}');".format(
			ipaddress=assets_host_ip, dbtype=int(assets_host_dbtype), db_account=assets_host_dbaccount, db_password=pwhash, db_port=assets_host_dbport, status=assets_host_status, createTime=currentTime, updateTime=currentTime, note=assets_host_note)
		try:
			record_list = [[u'IP地址','',assets_host_ip],[u'数据库类型','',int(assets_host_dbtype)],[u'DB账号','',assets_host_dbaccount],[u'DB端口','',assets_host_dbport],[u'状态','',assets_host_status],[u'备注','',assets_host_note]]
			cursor.execute(insert_assetinfo_sql)
			new_id = cursor.lastrowid
			insert_assetinfo_record_sql = "INSERT INTO dbadmin_assets_hosts_record(hostid,username,status,createTime,content) VALUES ('{hostid}','{username}',{status},'{createTime}',\"{content}\");".format(
									hostid=int(new_id),username=g.user.username,status=0,createTime=currentTime,content=record_list)
			cursor.execute(insert_assetinfo_record_sql)
			cursor.execute("COMMIT;")
		except Exception as e:
			print(e)
		return redirect(url_for('assets.asset_list'))

	return render_template('assets/asset_create.html',app=app,action=action)


# 资产信息列表 - ajax视图
@assets.route('/asset_list_ajax', methods=['GET', 'POST'])
@login_required
@admin_required
def asset_list_ajax():
	# 获取ajax中传递的request的data值
	page_dict = {'page_content': None, 'page_count': None,'per_page':None}
	data = request.get_json()

	# 初始化对dbadmin系统后台数据库的访问
	con = get_db()
	cursor = con.cursor()

	# 对非空的条件进行SQL语句拼接
	page = int(data['page'])
	condition = 'WHERE 1=1'
	if data['assetlist_keyword']:
		condition += " AND A.ipaddress like '%{ip}%'".format(ip=data['assetlist_keyword'].strip())
	if data['assetlist_dbtype']:
		condition += " AND A.dbtype = '{dbtype}'".format(dbtype=int(data['assetlist_dbtype']))
	if data['assetlist_status']:
		condition += " AND A.status = '{status}'".format(status=int(data['assetlist_status']))

	# 获取总数据行数
	assetlist_count_sql = "SELECT COUNT(A.id) FROM dbadmin_assets_hosts A  {condition};".format(condition=condition)
	cursor.execute(assetlist_count_sql)
	assetscount_result = cursor.fetchall()
	page_dict['page_count'] = assetscount_result[0][0]
	if int(data['asset_data_length']) != 100:
		page_dict['per_page'] = int(data['asset_data_length'])
		per_page = int(data['asset_data_length'])
	else:
		page_dict['per_page'] = int(assetscount_result[0][0])
		per_page = int(assetscount_result[0][0])

	# 获取首页展示的数据
	assetlist_select_sql = "SELECT A.id,A.ipaddress,A.dbtype,A.db_account,A.db_port,A.status,A.createTime FROM dbadmin_assets_hosts A  {condition} ORDER BY A.id DESC LIMIT {start},{per_page};".format(
		start=(page - 1) * per_page, condition=condition, per_page=per_page)
	cursor.execute(assetlist_select_sql)
	assetlist_result = cursor.fetchall()

	page_cont_str = ''
	for i in assetlist_result:

		# 主机状态类型
		if int(i[5]) == 0:
			asset_status = '<span class="label label-primary" style="font-size:12px;">已激活</span>'
			op_type = '<a class="btn btn-xs btn-danger" href="/assets/asset_toggle/{id}/{status}">禁用</a>'.format(id=int(i[0]),status=int(i[5]))
		else:
			asset_status = '<span class="label label-warning" style="font-size:12px;">未激活</span>'
			op_type = '<a class="btn btn-xs btn-primary" href="/assets/asset_toggle/{id}/{status}">启用</a>'.format(id=int(i[0]),status=int(i[5]))

		# 数据库类型
		if int(i[2]) == 0:
			assets_host_dbtype = 'MySQL'
		elif int(i[2]) == 1:
			assets_host_dbtype = 'ORACLE'
		elif int(i[2]) == 2:
			assets_host_dbtype = 'Redis'
		elif int(i[2]) == 3:
			assets_host_dbtype = 'MongoDB'
		else:
			assets_host_dbtype = '其他'

		page_cont_str += '''
					<tr class="gradeX">
						<td class="text-center">
							<input type="checkbox" name="checked" value="{id}" class="ipt_check">
						</td>
						<td class="text-center">{id}</td>
						<td class="text-center"><a href="/assets/asset_detail/{id}">{assets_host_ip}</a></td>
						<td class="text-center" title=""><span class="label label-primary" style="font-size:12px;">{assets_host_dbtype}</span></td>
						<td class="text-center">{assets_host_dbaccount}</td>
						<td class="text-center" >{assets_host_dbport}</td>
						<td class="text-center">{assets_host_status}</td>
						<td class="text-center">{assets_host_ctime}</td>
						<td class="text-center">
							<a href="/assets/asset_edit/{id}" class="btn btn-xs btn-info">编辑</a>
							{op_type}
							<a onClick="return confirm('确认要删除 {assets_host_ip} 这个主机？')" href="/assets/asset_delete/{id}" class="btn btn-xs btn-danger del">删除</a>
						</td>
					</tr>
					'''.format(id=int(i[0]),assets_host_ip=i[1],assets_host_dbtype=assets_host_dbtype,assets_host_dbaccount=i[3],assets_host_dbport=i[4],question=i[5],assets_host_status=asset_status,assets_host_ctime=i[6],op_type=op_type)
	page_dict['page_content'] = page_cont_str

	return json.dumps(page_dict)

# 资产信息列表 - 资产详情视图
@assets.route('/asset_detail/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def asset_detail(id):

	app = "资产管理"
	action = "资产详情"
	con = get_db()
	cursor = con.cursor()
	get_asset_detail_sql = "SELECT A.id,A.ipaddress,A.dbtype,A.db_account,A.db_port,A.status,A.createTime,A.note FROM dbadmin_assets_hosts A WHERE A.id = {id};".format(id=id)
	cursor.execute(get_asset_detail_sql)
	asset_detail_result = cursor.fetchall()

	get_asset_db_sql = "SELECT name,status,createTime,tables_nums FROM dbadmin_assets_mysqldb WHERE hostid={hostid};".format(hostid=id)
	cursor.execute(get_asset_db_sql)
	asset_db_result = cursor.fetchall()

	return render_template('assets/asset_detail.html',app=app,action=action,asset_detail_result=asset_detail_result,asset_db_result=asset_db_result)

# 资产信息列表 - 启用禁用功能视图
@assets.route('/asset_toggle/<int:id>/<int:status>', methods=['GET', 'POST'])
@login_required
@admin_required
def asset_toggle(id,status):
	con = get_db()
	cursor = con.cursor()
	if status == 1:
		asset_status = 0
	else:
		asset_status = 1
	update_asset_status_sql = "UPDATE dbadmin_assets_hosts SET status={status} WHERE id={id};".format(status=asset_status,id=id)
	try:
		cursor.execute(update_asset_status_sql)
		cursor.execute('COMMIT;')
	except Exception as e:
		print(e)

	return redirect(url_for('assets.asset_list'))

# 资产信息列表 - 删除功能视图
@assets.route('/asset_delete/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def asset_delete(id):
	con = get_db()
	cursor = con.cursor()
	delete_asset_sql = "DELETE FROM dbadmin_assets_hosts WHERE id='{id}';".format(id=id)
	try:
		cursor.execute(delete_asset_sql)
		cursor.execute('COMMIT;')
	except Exception as e:
		print(e)

	return redirect(url_for('assets.asset_list'))

# 资产信息列表 - 编辑功能视图
@assets.route('/asset_edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def asset_edit(id):
	con = get_db()
	cursor = con.cursor()

	get_assetinfo_sql = "SELECT A.ipaddress,A.dbtype,A.db_account,A.db_password,A.db_port,A.note,A.status,A.createTime FROM dbadmin_assets_hosts A  WHERE A.id='{id}';".format(id=id)
	cursor.execute(get_assetinfo_sql)
	assetinfo_result = cursor.fetchall()
	assetinfo_list = list(assetinfo_result[0])
	createTimeStamp = str(int(mktime(strptime(assetinfo_list[7],"%Y-%m-%d %H:%M:%S"))))
	pc = prpcrypt(createTimeStamp)
	assetinfo_list[3] = pc.decrypt(assetinfo_list[3])
	app = "资产管理"
	action = "编辑资产"
	if request.method == 'POST':
		assets_host_ip = request.form['assets_host_ip']
		assets_host_dbtype = request.form['assets_host_dbtype']
		assets_host_dbaccount = request.form['assets_host_dbaccount']
		assets_host_dbpasswd = request.form['assets_host_dbpasswd']
		assets_host_dbport = request.form['assets_host_dbport']
		assets_host_note = request.form.get('assets_host_note')
		assets_host_status = request.form.get('assets_host_status')
		if assets_host_status:
			assets_host_status = 0
		else:
			assets_host_status = 1
		pwhash = pc.encrypt(assets_host_dbpasswd)
		currentTime = strftime("%Y-%m-%d %H:%M:%S")
		update_assetinfo_sql = "UPDATE dbadmin_assets_hosts SET ipaddress='{ipaddress}',dbtype={dbtype},db_account='{db_account}',db_password='{db_password}',db_port={db_port},status={status},updateTime='{updateTime}',note='{note}' WHERE id={id};".format(
			id=id,ipaddress=assets_host_ip,dbtype=assets_host_dbtype,db_account=assets_host_dbaccount,db_password=pwhash,db_port=assets_host_dbport,note=assets_host_note,status=assets_host_status,updateTime=currentTime)
		try:
			cursor.execute(update_assetinfo_sql)
			cursor.execute("COMMIT;")
		except Exception as e:
			print(e)
		return redirect(url_for('assets.asset_edit',id=id))

	return render_template('assets/asset_edit.html',assetinfo_result=assetinfo_list,app=app,action=action)

# 资产信息列表 - 批量操作功能视图
@assets.route('/asset_list_bulk_ajax', methods=['GET', 'POST'])
@login_required
@admin_required
def asset_list_bulk_ajax():
	data = request.get_json()
	bulk_ids = []
	result = {"status": 0, "msg": ''}
	if data['asset_update_array']:
		for i in data['asset_update_array']:
			bulk_ids.append(int(i))
		bulk_ids.append(0)
		bulk_id_tuple = tuple(bulk_ids)
		currentTime = strftime("%Y-%m-%d %H:%M:%S")
		if data['type'] != 'delete':
			bulk_type = 1
			if data['type'] == 'active':
				bulk_type = 0
			elif data['type'] == 'deactive':
				bulk_type = 1
			bulk_assets_sql = "UPDATE dbadmin_assets_hosts SET status={status},updateTime='{updateTime}' WHERE id IN {bulk_id_tuple} AND status != {status};".format(status=bulk_type,bulk_id_tuple=bulk_id_tuple,updateTime=currentTime)
		else:
			bulk_assets_sql = "DELETE FROM dbadmin_assets_hosts WHERE id IN {bulk_id_tuple};".format(bulk_id_tuple=bulk_id_tuple)

		con = get_db()
		cursor = con.cursor()
		try:
			cursor.execute(bulk_assets_sql)
			cursor.execute('COMMIT;')
		except Exception as e:
			result['status'] = 1
			result['msg'] = str(e)
			print(e)
	else:
		result['status'] = 1
		result['msg'] = "未选中任何主机!"

	return json.dumps(result)

'''
资产管理 -- MySQL数据库列表
'''

# MySQL数据库列表 - 页面视图
@assets.route('/mysqldb_list', methods=['GET', 'POST'])
@login_required
@admin_required
def mysqldb_list():
	app = "资产管理"
	action = "MySQL数据库列表"
	return render_template('assets/mysqldb_list.html',app=app,action=action)

# MySQL数据库列表 - ajax视图
@assets.route('/mysqldb_list_ajax', methods=['GET', 'POST'])
@login_required
@admin_required
def mysqldb_list_ajax():
	# 获取ajax中传递的request的data值
	page_dict = {'page_content': None, 'page_count': None,'per_page':None}
	data = request.get_json()

	# 初始化对dbadmin系统后台数据库的访问
	con = get_db()
	cursor = con.cursor()

	# 对非空的条件进行SQL语句拼接
	page = int(data['page'])
	condition = 'WHERE 1=1'
	if data['mysqldb_name']:
		condition += " AND A.name like '%{name}%'".format(name=data['mysqldb_name'].strip())
	if data['mysqldb_status']:
		condition += " AND A.status = '{status}'".format(status=int(data['mysqldb_status']))
	if data['mysqldb_ipaddress']:
		condition += " AND B.ipaddress like '%{ipaddress}%'".format(ipaddress=data['mysqldb_ipaddress'])

	# 获取总数据行数
	mysqldblist_count_sql = "SELECT COUNT(A.id) FROM dbadmin_assets_mysqldb A  INNER JOIN dbadmin_assets_hosts B ON A.hostid=B.id {condition};".format(condition=condition)
	cursor.execute(mysqldblist_count_sql)
	mysqldbcount_result = cursor.fetchall()
	page_dict['page_count'] = mysqldbcount_result[0][0]
	if int(data['mysqldb_data_length']) != 100:
		page_dict['per_page'] = int(data['mysqldb_data_length'])
		per_page = int(data['mysqldb_data_length'])
	else:
		page_dict['per_page'] = int(mysqldbcount_result[0][0])
		per_page = int(mysqldbcount_result[0][0])

	# 获取首页展示的数据
	mysqldblist_select_sql = "SELECT A.id,A.name,B.ipaddress,A.status,A.createTime,B.id FROM dbadmin_assets_mysqldb A INNER JOIN dbadmin_assets_hosts B ON A.hostid=B.id {condition} ORDER BY A.id DESC LIMIT {start},{per_page};".format(
		start=(page - 1) * per_page, condition=condition, per_page=per_page)
	cursor.execute(mysqldblist_select_sql)
	mysqldblist_result = cursor.fetchall()

	page_cont_str = ''
	for i in mysqldblist_result:

		# 主机状态类型
		if int(i[3]) == 0:
			mysqldb_status = '<span class="label label-primary" style="font-size:12px;">已激活</span>'
			op_type = '<a class="btn btn-xs btn-danger" href="/assets/mysqldb_toggle/{id}/{status}">禁用</a>'.format(id=int(i[0]), status=int(i[3]))
		else:
			mysqldb_status = '<span class="label label-warning" style="font-size:12px;">未激活</span>'
			op_type = '<a class="btn btn-xs btn-primary" href="/assets/mysqldb_toggle/{id}/{status}">启用</a>'.format(id=int(i[0]), status=int(i[3]))


		page_cont_str += '''
					<tr class="gradeX">
						<td class="text-center">
							<input type="checkbox" name="checked" value="{id}" class="ipt_check">
						</td>
						<td class="text-center">{id}</td>
						<td style="padding-left:30px;">{name}</td>
						<td class="text-center"><a href="/assets/asset_detail/{hostid}">{assets_host_ip}</a></td>
						<td style=" word-wrap:break-word;word-break:break-all;" width="100"></td>
						<td class="text-center" title="">{mysqldb_status}</td>
						<td class="text-center">{mysqldb_createTime}</td>
						<td class="text-center">
							{op_type}
							<a onClick="return confirm('确认要去除 {name} 这个数据库？')" href="/assets/mysqldb_delete/{id}" class="btn btn-xs btn-danger del">删除</a>
						</td>
					</tr>
					'''.format(id=int(i[0]),name=i[1],assets_host_ip=i[2],mysqldb_status=mysqldb_status,mysqldb_createTime=i[4],op_type=op_type,hostid=int(i[5]))
	page_dict['page_content'] = page_cont_str

	return json.dumps(page_dict)

# MySQL数据库列表 - 批量操作功能视图
@assets.route('/mysqldb_list_bulk_ajax', methods=['GET', 'POST'])
@login_required
@admin_required
def mysqldb_list_bulk_ajax():
	data = request.get_json()
	bulk_ids = []
	result = {"status": 0, "msg": ''}
	if data['asset_update_array']:
		for i in data['asset_update_array']:
			bulk_ids.append(int(i))
		bulk_ids.append(0)
		bulk_id_tuple = tuple(bulk_ids)
		if data['type'] != 'delete':
			bulk_type = 1
			if data['type'] == 'active':
				bulk_type = 0
			elif data['type'] == 'deactive':
				bulk_type = 1
			bulk_mysqldb_sql = "UPDATE dbadmin_assets_mysqldb SET status={status} WHERE id IN {bulk_id_tuple} AND status != {status};".format(status=bulk_type,bulk_id_tuple=bulk_id_tuple)
		else:
			bulk_mysqldb_sql = "DELETE FROM dbadmin_assets_mysqldb WHERE id IN {bulk_id_tuple};".format(bulk_id_tuple=bulk_id_tuple)

		con = get_db()
		cursor = con.cursor()
		try:
			cursor.execute(bulk_mysqldb_sql)
			cursor.execute('COMMIT;')
		except Exception as e:
			result['status'] = 1
			result['msg'] = str(e)
			print(e)
	else:
		result['status'] = 1
		result['msg'] = "未选中任何DB!"

	return json.dumps(result)

# MySQL数据库列表 - 新增MySQL DB视图
@assets.route('/mysqldb_list/mysqldb_create', methods=['GET', 'POST'])
@login_required
@admin_required
def mysqldb_create():
	app = "资产管理"
	action = "新增MySQL数据库"
	if request.method == 'POST':
		con = get_db()
		cursor = con.cursor()

		assets_host_ip = request.form['assets_host_ip']
		assets_mysqldb_array = request.form['multi_select_base']
		assets_db_note = request.form.get('assets_db_note')
		assets_db_status = request.form.get('assets_db_status')
		currentTime = strftime("%Y-%m-%d %H:%M:%S")
		if assets_db_status:
			assets_db_status = 0
		else:
			assets_db_status = 1
		# 将字符串转换成列表，并且遍历改列表，拼接成多values的insert语句
		mysqldb_list = assets_mysqldb_array.split(',')
		get_hostid_sql = "SELECT id FROM dbadmin_assets_hosts WHERE ipaddress='{ipaddress}';".format(ipaddress=assets_host_ip)
		cursor.execute(get_hostid_sql)
		hostid = int(cursor.fetchall()[0][0])
		multi_values = ''
		for i in mysqldb_list:
			multi_values += "('{name}',{hostid},{status},'{createTime}','{note}'),".format(name=i,hostid=hostid,status=assets_db_status,createTime=currentTime,note=assets_db_note)
		# 将最后的逗号替换成分号,合成最终的insert语句
		insert_dbinfo_concat = "INSERT INTO dbadmin_assets_mysqldb(name,hostid,status,createTime,note) VALUES {multi_values}".format(multi_values=multi_values)
		regex = re.compile(',$')
		insert_dbinfo_sql = regex.sub(';',insert_dbinfo_concat)
		try:
			cursor.execute(insert_dbinfo_sql)
			cursor.execute("COMMIT;")
		except Exception as e:
			print(e)
		return redirect(url_for('assets.mysqldb_list'))

	return render_template('assets/mysqldb_create.html',app=app,action=action)

# MySQL数据库列表 - 新增MySQL DB 获取当前ip所包含数据库ajax
@assets.route('/mysqldb_create_getdb_ajax',methods=['GET', 'POST'])
@login_required
@admin_required
def mysqldb_create_getdb_ajax():
	'''
		用于multiselect2side获取当前ip地址对应的数据库名的视图
		:return: 数据库列表数据
	'''
	data = request.get_json()
	con = get_db()
	cursor = con.cursor()
	# 获取MySQL数据库的连接账号和密码,并且解密密码
	get_target_host_sql = "SELECT db_account,db_password,db_port,createTime FROM dbadmin_assets_hosts WHERE ipaddress='{ipaddress}' AND dbtype=0 AND status=0;".format(ipaddress=data['ipaddress'])
	cursor.execute(get_target_host_sql)
	get_target_host_result = cursor.fetchall()
	post_data = []
	if get_target_host_result:

		# 获取该MySQL实例中已经添加的逻辑库
		get_selected_db_sql = "SELECT A.name FROM dbadmin_assets_mysqldb A INNER JOIN dbadmin_assets_hosts B ON A.hostid=B.id WHERE B.ipaddress='{ipaddress}' AND B.dbtype=0 AND B.status=0;".format(
			ipaddress=data['ipaddress'])
		cursor.execute(get_selected_db_sql)
		get_selected_db_result = cursor.fetchall()

		get_target_host_list = list(get_target_host_result[0])
		createTimeStamp = str(int(mktime(strptime(get_target_host_list[3], "%Y-%m-%d %H:%M:%S"))))
		pc = prpcrypt(createTimeStamp)
		get_target_host_list[1] = pc.decrypt(get_target_host_list[1])

		# 连接对应的MySQL DB的实例
		try:
			new_conn = pymysql.connect(host=data['ipaddress'], user=get_target_host_list[0],passwd=get_target_host_list[1],port=get_target_host_list[2], charset='utf8')
			new_cursor = new_conn.cursor()
			new_cursor.execute("SHOW DATABASES;")
			get_target_db_result = new_cursor.fetchall()

			new_cursor.close()
			new_conn.close()

			black_list_db = ['information_schema','binlog','slowlog','sys','performance_schema']
			for j in get_selected_db_result:
				if j[0] not in black_list_db:
					black_list_db.append(j[0])
			for i in get_target_db_result:
				if i[0] not in black_list_db:
					post_data.append(i[0])
		except Exception as e:
			print(e)

	return json.dumps(post_data)

# MySQL数据库列表 - 启用禁用功能视图
@assets.route('/mysqldb_toggle/<int:id>/<int:status>', methods=['GET', 'POST'])
@login_required
@admin_required
def mysqldb_toggle(id,status):
	con = get_db()
	cursor = con.cursor()
	if status == 1:
		mysqldb_status = 0
	else:
		mysqldb_status = 1
	update_mysqldb_status_sql = "UPDATE dbadmin_assets_mysqldb SET status={status} WHERE id={id};".format(status=mysqldb_status,id=id)
	try:
		cursor.execute(update_mysqldb_status_sql)
		cursor.execute('COMMIT;')
	except Exception as e:
		print(e)

	return redirect(url_for('assets.mysqldb_list'))

# MySQL数据库列表 - 删除功能视图
@assets.route('/mysqldb_delete/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def mysqldb_delete(id):
	con = get_db()
	cursor = con.cursor()
	delete_mysqldb_sql = "DELETE FROM dbadmin_assets_mysqldb WHERE id='{id}';".format(id=id)
	try:
		cursor.execute(delete_mysqldb_sql)
		cursor.execute('COMMIT;')
	except Exception as e:
		print(e)

	return redirect(url_for('assets.mysqldb_list'))


