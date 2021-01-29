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
import os


from resource_management.core.resources.system import Execute, Directory, Link, File
from resource_management.libraries.functions.check_process_status import check_process_status
from resource_management.libraries.functions.format import format

from common import FLINK_REPO, FLINK_NAME

def package_install():
    """
    Flink package install
    :return:
    """
    import params

    flink_repo = FLINK_REPO

    flink_name = FLINK_NAME
    flink_home = params.flink_home
    flink_conf_dir = params.flink_conf_dir
    flink_log_dir = params.flink_env['log.dir']
    flink_pid_dir = params.flink_env['pid.dir']

    if os.path.isdir(flink_home):
        return

    # create home / log dir
    Directory([flink_home, flink_log_dir, flink_pid_dir],
              owner=params.flink_user,
              group=params.user_group,
              create_parents=True,
              ignore_failures=True,
              cd_access='a',
              mode=0775,
              )

    # copy tar file from repo
    Execute(format("wget --no-check-certificate {flink_repo}  -O /tmp/{flink_name}"))
    Execute(format("tar -xf /tmp/{flink_name} -C {flink_home} --strip-components 1"), user=params.flink_user)
    Execute(format("rm -f /tmp/{flink_name}"))


    # setting config
    Execute("sed -i \'s/##flink_home##/{0}/\' {1}/bin/config.sh".format(flink_home.replace("/", "\/"), flink_home))
    Execute("sed -i \'s/##flink_conf_dir##/{0}/\' {1}/bin/config.sh".format(flink_conf_dir.replace("/", "\/"), flink_home))

    #link
    setup_symlink()


def start_historical_server():
    import params
    flink_home = params.flink_home
    Execute(format("cd {flink_home} && bin/historyserver.sh start"), user=params.flink_user)


def stop_historical_server():
    import params
    flink_home = params.flink_home
    Execute(format("cd {flink_home} && bin/historyserver.sh stop"), user=params.flink_user)

def status_historical_server():
    import params
    flink_pid_dir = params.flink_env["pid.dir"]
    flink_user = params.flink_user
    flink_historical_server_name = "historyserver"

    file = format("{flink_pid_dir}/flink-{flink_user}-{flink_historical_server_name}.pid")

    check_process_status(file)

def setup_symlink():

    import params

    flink_ln_action = "/usr/bin/flink"
    flink_ln_conf = "/etc/flink/conf"

    Directory(["/etc/flink"],
              owner=params.flink_user,
              group=params.user_group,
              create_parents=True,
              ignore_failures=True,
              cd_access='a',
              mode=0775
            )

    if os.path.islink(flink_ln_action) :
        Link(flink_ln_action, action="delete")

    Link(flink_ln_action, to=os.path.join(params.flink_home, "bin/flink"))

    if os.path.islink(flink_ln_conf):
        Link(flink_ln_conf, action="delete")
    Link(flink_ln_conf, to=os.path.join(params.flink_home, "conf"))


def configuration():
    import params

    flink_conf_dir = os.path.join(params.flink_home, "conf")
    flink_conf_flie = os.path.join(flink_conf_dir, params.flink_config_file)

    flink_history_server_host = params.flink_history_server_host

    File(flink_conf_flie,
         owner=params.flink_user,
         group=params.user_group,
         mode=0644
         )

    key_val_template = "{0}: {1}\n"

    with open(flink_conf_flie, "w") as f:

        for key, value in params.flink_conf.iteritems():
            if value == "{{flink_history_server_host}}" :
                value = flink_history_server_host
            f.write(key_val_template.format(key, value))

        for key, value in params.flink_env.iteritems():
            f.write(key_val_template.format("env." + key, format(value)))

        f.write(key_val_template.format("env.yarn.conf.dir", params.hadoop_conf_dir))
        f.write(key_val_template.format("env.hadoop.conf.dir", params.hadoop_conf_dir))