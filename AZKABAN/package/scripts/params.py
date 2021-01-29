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

# config object that holds the configurations declared in the config xml file

config = Script.get_config()

azkaban_env = config['configurations']['azkaban-env']
azkaban_web_properties = config['configurations']['azkaban-web.properties']
azkaban_executor_properties = config['configurations']['azkaban-executor.properties']

azkaban_users = config['configurations']['azkaban-users']

azkaban_db = config['configurations']['azkaban-db']
global_properties = config['configurations']['global.properties']
log4j_properties = config['configurations']['log4j.properties']

azkaban_user = azkaban_env["azkaban_user"]
user_group = config['configurations']['cluster-env']['user_group']

azkaban_admin_username = azkaban_env['azkaban.manager.username']
azkaban_admin_password = azkaban_env['azkaba.manager.password']

azkaban_web_home = azkaban_env["azkaban.web.home"]
azkaban_exec_home = azkaban_env["azkaban.executor.home"]

azkaban_log_dir = azkaban_env["azkaban.log.dir"]