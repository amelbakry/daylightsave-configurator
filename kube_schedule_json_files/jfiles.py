import json
import fileinput
import os
import sys
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from daylightsave_configurator.helper import CustomFormatter, applogger
from daylightsave_configurator.helper import adjust_schedule, validate


def adjust_kube_schedule_json_files(json_files):
    logger = applogger("JSON_FILES")
    operation = os.environ["OPERATION"]
    if validate(operation):
        return
    if not os.path.exists(json_files):
        logger.error("The provided directory is not exist.")
        return
    msgs = set()
    for root, dirs, files in os.walk(json_files):
        for file in files:
            if file.endswith(".json"):
                 fname= os.path.join(root, file)
                 with open(fname) as f:
                    datafile = f.readlines()
                 for line in datafile:
                    if "schedule" in line:
                        schedule = line.split(":")[1].lstrip()
                        exp = str(schedule.replace('"', ''))
                        exp = re.sub(',$', '', exp)
                        updated_schedule = adjust_schedule(exp, operation).rstrip('\n')
                        updated_schedule = '"%s",' % updated_schedule
                        updated_schedule = updated_schedule + '\n'
                        with fileinput.FileInput(fname, inplace=True) as file:
                            for line in file:
                                print(line.replace(schedule, updated_schedule), end='')
                                msgs.add("Updated Cron Expressions of %s successfully" % fname)
    if not msgs:
          logger.warn("There is no JSON File matching the provided criteria or may be directory is empty")
    else:
         for msg in msgs:
              logger.info(msg)




