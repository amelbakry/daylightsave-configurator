import pykube
import os
import json
import croniter
import ast
import sys
from kube.resources.Stack import Stack
from kube.resources.Stackset import StackSet
from crontab import CronTab
from crontab import CronSlices
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from daylightsave_configurator.helper import adjust_schedule, CustomFormatter, applogger
from daylightsave_configurator import daylightsave_adjust_schedules



logger = applogger("Kube")

def get_kube_api():
    """ Initiating the API from Service Account or when running locally from ~/.kube/config """
    try:
        config = pykube.KubeConfig.from_service_account()
    except FileNotFoundError:
        # local testing
        config = pykube.KubeConfig.from_file(os.path.expanduser('~/.kube/config'))
    api = pykube.HTTPClient(config)
    return api


def update_kube_annotations(namespace=pykube.all):
    api = get_kube_api()
    operation = os.environ["OPERATION"]
    new_annotations = {}

    for resource in "Deployment", "StackSet":
        if resource == "Deployment":
            pykube_en = pykube.Deployment.objects(api, namespace=namespace)
        elif resource == "StackSet":
            pykube_en = StackSet.objects(api, namespace=namespace)

        for resource_name in pykube_en:
            if 'zalando.org/schedule-actions' in resource_name.annotations:
                try:
                    schedules = resource_name.annotations.get("zalando.org/schedule-actions")
                    if "\'" in schedules:
                        schedules = schedules.replace("\'", "\"")
                    if "s3" in schedules:
                        continue

                    # print(schedules)
                    updated_schedules = []
                    for sch in json.loads(schedules):
                        old_schedule = sch.get("schedule")
                        new_schedule = adjust_schedule(old_schedule, operation)
                        sch["schedule"] = new_schedule
                        logger.debug("Updating Schedule of %s %s from %s to %s" %  (resource, resource_name.name, old_schedule, new_schedule))
                        updated_schedules.append(sch)
                    try:
                        resource_name.annotations["zalando.org/schedule-actions"] = '%s' % json.dumps(updated_schedules)
                        resource_name.update()
                        logger.info("Schedule of %s %s has been updated successfully. " % (resource, resource_name.name))
                    except Exception as e:
                        logger.error(e)
                    # print(resource_name.annotations["zalando.org/schedule-actions"] )
                except Exception as e:
                    logger.warn(e)

