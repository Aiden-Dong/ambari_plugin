#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from resource_management.libraries.script.script import Script
from resource_management.libraries.functions.default import default
from resource_management.libraries.functions import conf_select

# config object that holds the configurations declared in the config xml file
config = Script.get_config()

print(config)

flink_env = config['configurations']['flink-env']
flink_conf = config['configurations']['flink-conf']

# FLINK_HISTORYSERVER
flink_jobhistoryserver_hosts = default("/clusterHostInfo/flink_historyserver_hosts", [])

flink_history_server_host = "localhost"

if len(flink_jobhistoryserver_hosts) > 0:
  flink_history_server_host = flink_jobhistoryserver_hosts[0]


flink_user = config['configurations']['flink-env']['flink_user']
user_group = config['configurations']['cluster-env']['user_group']

hadoop_conf_dir = conf_select.get_hadoop_conf_dir()

flink_home = '/usr/hdp/current/flink'
flink_conf_dir = "/etc/flink/conf"

flink_config_file ="flink-conf.yaml"
