import boto3
import time
from datetime import datetime
from datetime import timedelta
from crontab import CronTab
from crontab import CronSlices
from terminaltables import AsciiTable
import croniter
import glob
import json
import re
import os
import sys
import fileinput
import pykube
import logging



class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    grey = "\x1b[38;21m"
    green = '\033[92m'
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s "

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def applogger(app):
    logger = logging.getLogger(app)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(CustomFormatter())
    if (logger.hasHandlers()):
        logger.handlers.clear()
    logger.addHandler(ch)
    return logger

def adjust_schedule(schedule, operation):
    logger = applogger("Scheduler")
    fields = schedule.split(" ")
    M = fields[0]
    H = fields[1]
    DoM = fields[2]
    Mn = fields[3]
    DoW = fields[4]

    if operation == "increment":

        if H == "*":
            H = "*"
        elif int(H) == 23:
            H = 0
        else:
            H = int(H) + 1
    elif  operation == "decrement":

         if H == "*":
            H = "*"
         elif int(H) == 0:
            H = 23
         else:
            H = int(H) - 1
    elif operation == "None":
        logger.error("The provided operation is None")
        return
    fields[1] = str(H)
    parts = " ".join(fields)
    if CronSlices.is_valid(parts):
        return parts
    else:
        logger.error("invalid cron expression")
        return

def print_table(func):
    def _print(*args, **kwargs):

        table_data = func(*args, **kwargs)[0]
        func(*args, **kwargs)
        title = func(*args, **kwargs)[1]
        print('\033[1m' + ' %s' % title + '\033[0m')
        table = AsciiTable(table_data)
        print(table.table)
    return _print


def validate(operation):
    if operation == "None":
        logger.error("The provided operation is None")
        return True
    else:
        return False
