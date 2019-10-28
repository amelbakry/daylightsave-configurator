import time
import sys
import os
import glob
import json
import fileinput
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from daylightsave_configurator.helper import CustomFormatter, applogger
from daylightsave_configurator.helper import adjust_schedule, validate


logger = applogger("SENZA")

def adjust_senza_yaml_files_definitions(senza_files):
    operation = os.environ["OPERATION"]
    if validate(operation):
        return
    if not os.path.exists(senza_files):
        logger.error("The provided directory is not exist.")
        return
    msgs = set()
    for root, dirs, files in os.walk(senza_files):
        for file in files:
            if file.endswith(".yaml"):
                 fname= os.path.join(root, file)
                 file_name = file
                 with open(fname) as f:
                    if "TimeSaving" in f.read():
                            msgs.add("File %s will not be modified as preotection flag TimeSaving exist" % file_name)
                            f.close()
                    else:
                        with open(fname) as f:
                            datafile = f.readlines()
                        for line in datafile:
                            if "cronExpression" in line:
                                expression = line.split(":")[1].lstrip()
                                _expression = expression.strip("\n")
                                exp = str(expression.replace('"', ''))
                                updated_schedule = adjust_schedule(exp, operation)
                                with fileinput.FileInput(fname, inplace=True) as file:
                                    for line in file:
                                        print(line.replace(expression, updated_schedule), end='')
                                        msgs.add("Updated Cron Expression of %s from %s to %s" % (file_name, _expression, updated_schedule.strip("\n")))
                                with fileinput.FileInput(fname, inplace=True) as file:
                                    for line in file:
                                        if "TimeSaving" in line:
                                            print(line.replace(line, line), end='')
                                        else:
                                            print(line.replace("taskType: scale", "taskType: scale  # TimeSaving"), end='')
    if not msgs:
          logger.warn("There is no YAML File matching the provided criteria or may be directory is empty")
    else:
         for msg in msgs:
            if str("preotection flag TimeSaving exist") in msg:
                logger.warn(msg)
            elif str("Updated Cron Expression") in msg:
                logger.info(msg)

def remove_protection_flag(senza_files):
    if not os.path.exists(senza_files):
        logger.error("The provided directory is not exist.")
        return None
    msgs = set()
    for root, dirs, files in os.walk(senza_files):
        for file in files:
            file_name = file
            if file.endswith(".yaml"):
                 fname= os.path.join(root, file)
                 with open(fname) as f:
                    datafile = f.readlines()

                    for line in datafile:
                        if "TimeSaving" in line:
                            with fileinput.FileInput(fname, inplace=True) as file:
                            # with fileinput.FileInput(fname, inplace=True, backup='.bak') as file:
                                for line in file:
                                    print(line.replace("# TimeSaving", " "), end='')
                                    msgs.add("Removed Protection Flag for File %s " % file_name)
    if not msgs:
          logger.warn("No Protection Flag exists or may be directory is empty")
    else:
         for msg in msgs:
              logger.info(msg)
