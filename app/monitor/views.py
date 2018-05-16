# -*- coding: utf-8 -*-
from flask import render_template, session, redirect, url_for, current_app, flash,abort,request,send_from_directory,g,_app_ctx_stack,jsonify
from . import monitor
from flask_login import login_user, logout_user, login_required,current_user
from .. import login_manager
from time import strftime, localtime, time
from ..decorators import admin_required
from werkzeug.security import generate_password_hash
import json
import string
import requests
import pymysql
from random import choice
from .. import get_db

import sys
reload(sys)
sys.setdefaultencoding('utf8')


'''
    prometheus python api for mysql bi
'''
@monitor.route('/prometheus_mysql_bi_service/<service_name>', methods=['GET', 'POST'])
def prometheus_mysql_bi_service(service_name):

    # 初始化对dbadmin系统后台数据库的访问
    con = get_db()
    cursor = con.cursor()
    cursor_dict = con.cursor(cursor=pymysql.cursors.DictCursor)

    # 获取监控项表的相关参数信息
    get_monitor_items_sql = "SELECT * FROM td_monitor_item WHERE item_name IS NOT NULL;"
    cursor_dict.execute(get_monitor_items_sql)
    monitor_items_result = cursor_dict.fetchall()
    name_list = []
    for g in monitor_items_result:
        if g['item_name']:
            name_list.append({"item_name": g['item_name'].encode('utf-8'), "item_id": g['id']})

    # print(monitor_items_result)
    # print(name_list)

    createTime = strftime("%Y-%m-%d")
    auth = ('grafana', 'l0e1pVSMb3gr$50Q5omZ')

    # 获取当前service下的所有instance名称
    get_instances_op = requests.get('http://prometheus.intra.im/api/v1/query?query=max(node_load1{env="prod",service=\"' + str(service_name) + '\"}) by (instance)', auth=auth)
    instances_list = []
    for i in get_instances_op.json()['data']['result']:
        instances_list.append(i['metric']['instance'].split(':')[0])
    # print(instances_list)

    # # 初始化监控项列表和时间范围
    # name_list = ["node_cpu", "node_memory_MemAvailable", "node_load1", "node_memory_SwapUsed", "node_filesystem_free_ratio", "node_disk_writes_latency", "node_disk_reads_latency", "node_disk_completed",
    #              "node_disk_io_usage", "node_network_receive_bytes", "node_network_transmit_bytes", "mysql_global_tps", "mysql_global_qps", "mysql_left_connections", "mysql_left_min_connections", "mysql_table_locks",
    #              "mysql_slow_queries", "mysql_bytes_received", "mysql_bytes_sent", "mysql_left_open_files", "mysql_slave_status_slave_io_running", "mysql_slave_status_slave_sql_running",
    #              "mysql_slave_status_seconds_behind_master", "mysql_info_schema_table_rows", "mysql_info_schema_table_size", "mysql_info_schema_table_free_size"]
    # name_list = ["mysql_global_tps"]
    stopTime = int(time())
    startTime = stopTime - stopTime % 86400
    # startTime = stopTime - 5 * 60


    insert_prometheus_mysql_bi_table_sql = "INSERT INTO tf_monitor_detail(service_name,instance_name,item_id,item_name,safety_threshold_nums,alert_threshold_nums,critical_threshold_nums,createTime) VALUES "
    # 遍历每个实例(system)，首先获取每个实例的cpu，然后对其每个监控项进行数据提取
    for j in instances_list:

        # 获取当前实例的cpu个数
        cpu_nums = requests.get('http://prometheus.intra.im/api/v1/query?query=count(count(node_cpu{service=\"' + str(service_name) + '\", env="prod",mode!="idle", instance=~\"^' + j + '.*\"}) by (cpu))', auth=auth)
        instance_cpu_nums = int(float(cpu_nums.json()['data']['result'][0]['value'][1]))

        # 获取当前实例的磁盘设备
        device_nums = requests.get('http://prometheus.intra.im/api/v1/query?query=count(node_disk_read_time_ms{service=\"' + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"}) by (device)', auth=auth)
        instance_device_list = []
        for x in device_nums.json()['data']['result']:
            instance_device_list.append(x['metric']['device'].encode("utf-8"))

        # 获取当前实例的网卡设备
        network_device_nums = requests.get('http://prometheus.intra.im/api/v1/query?query=count(node_network_receive_bytes{service=\"' + str(service_name) + '\", env="prod", device!="lo", instance=~\"^' + j + '.*\"}) by (device)', auth=auth)
        instance_network_device_list = []
        for x in network_device_nums.json()['data']['result']:
            instance_network_device_list.append(x['metric']['device'].encode("utf-8"))

        # 遍历每个监控项，初始化cal_nums字典，记录每个实例的告警值
        for m in name_list:
            setting_sign = 0
            cal_nums = {"safety_threshold_nums": 0, "alert_threshold_nums": 0, "critical_threshold_nums": 0}
            # CPU使用率
            if m['item_name'] == "node_cpu":
                node_cpu = requests.get('http://prometheus.intra.im/api/v1/query_range?query=sum(rate(node_cpu{service=\"'
                            + str(service_name) + '\",env="prod",mode!="idle", instance=~\"^' + j + '.*\"}[1m]))*100 / ' + str(instance_cpu_nums) + '&start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                output = node_cpu.json()
                if output['data']['result']:
                    for n in output['data']['result'][0]['values']:
                        n_float = float(n[1])
                        if n_float >= 50:
                            cal_nums['safety_threshold_nums'] += 1
                            if n_float >= 80:
                                cal_nums['alert_threshold_nums'] += 1
                                if n_float >= 90:
                                    cal_nums['critical_threshold_nums'] += 1
            # 有效内存
            elif m['item_name'] == "node_memory_MemAvailable":
                node_memory_MemAvailable = requests.get('http://prometheus.intra.im/api/v1/query_range?query=node_memory_MemAvailable{service=\"'
                            + str(service_name) + '\",env="prod", instance=~\"^' + j + '.*\"}&start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                output = node_memory_MemAvailable.json()
                if output['data']['result']:
                    for n in output['data']['result'][0]['values']:
                        n_int = int(float(n[1])/1024/1024)
                        if n_int <= 2048:
                            cal_nums['safety_threshold_nums'] += 1
                            if n_int <= 1024:
                                cal_nums['alert_threshold_nums'] += 1
                                if n_int <= 1024:
                                    cal_nums['critical_threshold_nums'] += 1
            # 最近一分钟负载
            elif m['item_name'] == "node_load1":
                node_load1 = requests.get('http://prometheus.intra.im/api/v1/query_range?query=node_load1{service=\"'
                            + str(service_name) + '\",env="prod", instance=~\"^' + j + '.*\"}&start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                output = node_load1.json()
                if output['data']['result']:
                    for n in output['data']['result'][0]['values']:
                        n_float = round(float(n[1])/instance_cpu_nums, 2)
                        if n_float >= 0.5:
                            cal_nums['safety_threshold_nums'] += 1
                            if n_float >= 0.7:
                                cal_nums['alert_threshold_nums'] += 1
                                if n_float >= 0.9:
                                    cal_nums['critical_threshold_nums'] += 1
            # Swap使用量
            elif m['item_name'] == "node_memory_SwapUsed":
                node_memory_SwapUsed = requests.get('http://prometheus.intra.im/api/v1/query_range?query=node_memory_SwapTotal{service=\"'
                                    + str(service_name) + '\",env="prod", instance=~\"^' + j + '.*\"} - node_memory_SwapFree{service=\"'
                                    + str(service_name) + '\",env="prod", instance=~\"^' + j + '.*\"}&start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                output = node_memory_SwapUsed.json()
                if output['data']['result']:
                    for n in output['data']['result'][0]['values']:
                        n_int = int(float(n[1]) / 1024 / 1024)
                        if n_int >= 100:
                            cal_nums['safety_threshold_nums'] += 1
                            if n_int >= 200:
                                cal_nums['alert_threshold_nums'] += 1
                                if n_int >= 500:
                                    cal_nums['critical_threshold_nums'] += 1
            # 磁盘各分区剩余空间比例
            elif m['item_name'] == "node_filesystem_free_ratio":
                get_mountpoint_request = requests.get('http://prometheus.intra.im/api/v1/series?match[]=node_filesystem_free{service=\"' + str(service_name) + '\",env="prod",instance=~\"^' + j + '.*\", loc="alsh", fstype!~"rootfs|selinuxfs|autofs|rpc_pipefs|tmpfs"}', auth=auth)
                for z in get_mountpoint_request.json()['data']:
                    mountpoint = z['mountpoint'].encode("utf-8")
                    node_filesystem_free_ratio = requests.get('http://prometheus.intra.im/api/v1/query_range?query=node_filesystem_free{service=\"'
                                    + str(service_name) + '\",env="prod", instance=~\"^' + j + '.*\",mountpoint=\"' + mountpoint + '\", fstype!~"rootfs|selinuxfs|autofs|rpc_pipefs|tmpfs"} * 100 / node_filesystem_size{service=\"'
                                    + str(service_name) + '\",env="prod", instance=~\"^' + j + '.*\",mountpoint=\"' + mountpoint + '\", fstype!~"rootfs|selinuxfs|autofs|rpc_pipefs|tmpfs"}&start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                    output = node_filesystem_free_ratio.json()
                    if output['data']['result']:
                        for n in output['data']['result'][0]['values']:
                            n_int = int(float(n[1].encode("utf-8")))
                            if n_int >= 80:
                                cal_nums['safety_threshold_nums'] += 1
                                if n_int >= 90:
                                    cal_nums['alert_threshold_nums'] += 1
                                    if n_int >= 95:
                                        cal_nums['critical_threshold_nums'] += 1
                        insert_prometheus_mysql_bi_table_sql += "('{service_name}','{instance_name}','{item_id}','{item_name}',{safety_threshold_nums},{alert_threshold_nums},{critical_threshold_nums},'{createTime}'),".format(
                            service_name=service_name, instance_name=j, item_id=m['item_id'], item_name=m['item_name'] + "__" + mountpoint, safety_threshold_nums=cal_nums['safety_threshold_nums'],alert_threshold_nums=cal_nums['alert_threshold_nums'],
                            critical_threshold_nums=cal_nums['critical_threshold_nums'], createTime=createTime)
                setting_sign = 1
            # 云SSD写延迟
            elif m['item_name'] == "node_disk_writes_latency":
                for y in instance_device_list:
                    node_disk_writes_latency = requests.get('http://prometheus.intra.im/api/v1/query_range?query=log2(max(rate(node_disk_write_time_ms{service=\"'
                                    + str(service_name) + '\",env="prod", instance=~\"^' + j + '.*\",device=\"' + y + '\"}[1m])) / max(rate(node_disk_writes_completed{service=\"'
                                    + str(service_name) + '\",env="prod", instance=~\"^' + j + '.*\",device=\"' + y + '\"}[1m])))' + '&start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                    output = node_disk_writes_latency.json()
                    if output['data']['result']:
                        for n in output['data']['result'][0]['values']:
                            if n[1] == "NaN" or n[1] == "+Inf":
                                pass
                            else:
                                n_float = float(n[1])
                                if n_float >= 2:
                                    cal_nums['safety_threshold_nums'] += 1
                                    if n_float >= 4:
                                        cal_nums['alert_threshold_nums'] += 1
                                        if n_float >= 8:
                                            cal_nums['critical_threshold_nums'] += 1
                        insert_prometheus_mysql_bi_table_sql += "('{service_name}','{instance_name}','{item_id}','{item_name}',{safety_threshold_nums},{alert_threshold_nums},{critical_threshold_nums},'{createTime}'),".format(
                            service_name=service_name, instance_name=j, item_id=m['item_id'], item_name=m['item_name'] + "__" + y, safety_threshold_nums=cal_nums['safety_threshold_nums'], alert_threshold_nums=cal_nums['alert_threshold_nums'],
                            critical_threshold_nums=cal_nums['critical_threshold_nums'], createTime=createTime)
                setting_sign = 1
            # 云SSD读延迟
            elif m['item_name'] == "node_disk_reads_latency":
                for y in instance_device_list:
                    node_disk_reads_latency = requests.get('http://prometheus.intra.im/api/v1/query_range?query=log2(max(rate(node_disk_read_time_ms{service=\"'
                                + str(service_name) + '\",env="prod", instance=~\"^' + j + '.*\",device=\"' + y + '\"}[1m])) / max(rate(node_disk_reads_completed{service=\"'
                                + str(service_name) + '\",env="prod", instance=~\"^' + j + '.*\",device=\"' + y + '\"}[1m])))' + '&start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                    output = node_disk_reads_latency.json()
                    if output['data']['result']:
                        for n in output['data']['result'][0]['values']:
                            if n[1] == "NaN" or n[1] == "+Inf":
                                pass
                            else:
                                n_float = float(n[1])
                                if n_float >= 2:
                                    cal_nums['safety_threshold_nums'] += 1
                                    if n_float >= 4:
                                        cal_nums['alert_threshold_nums'] += 1
                                        if n_float >= 8:
                                            cal_nums['critical_threshold_nums'] += 1
                        insert_prometheus_mysql_bi_table_sql += "('{service_name}','{instance_name}','{item_id}','{item_name}',{safety_threshold_nums},{alert_threshold_nums},{critical_threshold_nums},'{createTime}'),".format(
                            service_name=service_name, instance_name=j, item_id=m['item_id'], item_name=m['item_name'] + "__" + y, safety_threshold_nums=cal_nums['safety_threshold_nums'], alert_threshold_nums=cal_nums['alert_threshold_nums'],
                            critical_threshold_nums=cal_nums['critical_threshold_nums'], createTime=createTime)
                setting_sign = 1
            # 每个磁盘分区的利用率(%)
            elif m['item_name'] == "node_disk_io_usage":
                for y in instance_device_list:
                    node_disk_io_usage = requests.get('http://prometheus.intra.im/api/v1/query_range?query=rate(node_disk_read_time_ms{service=\"'
                                + str(service_name) + '\",env="prod", instance=~\"^' + j + '.*\",device=\"' + y + '\"}[1m]) / 1000 ' + '&start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                    output = node_disk_io_usage.json()
                    if output['data']['result']:
                        for n in output['data']['result'][0]['values']:
                            n_float = float(n[1])
                            if n_float >= 50:
                                cal_nums['safety_threshold_nums'] += 1
                                if n_float >= 80:
                                    cal_nums['alert_threshold_nums'] += 1
                                    if n_float >= 90:
                                        cal_nums['critical_threshold_nums'] += 1
                        insert_prometheus_mysql_bi_table_sql += "('{service_name}','{instance_name}','{item_id}','{item_name}',{safety_threshold_nums},{alert_threshold_nums},{critical_threshold_nums},'{createTime}'),".format(
                            service_name=service_name, instance_name=j, item_id=m['item_id'], item_name=m['item_name'] + "__" + y, safety_threshold_nums=cal_nums['safety_threshold_nums'], alert_threshold_nums=cal_nums['alert_threshold_nums'],
                            critical_threshold_nums=cal_nums['critical_threshold_nums'], createTime=createTime)
                setting_sign = 1
            # 云SSD每秒磁盘操作次数(iops read+write)
            elif m['item_name'] == "node_disk_completed":
                for y in instance_device_list:
                    node_disk_reads_completed = requests.get('http://prometheus.intra.im/api/v1/query_range?query=rate(node_disk_reads_completed{service=\"'
                                    + str(service_name) + '\",env="prod", instance=~\"^' + j + '.*\",device=\"' + y + '\"}[1m])' + '&start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                    reads_completed_output = node_disk_reads_completed.json()
                    node_disk_writes_completed = requests.get('http://prometheus.intra.im/api/v1/query_range?query=rate(node_disk_writes_completed{service=\"'
                                    + str(service_name) + '\",env="prod", instance=~\"^' + j + '.*\",device=\"' + y + '\"}[1m])' + '&start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                    writes_completed_output = node_disk_writes_completed.json()
                    if reads_completed_output['data']['result'] and writes_completed_output['data']['result']:
                        for n, o in enumerate(reads_completed_output['data']['result'][0]['values']):
                            n_float = float(o[1]) + float(writes_completed_output['data']['result'][0]['values'][n][1])
                            if n_float >= 5000:
                                cal_nums['safety_threshold_nums'] += 1
                                if n_float >= 7000:
                                    cal_nums['alert_threshold_nums'] += 1
                                    if n_float >= 10000:
                                        cal_nums['critical_threshold_nums'] += 1

                        insert_prometheus_mysql_bi_table_sql += "('{service_name}','{instance_name}','{item_id}','{item_name}',{safety_threshold_nums},{alert_threshold_nums},{critical_threshold_nums},'{createTime}'),".format(
                            service_name=service_name, instance_name=j, item_id=m['item_id'], item_name=m['item_name'] + "__" + y, safety_threshold_nums=cal_nums['safety_threshold_nums'], alert_threshold_nums=cal_nums['alert_threshold_nums'],
                            critical_threshold_nums=cal_nums['critical_threshold_nums'], createTime=createTime)
                setting_sign = 1
            # 网卡入流量
            elif m['item_name'] == "node_network_receive_bytes":
                for y in instance_network_device_list:
                    node_network_receive_bytes = requests.get('http://prometheus.intra.im/api/v1/query_range?query=rate(node_network_receive_bytes{service=\"'
                                    + str(service_name) + '\",env="prod", instance=~\"^' + j + '.*\",device=\"' + y + '\"}[1m]) / 1024 / 1024' + '&start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                    output = node_network_receive_bytes.json()
                    if output['data']['result']:
                        for n in output['data']['result'][0]['values']:
                            n_float = float(n[1])
                            if n_float >= 30:
                                cal_nums['safety_threshold_nums'] += 1
                                if n_float >= 50:
                                    cal_nums['alert_threshold_nums'] += 1
                                    if n_float >= 70:
                                        cal_nums['critical_threshold_nums'] += 1
                        insert_prometheus_mysql_bi_table_sql += "('{service_name}','{instance_name}','{item_id}','{item_name}',{safety_threshold_nums},{alert_threshold_nums},{critical_threshold_nums},'{createTime}'),".format(
                            service_name=service_name, instance_name=j, item_id=m['item_id'], item_name=m['item_name'] + "__" + y, safety_threshold_nums=cal_nums['safety_threshold_nums'], alert_threshold_nums=cal_nums['alert_threshold_nums'],
                            critical_threshold_nums=cal_nums['critical_threshold_nums'], createTime=createTime)
                setting_sign = 1
            # 网卡出流量
            elif m['item_name'] == "node_network_transmit_bytes":
                for y in instance_network_device_list:
                    node_network_transmit_bytes = requests.get('http://prometheus.intra.im/api/v1/query_range?query=rate(node_network_transmit_bytes{service=\"'
                                        + str(service_name) + '\",env="prod", instance=~\"^' + j + '.*\",device=\"' + y + '\"}[1m]) / 1024 / 1024' + '&start='
                                        + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                    output = node_network_transmit_bytes.json()
                    if output['data']['result']:
                        for n in output['data']['result'][0]['values']:
                            n_float = float(n[1])
                            if n_float >= 50:
                                cal_nums['safety_threshold_nums'] += 1
                                if n_float >= 80:
                                    cal_nums['alert_threshold_nums'] += 1
                                    if n_float >= 100:
                                        cal_nums['critical_threshold_nums'] += 1
                        insert_prometheus_mysql_bi_table_sql += "('{service_name}','{instance_name}','{item_id}','{item_name}',{safety_threshold_nums},{alert_threshold_nums},{critical_threshold_nums},'{createTime}'),".format(
                            service_name=service_name, instance_name=j, item_id=m['item_id'], item_name=m['item_name'] + "__" + y, safety_threshold_nums=cal_nums['safety_threshold_nums'], alert_threshold_nums=cal_nums['alert_threshold_nums'],
                            critical_threshold_nums=cal_nums['critical_threshold_nums'], createTime=createTime)
                setting_sign = 1
            # MySQL TPS
            elif m['item_name'] == "mysql_global_tps":
                mysql_global_tps = requests.get('http://prometheus.intra.im/api/v1/query_range?query=sum(rate(mysql_global_status_commands_total{service=\"'
                            + str(service_name) + '\", env="prod", command=~"insert|update|delete|replace", instance=~\"^' + j + '.*\"}[1m])) by (instance) &start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                output = mysql_global_tps.json()
                if output['data']['result']:
                    for n in output['data']['result'][0]['values']:
                        n_float = float(n[1])
                        if n_float >= 3000:
                            cal_nums['safety_threshold_nums'] += 1
                            if n_float >= 5000:
                                cal_nums['alert_threshold_nums'] += 1
                                if n_float >= 7000:
                                    cal_nums['critical_threshold_nums'] += 1
            # MySQL - QPS
            elif m['item_name'] == "mysql_global_qps":
                mysql_global_qps = requests.get('http://prometheus.intra.im/api/v1/query_range?query=rate(mysql_global_status_queries{service=\"'
                            + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"}[1m]) &start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                output = mysql_global_qps.json()
                if output['data']['result']:
                    for n in output['data']['result'][0]['values']:
                        n_float = float(n[1])
                        if n_float >= 5000:
                            cal_nums['safety_threshold_nums'] += 1
                            if n_float >= 10000:
                                cal_nums['alert_threshold_nums'] += 1
                                if n_float >= 15000:
                                    cal_nums['critical_threshold_nums'] += 1
            # MySQL - 剩余连接数
            elif m['item_name'] == "mysql_left_connections":
                mysql_left_connections = requests.get('http://prometheus.intra.im/api/v1/query_range?query=100 - (mysql_global_status_threads_connected{service=\"'
                                + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"} * 100 / mysql_global_variables_max_connections{service=\"'
                                + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"})&start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                output = mysql_left_connections.json()
                if output['data']['result']:
                    for n in output['data']['result'][0]['values']:
                        n_int = int(float(n[1]))
                        if n_int <= 50:
                            cal_nums['safety_threshold_nums'] += 1
                            if n_int <= 30:
                                cal_nums['alert_threshold_nums'] += 1
                                if n_int <= 10:
                                    cal_nums['critical_threshold_nums'] += 1
            # MySQL - 历史剩余最少连接数
            elif m['item_name'] == "mysql_left_min_connections":
                mysql_left_min_connections = requests.get('http://prometheus.intra.im/api/v1/query?query=100 - (mysql_global_status_max_used_connections{service=\"'
                            + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"} * 100 / mysql_global_variables_max_connections{service=\"'
                            + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"})', auth=auth)
                output = mysql_left_min_connections.json()
                if output['data']['result']:
                    n_float = float(output['data']['result'][0]['value'][1])
                    if n_float <= 50:
                        cal_nums['safety_threshold_nums'] += 1
                        if n_float <= 30:
                            cal_nums['alert_threshold_nums'] += 1
                            if n_float <= 10:
                                cal_nums['critical_threshold_nums'] += 1
            # MySQL - 锁的数量
            elif m['item_name'] == "mysql_table_locks":
                mysql_table_locks = requests.get('http://prometheus.intra.im/api/v1/query_range?query=rate(mysql_global_status_table_locks_immediate{service=\"'
                            + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"}[1m]) &start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                output = mysql_table_locks.json()
                if output['data']['result']:
                    for n in output['data']['result'][0]['values']:
                        n_float = float(n[1])
                        if n_float >= 5:
                            cal_nums['safety_threshold_nums'] += 1
                            if n_float >= 10:
                                cal_nums['alert_threshold_nums'] += 1
                                if n_float >= 20:
                                    cal_nums['critical_threshold_nums'] += 1
            # MySQL - 慢查询的数量
            elif m['item_name'] == "mysql_slow_queries":
                mysql_slow_queries = requests.get('http://prometheus.intra.im/api/v1/query_range?query=rate(mysql_global_status_slow_queries{service=\"'
                            + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"}[1m]) &start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                output = mysql_slow_queries.json()
                if output['data']['result']:
                    for n in output['data']['result'][0]['values']:
                        n_float = float(n[1])
                        if n_float >= 3:
                            cal_nums['safety_threshold_nums'] += 1
                            if n_float >= 5:
                                cal_nums['alert_threshold_nums'] += 1
                                if n_float >= 10:
                                    cal_nums['critical_threshold_nums'] += 1
            # MySQL - 进流量
            elif m['item_name'] == "mysql_bytes_received":
                mysql_bytes_received = requests.get('http://prometheus.intra.im/api/v1/query_range?query=rate(mysql_global_status_bytes_received{service=\"'
                                + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"}[1m]) / 1024 / 1024 &start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                output = mysql_bytes_received.json()
                if output['data']['result']:
                    for n in output['data']['result'][0]['values']:
                        n_float = float(n[1])
                        if n_float >= 5:
                            cal_nums['safety_threshold_nums'] += 1
                            if n_float >= 10:
                                cal_nums['alert_threshold_nums'] += 1
                                if n_float >= 15:
                                    cal_nums['critical_threshold_nums'] += 1
            # MySQL 出流量
            elif m['item_name'] == "mysql_bytes_sent":
                mysql_bytes_sent = requests.get('http://prometheus.intra.im/api/v1/query_range?query=rate(mysql_global_status_bytes_received{service=\"'
                                + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"}[1m]) / 1024 / 1024 &start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                output = mysql_bytes_sent.json()
                if output['data']['result']:
                    for n in output['data']['result'][0]['values']:
                        n_float = float(n[1])
                        if n_float >= 50:
                            cal_nums['safety_threshold_nums'] += 1
                            if n_float >= 80:
                                cal_nums['alert_threshold_nums'] += 1
                                if n_float >= 100:
                                    cal_nums['critical_threshold_nums'] += 1
            # MySQL - 剩余可打开文件数量
            elif m['item_name'] == "mysql_left_open_files":
                mysql_left_open_files = requests.get('http://prometheus.intra.im/api/v1/query_range?query=(mysql_global_variables_open_files_limit{service=\"'
                            + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"}  - mysql_global_status_open_files{service=\"'
                            + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"} - mysql_global_status_innodb_num_open_files{service=\"'
                            + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"}) * 100 / mysql_global_variables_open_files_limit{service=\"'
                            + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"}&start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                output = mysql_left_open_files.json()
                if output['data']['result']:
                    for n in output['data']['result'][0]['values']:
                        n_float = float(n[1])
                        if n_float <= 50:
                            cal_nums['safety_threshold_nums'] += 1
                            if n_float <= 30:
                                cal_nums['alert_threshold_nums'] += 1
                                if n_float <= 10:
                                    cal_nums['critical_threshold_nums'] += 1
            # MySQL - 表缓存命中率
            # elif m['item_name'] == "mysql_table_cache_ratio":
            #     mysql_table_cache_ratio = requests.get('http://prometheus.intra.im/api/v1/query_range?query=rate(mysql_global_status_table_open_cache_hits{service=\"'
            #                     + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"})  / (rate(mysql_global_status_table_open_cache_hits{service=\"'
            #                     + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"}) + rate(mysql_global_status_table_open_cache_misses{service=\"'
            #                     + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"}))&start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
            #     output = mysql_table_cache_ratio.json()
            #     if output['data']['result']:
            #     # for n in output['data']['result'][0]['values']:
            #     #     n_float = float(n[1])
            #     #     if n_float <= 50:
            #     #         cal_nums['safety_threshold_nums'] += 1
            #     #         if n_float <= 30:
            #     #             cal_nums['alert_threshold_nums'] += 1
            #     #             if n_float <= 10:
            #     #                 cal_nums['critical_threshold_nums'] += 1
            # MySQL - 主从io线程状态
            # MySQL - 主从iO线程状态
            elif m['item_name'] == "mysql_slave_status_slave_io_running":
                mysql_slave_status_slave_io_running = requests.get('http://prometheus.intra.im/api/v1/query_range?query=mysql_slave_status_slave_io_running{service=\"'
                                    + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"} &start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                output = mysql_slave_status_slave_io_running.json()
                if output['data']['result']:
                    for n in output['data']['result'][0]['values']:
                        n_int = int(float(n[1]))
                        if n_int == 0:
                            cal_nums['critical_threshold_nums'] += 1
                else:
                    setting_sign = 1
            # MySQL - 主从sql线程状态
            elif m['item_name'] == "mysql_slave_status_slave_sql_running":
                mysql_slave_status_slave_sql_running = requests.get('http://prometheus.intra.im/api/v1/query_range?query=mysql_slave_status_slave_sql_running{service=\"'
                                + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"} &start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                output = mysql_slave_status_slave_sql_running.json()

                if output['data']['result']:
                    for n in output['data']['result'][0]['values']:
                        n_int = int(float(n[1]))
                        if n_int == 0:
                            cal_nums['critical_threshold_nums'] += 1
                else:
                    setting_sign = 1
            # MySQL - 主从延迟
            elif m['item_name'] == "mysql_slave_status_seconds_behind_master":
                mysql_slave_status_seconds_behind_master = requests.get('http://prometheus.intra.im/api/v1/query_range?query=mysql_slave_status_seconds_behind_master{service=\"'
                                    + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"} &start=' + str(startTime) + '&end=' + str(stopTime) + '&step=1m', auth=auth)
                output = mysql_slave_status_seconds_behind_master.json()
                if output['data']['result']:
                    for n in output['data']['result'][0]['values']:
                        n_int = int(float(n[1]))
                        if n_int >= 1:
                            cal_nums['safety_threshold_nums'] += 1
                            if n_int >= 5:
                                cal_nums['alert_threshold_nums'] += 1
                                if n_int >= 60:
                                    cal_nums['critical_threshold_nums'] += 1
                else:
                    setting_sign = 1
            # MySQL - 表的行数
            elif m['item_name'] == "mysql_info_schema_table_rows":
                mysql_info_schema_table_rows = requests.get('http://prometheus.intra.im/api/v1/query?query=mysql_info_schema_table_rows{service=\"'
                                + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"}', auth=auth)
                output = mysql_info_schema_table_rows.json()
                if output['data']['result']:
                    for n in output['data']['result']:
                        n_int = int(float(n["value"][1]))
                        if n_int >= 10000000:
                            cal_nums['safety_threshold_nums'] += 1
                            if n_int >= 30000000:
                                cal_nums['alert_threshold_nums'] += 1
                                if n_int >= 100000000:
                                    cal_nums['critical_threshold_nums'] += 1
            # MySQL - 所占空间
            elif m['item_name'] == "mysql_info_schema_table_size":
                mysql_info_schema_table_size = requests.get('http://prometheus.intra.im/api/v1/query?query=sum(mysql_info_schema_table_size{service=\"'
                                    + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"}) by (table)', auth=auth)
                output = mysql_info_schema_table_size.json()
                if output['data']['result']:
                    for n in output['data']['result']:
                        n_int = int(float(n["value"][1]))
                        if n_int >= 1024*1024*1024:
                            cal_nums['safety_threshold_nums'] += 1
                            if n_int >= 3*1024*1024*1024:
                                cal_nums['alert_threshold_nums'] += 1
                                if n_int >= 10*1024*1024*1024:
                                    cal_nums['critical_threshold_nums'] += 1
            # # MySQL - 碎片空间
            # elif m['item_name'] == "mysql_info_schema_table_free_size":
            #     mysql_info_schema_table_free_size = requests.get('http://prometheus.intra.im/api/v1/query?query=mysql_info_schema_table_size{service=\"'
            #                         + str(service_name) + '\", env="prod", component="data_free", instance=~\"^' + j + '.*\"} / on (env,instance,schema,table) (mysql_info_schema_table_size{service=\"'
            #                         + str(service_name) + '\", env="prod", component="data_length",instance=~\"^' + j + '.*\"} + on (env,instance,schema,table) mysql_info_schema_table_size{service=\"'
            #                         + str(service_name) + '\", env="prod", component="data_free",instance=~\"^' + j + '.*\"})', auth=auth)
            #     output = mysql_info_schema_table_free_size.json()
            #     if output['data']['result']:
            #     print(output)
            #     # for n in output['data']['result']:
            #     #     n_int = int(float(n["value"][1]))
            #     #     if n_int >= 1024 * 1024 * 1024:
            #     #         cal_nums['safety_threshold_nums'] += 1
            #     #         if n_int >= 3 * 1024 * 1024 * 1024:
            #     #             cal_nums['alert_threshold_nums'] += 1
            #     #             if n_int >= 10 * 1024 * 1024 * 1024:
            #     #                 cal_nums['critical_threshold_nums'] += 1

            if setting_sign == 0:
                insert_prometheus_mysql_bi_table_sql += "('{service_name}','{instance_name}', '{item_id}', '{item_name}',{safety_threshold_nums},{alert_threshold_nums},{critical_threshold_nums},'{createTime}'),".format(
                    service_name=service_name, instance_name=j, item_id=m['item_id'], item_name=m['item_name'], safety_threshold_nums=cal_nums['safety_threshold_nums'], alert_threshold_nums=cal_nums['alert_threshold_nums'],
                    critical_threshold_nums=cal_nums['critical_threshold_nums'], createTime=createTime)

    insert_prometheus_mysql_bi_table_sql = insert_prometheus_mysql_bi_table_sql.rstrip(',') + ';'
    cursor.execute(insert_prometheus_mysql_bi_table_sql)
    cursor.execute('commit;')

    # 遍历每个实例(system)，首先获取每个实例的cpu，然后对其每个监控项进行数据提取
    # for j in instances_list:
    #
    #     # 获取当前实例的cpu个数
    #     cpu_nums = requests.get('http://prometheus.intra.im/api/v1/query?query=count(count(node_cpu{service=\"' + str(service_name) + '\", env="prod",mode!="idle", instance=~\"^' + j + '.*\"}) by (cpu))', auth=auth)
    #     instance_cpu_nums = int(float(cpu_nums.json()['data']['result'][0]['value'][1]))
    #
    #     # 获取当前实例的磁盘设备
    #     device_nums = requests.get('http://prometheus.intra.im/api/v1/query?query=count(node_disk_read_time_ms{service=\"' + str(service_name) + '\", env="prod", instance=~\"^' + j + '.*\"}) by (device)', auth=auth)
    #     instance_device_list = []
    #     for x in device_nums.json()['data']['result']:
    #         instance_device_list.append(x['metric']['device'].encode("utf-8"))
    #
    #     # 获取当前实例的网卡设备
    #     network_device_nums = requests.get('http://prometheus.intra.im/api/v1/query?query=count(node_network_receive_bytes{service=\"' + str(service_name) + '\", env="prod", device!="lo", instance=~\"^' + j + '.*\"}) by (device)', auth=auth)
    #     instance_network_device_list = []
    #     for x in network_device_nums.json()['data']['result']:
    #         instance_network_device_list.append(x['metric']['device'].encode("utf-8"))
    #
    #     # 遍历每个监控项，初始化cal_nums字典，记录每个实例的告警值
    #     for m in monitor_items_result:
    #         setting_sign = 0
    #         cal_nums = {"safety_threshold_nums": 0, "alert_threshold_nums": 0, "critical_threshold_nums": 0}
    #         query_statement = m['expression']
    #         query_statement = query_statement.replace('startTime', str(startTime)).replace('service_name', service_name).replace('instance_name', j).replace('instance_cpu_nums', str(instance_cpu_nums)).replace('stopTime', str(stopTime))
    #         # query_range?query=sum(rate(node_cpu{service="service_name",env="prod",mode!="idle", instance=~"^instance_name.*"}[1m]))*100 / instance_cpu_nums&start=startTime&end=stopTime&step=1m
    #         # print('http://prometheus.intra.im/api/v1/{query_statement}'.format(query_statement=query_statement))
    #         print('http://prometheus.intra.im/api/v1/' + query_statement)
    #         item_obj = requests.get('http://prometheus.intra.im/api/v1/' + query_statement, auth=auth)
    #         print(item_obj.json())

    return ''

@monitor.route('/prometheus_mysql_bi', methods=['GET', 'POST'])
def prometheus_mysql_bi():
    auth = ('grafana', 'l0e1pVSMb3gr$50Q5omZ')

    # 获取当前prod环境的所有service_name
    get_service_names_op = requests.get('http://prometheus.intra.im/api/v1/query?query=max(node_load1{env="prod", job="mysql"}) by (service)', auth=auth)
    output = get_service_names_op.json()
    services_list = []
    total_start_time = int(time())
    for i in output['data']['result']:
        services_list.append(i['metric']['service'].encode('utf-8'))
        start_time = int(time())
        print("{time} - service:'{service_name}' : begining pull prometheus data...".format(time=strftime("%Y-%m-%d %H:%M:%S"), service_name=i['metric']['service'].encode('utf-8')))
        # 获取每个service的所有数据
        prometheus_mysql_bi_service(i['metric']['service'].encode('utf-8'))
        elapsed_time = int(time()) - start_time
        print("{time} - service:'{service_name}' : finished pull prometheus data. Elapsed Time [{duration}s]!".format(time=strftime("%Y-%m-%d %H:%M:%S"), service_name=i['metric']['service'].encode('utf-8'), duration=elapsed_time))
    total_elapsed_time = int(time()) - total_start_time
    print("{time} - ALL services task is done : Elapsed Time of Total [{total_time}s]!".format(time=strftime("%Y-%m-%d %H:%M:%S"), total_time=total_elapsed_time))

    return jsonify(services_list)

@monitor.route('/get_prometheus_json/<service_name>/<select_time>', methods=['GET', 'POST'])
def get_prometheus_json(service_name, select_time):

    # 初始化对dbadmin系统后台数据库的访问
    con = get_db()
    cursor = con.cursor(cursor=pymysql.cursors.DictCursor)

    get_monitor_detail_sql = "SELECT a.category,a.sub_category,a.object,a.item_name,a.item_comment,b.item_name AS sub_item,b.safety_threshold_nums,b.alert_threshold_nums,b.critical_threshold_nums FROM td_monitor_item a INNER JOIN tf_monitor_detail b ON a.id=b.item_id " \
                             "WHERE service_name='{service_name}' AND createTime='{createTime}';".format(service_name=service_name, createTime=select_time)
    cursor.execute(get_monitor_detail_sql)
    get_monitor_detail_result = cursor.fetchall()
    output = []
    for i in get_monitor_detail_result:
        if i['sub_item'] == i['item_name']:
            i['sub_item'] = ''
        else:
            i['sub_item'] = i['sub_item'].split('__')[1]

        output.append({"category": i["category"], "sub_category": i['sub_category'], "item_comment": i['item_comment'], "sub_item": i['sub_item'],
                       "safety_value": i['safety_threshold_nums'], "warning_value": i['alert_threshold_nums'], "critical_value": i['critical_threshold_nums']})
    data = {"data": output}

    print(data)

    return jsonify(data)

@monitor.route('/get_prometheus_html/<service_name>/<select_time>', methods=['GET', 'POST'])
def get_prometheus_html(service_name, select_time):

    # 初始化对dbadmin系统后台数据库的访问
    con = get_db()
    cursor = con.cursor(cursor=pymysql.cursors.DictCursor)

    get_monitor_detail_sql = "SELECT a.category,a.sub_category,a.object,a.item_name,a.item_comment,b.item_name AS sub_item,b.safety_threshold_nums,b.alert_threshold_nums,b.critical_threshold_nums " \
                             "FROM td_monitor_item a INNER JOIN tf_monitor_detail b ON a.id=b.item_id " \
                             "WHERE service_name='{service_name}' AND createTime='{createTime}';".format(service_name=service_name, createTime=select_time)

    cursor.execute(get_monitor_detail_sql)
    get_monitor_detail_result = cursor.fetchall()
    output = []

    page_cont_str = ''
    for i in get_monitor_detail_result:
        if i['sub_item'] == i['item_name']:
            i['sub_item'] = ''
        else:
            i['sub_item'] = i['sub_item'].split('__')[1]

        page_cont_str += '''
        					<tr class="gradeX">
        						<td class="text-center">{category}</td>
        						<td class="text-center">{object}</td>
        						<td class="text-center" title="">{item_name}</td>
        						<td class="text-center">{sub_item_name}</td>
        						<td class="text-center" >{safety_value}</td>
        						<td class="text-center">{warning_value}</td>
        						<td class="text-center">{critical_value}</td>
        					</tr>
        					'''.format(category=i['sub_category'], object=i['object'], item_name=i['item_comment'], sub_item_name=i['sub_item'], safety_value=i['safety_threshold_nums'], warning_value=i['alert_threshold_nums'], critical_value=i['critical_threshold_nums'])

    main_table_html = '''
                    <!DOCTYPE html>
                    <html lang="en">
                        <head>
                          <title>Bootstrap Example</title>
                          <meta charset="utf-8">
                          <meta name="viewport" content="width=device-width, initial-scale=1">
                          <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
                          <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
                          <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>
                        </head>
                        <body>
                        
                            <div class="container">
                                  <h2>数据库健康状态日报</h2>
                                  <p>。。。</p>
                                <table class="table table-striped table-bordered table-hover dataTable no-footer">
                                <thead>
                                    <tr>
                                        <th class="text-center">监控类</th>
                                        <th class="text-center">监控对象</th>
                                        <th class="text-center">监控项</th>
                                        <th class="text-center">监控子项</th>
                                        <th class="text-center">安全值</th>
                                        <th class="text-center">告警值</th>
                                        <th class="text-center">临界值</th>
                                    </tr>
                                </thead>
                                <tbody>{html_detail}</tbody>
                                </table>
                            </div>
                        </body>
                    </html>

                '''.format(html_detail=page_cont_str)

    return render_template(main_table_html)

# prometheus监控报表列表 - 页面视图
@monitor.route('/monitor_prometheus_list', methods=['GET', 'POST'])
@login_required
@admin_required
def monitor_prometheus_list():
    app = "监控管理"
    action = "报表列表"
    return render_template('monitor/monitor_prometheus_list.html', app=app, action=action)

# prometheus监控报表列表 - ajax视图
@monitor.route('/monitor_prometheus_list_ajax', methods=['GET', 'POST'])
@login_required
@admin_required
def monitor_prometheus_list_ajax():
    # 获取ajax中传递的request的data值
    page_dict = {'page_content': None, 'page_count': None, 'per_page': None}
    data = request.get_json()

    # 初始化对dbadmin系统后台数据库的访问
    con = get_db()
    cursor = con.cursor()

    # 对非空的条件进行SQL语句拼接
    page = int(data['page'])
    condition = 'WHERE 1=1'
    if data['promlist_service_name']:
        condition += " AND A.service_name = '{service_name}'".format(service_name=data['promlist_service_name'].strip())
    if data['promlist_item_name']:
        condition += " AND B.item_name = '{item_name}'".format(item_name=int(data['promlist_item_name']))
    if data['promlist_datetime']:
        condition += " AND A.createTime = '{createTime}'".format(createTime=int(data['promlist_datetime']))

    # 获取总数据行数
	promlist_count_sql = "SELECT COUNT(A.id) FROM tf_monitor_detail A  INNER JOIN td_monitor_item B ON A.item_id=B.id {condition};".format(condition=condition)
    cursor.execute(promlist_count_sql)
    promlistcount_result = cursor.fetchall()
    page_dict['page_count'] = promlistcount_result[0][0]
    if int(data['promlist_data_length']) != 100:
        page_dict['per_page'] = int(data['promlist_data_length'])
        per_page = int(data['promlist_data_length'])
    else:
        page_dict['per_page'] = int(promlistcount_result[0][0])
        per_page = int(promlistcount_result[0][0])

    # 获取首页展示的数据
    promlist_select_sql = "SELECT B.sub_category,B.object,B.item_comment,A.item_name AS sub_item,A.safety_threshold_nums,A.alert_threshold_nums,A.critical_threshold_nums FROM tf_monitor_detail A  INNER JOIN td_monitor_item B ON A.item_id=B.id {condition} ORDER BY A.id DESC LIMIT {start},{per_page};".format(
        start=(page - 1) * per_page, condition=condition, per_page=per_page)
    cursor.execute(promlist_select_sql)
    promlist_result = cursor.fetchall()

    page_cont_str = ''
    for i in promlist_result:

        page_cont_str += '''
					<tr class="gradeX">
						<td class="text-center">{category}</td>
                        <td class="text-center">{object}</td>
                        <td class="text-center" title="">{item_name}</td>
                        <td class="text-center">{sub_item_name}</td>
                        <td class="text-center" >{safety_value}</td>
                        <td class="text-center">{warning_value}</td>
                        <td class="text-center">{critical_value}</td>
					</tr>
					'''.format(category=i[0], object=i[1], item_name=i[2], sub_item_name=i[3], safety_value=i[4], warning_value=i[5], critical_value=i[6])
    page_dict['page_content'] = page_cont_str

    return json.dumps(page_dict)

