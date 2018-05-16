# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField,SelectField
from wtforms.validators import  Length, Regexp, EqualTo,InputRequired
from wtforms import ValidationError
from .. import get_db

class LoginForm(FlaskForm):
	account = StringField('账号', validators=[InputRequired(),Length(1, 64)])
	password = PasswordField('密码', validators=[InputRequired()])
	remember_me = BooleanField('记住密码')
	submit = SubmitField('登录')

# class RegistrationForm(FlaskForm):
# 	dept = SelectField('所属部门', validators=[InputRequired()],choices=[('', '请选择部门'), ('1', '系统运维部'), ('2', 'POP产品研发部'), ('3', '财务产品研发部'),
# 								('4', '商城产品研发部'), ('5', '钢银钱庄研发部'), ('6', '物流加工研发部'),
# 								('7', '自营产品研发部'),('8', '数据产品研发部'), ('9', '钢联运营中心'),('10','进销存产品研发部'),('11','OA产品研发部')])
# 	name =  StringField('真实姓名', validators=[InputRequired()])
# 	username = StringField('用户名', validators=[InputRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,'用户名只能使用字符串、数字和*%等特殊字符')])
# 	password = PasswordField('密码', validators=[InputRequired(), EqualTo('password2', message='两次密码不一致')])
# 	password2 = PasswordField('确认密码', validators=[InputRequired()])
# 	question = StringField('密保问题：谁是产品研发中心最帅的人(请勿填写简单答案)？', validators=[InputRequired()])
# 	submit = SubmitField('注册')
#
# 	def validate_username(self, field):
# 		con = get_db()
# 		cursor = con.cursor()
# 		checkUserSql = "SELECT 1 FROM users WHERE username = '{username}';".format(username=field.data)
# 		cursor.execute(checkUserSql)
# 		checkresult = cursor.fetchall()
# 		if checkresult:
# 			raise ValidationError('用户名已存在.')
#
# class changePasswdForm(FlaskForm):
# 	username = StringField('用户名', validators=[InputRequired(), Length(1, 64)])
# 	password = PasswordField('新密码', validators=[InputRequired(), EqualTo('password2', message='两次密码不一致')])
# 	password2 = PasswordField('确认密码', validators=[InputRequired()])
# 	email = StringField('密保问题：谁是产品研发中心最帅的人？', validators=[InputRequired()])
# 	newQuestion = StringField('新密保答案', validators=[InputRequired()])
# 	submit = SubmitField('提交')
#
# 	def validate_username(self, field):
# 		con = get_db()
# 		cursor = con.cursor()
# 		checkUserSql = "SELECT 1 FROM users WHERE username = '{username}';".format(username=field.data)
# 		cursor.execute(checkUserSql)
# 		checkresult = cursor.fetchall()
# 		if not checkresult:
# 			raise ValidationError('用户名不存在.')
#
# 	def validate_email(self, field):
# 		con = get_db()
# 		cursor = con.cursor()
# 		checkUserSql = "SELECT 1 FROM users WHERE question = '{question}';".format(question=field.data)
# 		cursor.execute(checkUserSql)
# 		checkresult = cursor.fetchall()
# 		if not checkresult:
# 			raise ValidationError('验证答案错误.')
#
# class manageForm(FlaskForm):
# 	name = StringField('')
# 	status = SelectField('',choices=[('','请选择状态'),('0','禁用'),('1','启用')])
# 	submit = SubmitField('提交')
#
# class dbMangementForm(FlaskForm):
# 	name = StringField('', validators=[InputRequired()])
# 	ipaddress = StringField('', validators=[InputRequired()])
# 	port = StringField('', validators=[InputRequired()])
# 	submit = SubmitField('新增')



