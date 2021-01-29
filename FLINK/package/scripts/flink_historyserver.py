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

import flink

class FlinkHistoryServer(Script):

    def install(self, env):
        flink.package_install()
        self.configure(env)

    def configure(self, env):
        flink.configuration()

    def stop(self, env):
        flink.stop_historical_server()

    def start(self, env):
        self.configure(env)
        flink.start_historical_server()

    def status(self, env):
        flink.status_historical_server()

if __name__ == "__main__":
    FlinkHistoryServer().execute()