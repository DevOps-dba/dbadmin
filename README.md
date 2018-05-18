DBadmin

数据库自动化操作系统

开发语言和推荐环境：
python：2.7.14 
django：0.11.1 
mysql : 5.7.20 
linux : win10 或者 64位linux操作系统均可

主要功能：
1),用户认证管理系统
2),资产管理系统
3),数据库监控系统
4),自动审核系统

主要配置文件：
app/config.py

安装步骤：
环境准备：
(1)克隆代码到本地: git clone https://github.com/DevOps-dba/DjangoFirstProgram.git 或 下载zip包 
(2)安装mysql 5.7实例，请注意保证mysql数据库默认字符集为utf8或utf8mb4 \

安装python2：(强烈建议使用virtualenv或venv等单独隔离环境！) 
tar -xzvf Python-2.7.14.tar.gz 
cd Python-2.7.14 
./configure --prefix=/path/to/python2 && make && make install 或者rpm、yum、binary等其他安装方式

安装所需相关模块：
(1)django： 
pip3 install Django 
(3)其他模块: 
pip3 install -r requirements.txt