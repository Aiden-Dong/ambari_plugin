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
import urllib2
import base64
import json
import time

from common import AZKABAN_WEB_URL, AZKABAN_NAME
from ambari_commons.inet_utils import openurl
from resource_management.core.exceptions import Fail
from resource_management.core.exceptions import ExecutionFailed, ComponentIsNotRunning
from resource_management.core.resources.system import Execute, Directory
from resource_management.libraries.script.script import Script
from resource_management.libraries.functions.check_process_status import check_process_status
from resource_management.libraries.functions.format import format


class WebServer(Script):
    def install(self, env):
        import params

        azkaban_web_url = AZKABAN_WEB_URL
        azkaban_web_home = params.azkaban_web_home
        azkaban_user = params.azkaban_user
        azkaban_group = params.user_group
        azkaban_name = AZKABAN_NAME
        
        # create log dir
        Directory([params.azkaban_log_dir, params.azkaban_web_home],
            owner=azkaban_user,
            group=azkaban_group,
            create_parents=True,
            cd_access="a",
            mode=0775
        )

        Execute(format("wget --no-check-certificate {azkaban_web_url}  -O /tmp/{azkaban_name}"))
        Execute(format("tar -xf /tmp/{azkaban_name} -C {azkaban_web_home} --strip-components 1"), user=azkaban_user)
        Execute(format("chown -R {azkaban_user} {azkaban_web_home}"))

        Execute(format("rm -f /tmp/{azkaban_name}"))

        self.configure(env)

    def stop(self, env):
        import params
        azkaban_web_home = params.azkaban_web_home
        azkaban_user = params.azkaban_user

        Execute(format("cd {azkaban_web_home}; bin/azkaban-web-shutdown.sh"), user=azkaban_user)

    def start(self, env):
        import params

        azkaban_web_home = params.azkaban_web_home
        azkaban_user = params.azkaban_user

        self.configure(env)

        Execute(format("cd {azkaban_web_home}; bin/azkaban-web-start.sh"), user=azkaban_user)

    def update(self, env):
        import params

        azkaban_user = params.azkaban_user
        azkaban_group = params.user_group
        azkaban_name = AZKABAN_NAME

        azkaban_web_url = AZKABAN_WEB_URL
        azkaban_web_home = params.azkaban_web_home
        azkaban_web_tmp_dir = '/tmp/azkaban-web-' + str(time.time())

        Directory([azkaban_web_tmp_dir],
                  owner=azkaban_user,
                  group=azkaban_group,
                  create_parents=True,
                  cd_access="a",
                  mode=0775
                  )

        Execute(format("wget --no-check-certificate {azkaban_web_url}  -O /tmp/{azkaban_name}"), user=azkaban_user)
        Execute(format("tar -xf /tmp/{azkaban_name} -C {azkaban_web_tmp_dir} --strip-components 1"), user=azkaban_user)
        Execute(format("rm -f {azkaban_web_home}/lib/* "), user=azkaban_user)
        Execute(format("cp {azkaban_web_tmp_dir}/lib/* {azkaban_web_home}/lib/ "), user=azkaban_user)
        Execute(format("rm -f /tmp/{azkaban_name}"), user=azkaban_user)
        Execute(format("rm -rf {azkaban_web_tmp_dir}"), user=azkaban_user)


    def refresh(self, env):
        import params
        azkaban_admin_username = params.azkaban_admin_username
        azkaban_admin_password = params.azkaban_admin_password
        azkaban_web_port = int(params.azkaban_web_properties['jetty.port'])

        active_url = format("http://localhost:{azkaban_web_port}/executor?ajax=reloadExecutors")
        request = urllib2.Request(active_url)
        base64string = base64.encodestring(format('{azkaban_admin_username}:{azkaban_admin_password}')).replace('\n', '')
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json")
        request.add_header("Authorization", "Basic {0}".format(base64string))

        result = openurl(request, timeout=20)
        response_code = result.getcode()
        response_message = result.read()

        print(response_message)

        response = json.loads(response_message)

        if response_code != 200:
            raise Fail("Error when refresh server")

        status = response['status']

        if status != 'success':
            raise Fail("Falied when refresh server")

    def status(self, env):
        import params

        azkaban_web_home = params.azkaban_web_home
        check_process_status(format("{azkaban_web_home}/currentpid"))

    def configure(self, env):
        import params

        key_val_template = "{0}={1}\n"
        azkaban_web_home = params.azkaban_web_home
        azkaban_conf_dir = format("{azkaban_web_home}/conf")
        azkaban_log_dir = params.azkaban_log_dir
        azkaban_admin_username = params.azkaban_admin_username
        azkaban_admin_password = params.azkaban_admin_password

        with open(path.join(azkaban_conf_dir, "azkaban.properties"), "w") as f:
            for key, value in params.azkaban_db.iteritems():
                f.write(key_val_template.format(key, value))
            for key, value in params.azkaban_web_properties.iteritems():
                if key != "content":
                    f.write(key_val_template.format(key, value))
            if params.azkaban_web_properties.has_key("content"):
                    f.write(str(params.azkaban_web_properties["content"]))

        with open(path.join(azkaban_conf_dir, "azkaban-users.xml"), "w") as f:
            f.writelines("<azkaban-users>\n")
            f.writelines("<role name=\"azkaban_r_admin\" permissions=\"ADMIN\"/>\n")
            f.writelines("<group name=\"azkaban_g_admin\" roles=\"azkaban_r_admin\"/>\n")
            f.writelines(format("<user username=\"{azkaban_admin_username}\" password=\"{azkaban_admin_password}\" groups=\"azkaban_g_admin\"/>\n"))

            if params.azkaban_users.has_key("content"):
                f.writelines(str(params.azkaban_users["content"]))

            f.writelines("\n</azkaban-users>")

        with open(path.join(azkaban_conf_dir, "global.properties"), "w") as f:
            if params.global_properties.has_key("content"):
                f.write(str(params.global_properties["content"]))

        with open(path.join(azkaban_conf_dir, "log4j.properties"), "w") as f:
            f.write(format("azkaban.log.home={azkaban_log_dir}"))

            if params.log4j_properties.has_key("content"):
                f.write(str(params.log4j_properties["content"]))

if __name__ == "__main__":
    WebServer().execute()
