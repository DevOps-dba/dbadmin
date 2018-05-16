# -*- coding: utf-8 -*-
import requests
import time
import json

auth = ('grafana', 'l0e1pVSMb3gr$50Q5omZ')
# r = requests.get("http://prometheus.intra.im/api/v1/targets", auth=auth)
# print(r.json())

# name_list = []

# get_instances_check = requests.get('http://prometheus.intra.im/api/v1/series?match[]=mysql_global_status_questions{job="mysql"}', auth=auth)
# # print(get_instances_check.json())
# instances_list = []
# for i in get_instances_check.json()['data']:
#     instances_list.append(i['instance'])
# print(instances_list)

# currentTime = int(time.time())
# currentZeroTime = currentTime - currentTime % 86400

# # print(currentTime)
# # print(currentZeroTime)
# mysql_global_status_questions = requests.get('http://prometheus.intra.im/api/v1/query?query=mysql_global_status_questions{job="mysql",instance="mysql-metastore-1.db.dat.alsh.intra.im:9104",job="mysql"}[30s]&start='+ str(currentZeroTime) + '&end=' + str(currentTime) + '&step=30s', auth=auth)
# json_string = mysql_global_status_questions.json()
# print(json_string)
# value_list = json_string['data']['result'][0]['values']
# print(value_list)














