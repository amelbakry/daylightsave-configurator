import os
import subprocess
import shutil, sys
import ruamel.yaml
import json
import re
import logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from daylightsave_configurator.helper import CustomFormatter, applogger
from daylightsave_configurator.helper import adjust_schedule, validate


logger = applogger("ZMON")

def adjust_hour(hour):
    operation = os.environ["OPERATION"]

    if operation == "increment":
        if int(hour) == 23 or int(hour) == 24:
            hour = 0
        else:
            hour = int(hour) + 1
    elif  operation == "decrement":
         if int(hour) == 0 or int(hour) == 24:
            hour = 23
         else:
            hour = int(hour) - 1
    return hour


def export_zmon_alerts(zmon_directory):
    """ This function will use bash script ./export.sh to collect zmon alerts per team """
    if os.path.isdir(zmon_directory):
        shutil.rmtree(zmon_directory)
        logger.info("Exporting ZMON Alerts")
    subprocess.call("./zmon/export.sh", shell=True)


def adjust_zmon_time_period(period):
    ''' function to update zmon time period. supported format at the moment
       TimePeriod
              = "wd {2-6} hr {7-22}, wd {2-6} hr {6-7} min {10-59}, wd {1 7} hr {8-22}, wd {1 7} hr {7-8} min {10-59}"
              = "wd {Mon-Fri} hr {9-18} min {0 10 20 30 40 50}"
              = " wd{Mon-Fri}hr{0-23}, wd{Sat}hr{0-20}, wd{Son}hr{20-23}"
              = "wd {Mon} hr {12-24}, wd{Tue-Sun}"
              = "wd {Mon-Thu} hr {0-23} , wd {Fri} hr {0-22}, wd {Sat} hr {10-22}, wd {Sun}"
              = "wd {Mon-Fri} hr {9-17}"
              = "wd {Mon-Wed}"
    '''
    period = period.split(",")


    adjusted = []
    for s in period:
        if re.match(r'(^\s?\w{2,3}\s?{\w+[-\s]?\w+?}\shr\s){(\d+)-(\d+)}(\smin\s{(\d+[-\s]?\d?)+}\s?)$', s):
            match = re.match(r'(^\s?\w{2,3}\s?{\w+[-\s]?\w+?}\shr\s){(\d+)-(\d+)}(\smin\s{(\d+[-\s]?\d?)+}\s?)$', s)
            updated = match.group(1) + "{" + str(adjust_hour(match.group(2))) + \
                         "-" + str(adjust_hour(match.group(3))) + "}" + match.group(4)
            adjusted.append(updated)
        elif re.match(r'(^\s?\w{2,3}\s?{\w+[-\s]?\w+?}\s?hr\s?){(\d+)-(\d+)\s?}\s?$', s):
            match = re.match(r'(^\s?\w{2,3}\s?{\w+[-\s]?\w+?}\s?hr\s?){(\d+)-(\d+)}\s?$', s)
            updated = match.group(1) + "{" + str(adjust_hour(match.group(2))) + \
                         "-" + str(adjust_hour(match.group(3))) + "}"
            adjusted.append(updated)
        elif re.match(r'^\s?\w{2,3}\s?{\w+[-\s]?\w+?}$', s):
            match = re.match(r'^\s?\w{2,3}\s?{\w+[-\s]?\w+?}$', s)
            adjusted.append(match.group(0))
        else:
            adjusted.append("None")

    if "None" in adjusted:
        logger.error("Some Schedules not parsed correctly")
        return None
    else:
        adjusted = ",".join(adjusted)
        return adjusted


def adjust_zmon_alerts(zmon_directory):
    operation = os.environ["OPERATION"]
    if validate(operation):
        return
    export_zmon_alerts(zmon_directory)
    yaml = ruamel.yaml.YAML(typ='safe')
    msgs = set()
    for root, dirs, files in os.walk(zmon_directory):
        for file in files:
            fname= os.path.join(root, file)
            with open(fname) as f:
                if "period: wd" in f.read():
                    print(file)
                else:
                    os.remove(fname)
            try:
                with open(fname, 'r') as f:
                    data = yaml.load(f)
                    data["period"] = adjust_zmon_time_period(data.get("period"))
                    with open(fname, "w") as f:
                        f.write(json.dumps(data))
                subprocess.run(["zmon", "alert-definition", "update", fname])
                msgs.add("Updated Schedule of Alert %s successfully" % file)

            except FileNotFoundError:
                pass

    for msg in msgs:
        logger.info(msg)




