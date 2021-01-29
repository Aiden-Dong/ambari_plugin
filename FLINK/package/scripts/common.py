import os

import ConfigParser

script_dir = os.path.dirname(os.path.realpath(__file__))
config = ConfigParser.ConfigParser()
config.readfp(open(os.path.join(script_dir, 'download.ini')))

FLINK_NAME = "flink"
FLINK_REPO = config.get('download', 'flink_repo')