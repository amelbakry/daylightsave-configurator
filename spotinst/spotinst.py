import json
import csv
import os
import sys
import time
from spotinst_sdk import SpotinstClient
from spotinst_sdk.aws_elastigroup import *
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from daylightsave_configurator.helper import CustomFormatter, applogger
from daylightsave_configurator.helper import adjust_schedule, print_table, validate
from daylightsave_configurator import daylightsave_adjust_schedules

def client():
    client = SpotinstClient()

    def get_token_from_file():
        credentials_file = os.path.isfile('~/.spotinst/credentials')
        if credentials_file:
            client = SpotinstClient(credentials_file='~/.spotinst/credentials', profile='default')

    def get_token_from_env():
        if 'spotinst_token' in os.environ:
            spotinst_token = os.environ.get("spotinst_token")
            if "account_id" in os.environ:
                account_id = os.environ.get("account_id")
                client = SpotinstClient(auth_token=spotinst_token, account_id=account_id)

    return client

client = client()
groups = client.get_elastigroups()
logger = applogger("SpotInst")


def get_group(g):
    for group in groups:
        if g in group.get("name"):
            return group.get("name")


def get_group_id(g):
    for group in groups:
        if g == group.get("name"):
            return group.get("id")


def get_group_metadata(group):
    id = get_group_id(group)
    if id is None:
        logger.error("There is no ElasticGroup called %s" % group)
        sys.exit()
    else:
        eg = client.get_elastigroup(id)
        return eg

def reverse_operation(operation):
    if operation == "increment":
        return "decrement"
    elif operation == "decrement":
        return "increment"

def adjust_cron_expression_for_schedule_tasks(check=None):
    operation = os.environ["OPERATION"]
    if validate(operation):
        return
    for group in groups:
        groupName = group.get("name")
        if check is not None:
            if check not in str(groupName):
                schedule = None
            else:
                schedule = group.get("scheduling")
        else:
            schedule = group.get("scheduling")
        if schedule is not None:
            scaling_tasks = schedule.get("tasks")
            if scaling_tasks is not None:
                for n in range(len(scaling_tasks)):
                    schedule = scaling_tasks[n]
                    adjusted_cron_expression = adjust_schedule(schedule.get("cron_expression"), operation=operation)
                    scale_min_capacity = schedule.get("scale_min_capacity")
                    scale_max_capacity = schedule.get("scale_max_capacity")
                    scale_target_capacity = schedule.get("scale_target_capacity")
                    configure_scheduled_tasks(groupName,
                                              adjusted_cron_expression,
                                              scale_min_capacity,
                                              scale_max_capacity,
                                              scale_target_capacity)


def configure_scheduled_tasks(group, cron_expression, scale_min_capacity, scale_max_capacity, scale_target_capacity=None):
    operation = os.environ["OPERATION"]
    tasks = []
    all_tasks = []
    eg = get_group_metadata(group)
    id = get_group_id(group)
    schedule = eg.get("scheduling")
    if schedule:
        scaling_tasks = schedule.get("tasks")
        for n in range(len(scaling_tasks)):
            schedule = scaling_tasks[n]
            schedule["task_type"] = "scale"
            tasks.append(schedule)
    for i in range(len(tasks)):
        try:
            for key, val in tasks[i].items():
                if val == adjust_schedule(cron_expression, operation=reverse_operation(operation)):
                    del tasks[i]
        except IndexError:
            # expected IndexErrors when deleting a task to be updated
            continue
    updated_task = {"task_type": "scale",
                    "is_enabled": True,
                    "cron_expression": cron_expression,
                    "scale_min_capacity": scale_min_capacity,
                    "scale_max_capacity": scale_max_capacity
                    }
    if scale_target_capacity is not None:
        updated_task["scale_target_capacity"] = scale_target_capacity
    tasks.append(updated_task)
    for t in range(len(tasks)):
        task = tasks[t]
        for key, val in task.items():
            if task.get("scale_target_capacity") is not None:
                t = ScheduledTask(task_type='scale',
                                  cron_expression=task["cron_expression"],
                                  scale_target_capacity=task["scale_target_capacity"],
                                  scale_min_capacity=task["scale_min_capacity"],
                                  scale_max_capacity=task["scale_max_capacity"],
                                  is_enabled=True)
            else:
                t = ScheduledTask(task_type='scale',
                                  cron_expression=task["cron_expression"],
                                  scale_min_capacity=task["scale_min_capacity"],
                                  scale_max_capacity=task["scale_max_capacity"],
                                  is_enabled=True)
        all_tasks.append(t)
    try:
        scheduling = Scheduling(tasks=all_tasks)
        group_update = Elastigroup(scheduling=scheduling)
        update_result = client.update_elastigroup(group_update=group_update, group_id=id)
        logger.info("Scheduled Tasks of Elasticgroup %s have been configured successfully." % group)
    except:
        raise


@print_table
def get_all_scheduled_tasks(check=None):
    title = "Scheduled Tasks:"
    table_data = [["group_name", "cron_expression", "scale_min_capacity",
                   "scale_max_capacity", "scale_target_capacity"]]
    for group in groups:
        groupName = group.get("name")
        if check is not None:
            if check not in str(groupName):
                schedule = None
            else:
                schedule = group.get("scheduling")
        else:
            schedule = group.get("scheduling")
        if schedule is not None:
            scaling_tasks = schedule.get("tasks")
            if scaling_tasks is not None:
                for n in range(len(scaling_tasks)):
                    schedule = scaling_tasks[n]
                    data = [schedule[k] for k in table_data[0] if k in schedule]
                    data.insert(0, groupName)
                    table_data.append(data)
    return table_data, title
