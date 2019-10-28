import boto3
import json
import re
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from daylightsave_configurator.helper import CustomFormatter, applogger
from daylightsave_configurator.helper import adjust_schedule, print_table, validate



client = boto3.client('autoscaling')
logger = applogger("AWS")

def adjust_aws_schedule_tasks(check=None):
    operation = os.environ["OPERATION"]
    if validate(operation):
        return
    groups = client.describe_auto_scaling_groups().get("AutoScalingGroups")
    autoscaling_groups = []
    for group in groups:
        asg = group.get("AutoScalingGroupName")
        if check is not None:
            if check not in str(asg):
                continue
            else:
                autoscaling_groups.append(asg)
        else:
            autoscaling_groups.append(asg)

    schedules = {}
    for group in autoscaling_groups:
        scheduled_actions = client.describe_scheduled_actions(AutoScalingGroupName=group).get("ScheduledUpdateGroupActions")
        if not scheduled_actions:
            pass
        else:
            schedules[group] = scheduled_actions

    for schedule, actions in schedules.items():
        for n in range(len(actions)):
            action = actions[n]
            AutoScalingGroupName = action.get("AutoScalingGroupName")
            ScheduledActionName = action.get("ScheduledActionName")
            StartTime = action.get("StartTime")
            Recurrence = action.get("Recurrence")
            MinSize = action.get("MinSize")
            MaxSize = action.get("MaxSize")
            update = adjust_schedule(Recurrence, operation)
            try:
                response = client.put_scheduled_update_group_action(
                        AutoScalingGroupName= AutoScalingGroupName,
                        ScheduledActionName= ScheduledActionName,
                        Recurrence= update,
                        MinSize= MinSize,
                        MaxSize= MaxSize
                    )
                logger.info("Adusted schedule of AutoscalingGroup %s from %s to %s successfully." % (AutoScalingGroupName, Recurrence, update))
            except exception as e:
                logger.error(e)


@print_table
def describe_aws_schedule_tasks(check=None):
    title = "Scheduled Tasks:"
    table_data = [["group_name", "cron_expression", "scale_min_capacity",
                   "scale_max_capacity"]]
    response = client.describe_auto_scaling_groups()
    all_asg = response['AutoScalingGroups']
    for asg in all_asg:
        asg = asg["AutoScalingGroupName"]
        if check is not None:
            if check not in str(asg):
                asg = None
            else:
                asg = asg
        else:
            asg = asg
        if asg is not None:

            response = client.describe_scheduled_actions(
                AutoScalingGroupName=asg)
            schedules = response["ScheduledUpdateGroupActions"]
            for schedule in schedules:
                data = [schedule["AutoScalingGroupName"], schedule["Recurrence"], schedule["MaxSize"], schedule["MinSize"]]
                table_data.append(data)
    return table_data, title


