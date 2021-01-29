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

import os.path as path
import time
import socket
import urllib2
import base64
import json

from common import AZKABAN_EXECUTOR_URL, AZKABAN_NAME
from ambari_commons.inet_utils import openurl
from resource_management.core.exceptions import Fail
from resource_management.core.exceptions import ExecutionFailed, ComponentIsNotRunning
from resource_management.core.resources.system import Execute, Directory
from resource_management.libraries.script.script import Script
from resource_management.libraries.functions.check_process_status import check_process_status
from resource_management.libraries.functions.format import format

class ExecutorServer(Script):
    def install(self, env):
        import params

        azkaban_exec_url = AZKABAN_EXECUTOR_URL
        azkaban_name = AZKABAN_NAME
        azkaban_exec_home = params.azkaban_exec_home
        azkaban_log_dir = params.azkaban_log_dir
        azkaban_user = params.azkaban_user
        azkaban_group = params.user_group

        # create log dir
        Directory([azkaban_log_dir, azkaban_exec_home],
            owner=azkaban_user,
            group=azkaban_group,
            create_parents=True,
            cd_access="a",
            mode=0775
        )
        
        Execute(format("wget --no-check-certificate {azkaban_exec_url}  -O /tmp/{azkaban_name}"))
        Execute(format("tar -xf /tmp/{azkaban_name} -C {azkaban_exec_home} --strip-components 1"), user=azkaban_user)
        Execute(format("chown -R {azkaban_user} {azkaban_exec_home}"))

        Execute(format("rm -f /tmp/{azkaban_name}"))

        self.configure(env)

    def stop(self, env):
        import params

        azkaban_exec_home = params.azkaban_exec_home
        azkaban_user = params.azkaban_user

        Execute(format("cd {azkaban_exec_home}; bin/azkaban-executor-shutdown.sh"), user=azkaban_user)

    def start(self, env):
        import params

        azkaban_exec_home = params.azkaban_exec_home
        azkaban_user = params.azkaban_user
        executor_port = int(params.azkaban_executor_properties["executor.port"])

        self.configure(env)

        Execute(format("cd {azkaban_exec_home}; bin/azkaban-executor-start.sh"), user=azkaban_user)

        for index in range(1, 5) :
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("127.0.0.1",executor_port))
            sock.close()
            
            if result == 0:
                self.active(env)
                break
            else:
                time.sleep(5)

    def update(self, env):
        import params

        azkaban_user = params.azkaban_user
        azkaban_group = params.user_group
        azkaban_name = AZKABAN_NAME

        azkaban_exec_url = AZKABAN_EXECUTOR_URL
        azkaban_exec_home = params.azkaban_exec_home
        azkaban_exec_tmp_dir = '/tmp/azkaban-exec-' + str(time.time())

        Directory([azkaban_exec_tmp_dir],
                  owner=azkaban_user,
                  group=azkaban_group,
                  create_parents=True,
                  cd_access="a",
                  mode=0775
                  )

        Execute(format("wget --no-check-certificate {azkaban_exec_url}  -O /tmp/{azkaban_name}"), user=azkaban_user)
        Execute(format("tar -xf /tmp/{azkaban_name} -C {azkaban_exec_tmp_dir} --strip-components 1"), user=azkaban_user)
        Execute(format("rm -f {azkaban_exec_home}/lib/* "), user=azkaban_user)
        Execute(format("cp {azkaban_exec_tmp_dir}/lib/* {azkaban_exec_home}/lib/ "), user=azkaban_user)
        Execute(format("rm -f /tmp/{azkaban_name}"), user=azkaban_user)
        Execute(format("rm -rf {azkaban_exec_tmp_dir}"), user=azkaban_user)


    def active(self, env):
        import params

        executor_port = int(params.azkaban_executor_properties["executor.port"])

        active_url = format("http://localhost:{executor_port}/executor?action=activate")
        request = urllib2.Request(active_url)
        result = openurl(request, timeout=20)
        response_code = result.getcode()

        response_message = result.read()
        print(response_message)
        response = json.loads(response_message)

        if response_code != 200 :
            raise Fail("Error when active executor")

        status = response['status']

        if status != 'success':
            raise Fail("Falied when active executor")

    def deactive(self, env):
        import params

        executor_port = int(params.azkaban_executor_properties["executor.port"])

        active_url = format("http://localhost:{executor_port}/executor?action=deactivate")
        request = urllib2.Request(active_url)
        result = openurl(request, timeout=20)
        response_code = result.getcode()
        response_message = result.read()
        print(response_message)
        response = json.loads(response_message)

        if response_code != 200:
            raise Fail("Error when active executor")

        status = response['status']

        if status != 'success':
            raise Fail("Falied when active executor")

    def status(self, env):
        import params

        azkaban_exec_home = params.azkaban_exec_home
        check_process_status(format("{azkaban_exec_home}/currentpid"))


    def configure(self, env):
        import params

        azkaban_exec_home = params.azkaban_exec_home
        azkaban_conf_dir = format("{azkaban_exec_home}/conf")
        azkaban_log_dir = params.azkaban_log_dir

        key_val_template = "{0}={1}\n"

        with open(path.join(azkaban_conf_dir, "azkaban.properties"), "w") as f:
            for key, value in params.azkaban_db.iteritems():
                f.write(key_val_template.format(key, value))

            for key, value in params.azkaban_executor_properties.iteritems():
                if key != "content":
                    f.write(key_val_template.format(key, value))
            if params.azkaban_executor_properties.has_key("content"):
                f.write(str(params.azkaban_executor_properties["content"]))

        with open(path.join(azkaban_conf_dir, "log4j.properties"), "w") as f:
            
            f.write(format("azkaban.log.home={azkaban_log_dir}"))

            if params.log4j_properties.has_key("content"):
                f.write(str(params.log4j_properties["content"]))


if __name__ == "__main__":
    ExecutorServer().execute()