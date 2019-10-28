#!/usr/bin/env python3

from __future__ import print_function, unicode_literals
from PyInquirer import style_from_dict, Token, prompt, Separator
from pprint import pprint
from zmon import zmon
from senza_files import senza
from kube import kube
from spotinst import spotinst
from kube_schedule_json_files import jfiles
from aws_schedules import aws
import time
import croniter
import subprocess
import glob
import os
import sys
import fileinput


# sudo pip3 install 'prompt_toolkit==1.0.14'

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


style = style_from_dict({
    Token.Separator: '#cc5454',
    Token.QuestionMark: '#673ab7 bold',
    Token.Selected: '#cc5454',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Instruction: '',  # default
    Token.Answer: '#f44336 bold',
    Token.Question: '',
})

def confirm():
    answer = input(bcolors.BOLD + "OK to continue [Y/N]? ").lower()
    if answer == "y":
        return answer == "y"
    elif answer == "n":
        sys.exit()
    else:
        print("Unknown Option")
        sys.exit()


def __operation__():
    operation = [
    {
        'type': 'list',
        'message': 'DayTimeSave Status',
        'name': 'Keys',
        'choices': [
               'DayTimeSave ON         CEST = UTC+2:00',
               'DayTimeSave OFF        CEST = UTC+1:00',
               'None'
               ]
            },
       ]

    operation = prompt(operation, style=style)
    operation = operation.get("Keys")
    if operation == str("DayTimeSave ON         CEST = UTC+2:00"):
        operation = "increment"
    elif operation == str("DayTimeSave OFF        CEST = UTC+1:00"):
        operation = "decrement"
    elif operation == str("None"):
        operation = "None"

    return operation



def main():

    print(bcolors.BOLD + "Welcome to DayLight Save Configuration Wizard")
    operation = __operation__()
    os.environ["OPERATION"] = operation
    cmd = "export OPERATION=%s" % operation
    os.system(cmd)
    actions = [
        {
            'type': 'checkbox',
            'message': 'Actions: ',
            'name': 'Keys',
            'choices': [
                Separator('= Please select actions to be applied ='),
                {
                    'name': 'Adjust AWS Schedules'
                },
                {
                    'name': 'Adjust SpotInst Schedules'
                },
                {
                    'name': 'Adjust Kubernetes Annotations Schedules'
                },
                {
                 'name': 'Adjust ZMON Alerts which have Time Period'
                },
                {
                 'name': 'Adjust Local Senza Yaml FIles'
                },
                {
                'name': 'Adjust Local Kubernetes JSON Files'
                },

                Separator('= Other Functions ='),
                {
                'name': 'Remove Protection Flag'
                },
                {
                'name': 'Check SpotInst Schedules'
                },
                {
                'name': 'Check AWS Schedules'
                },
                {
                'name': 'Exit'
                }
            ],
            'validate': lambda answer: 'You must choose at least one topping.'
            if len(answer) == 0 else True
        }
    ]

    actions = prompt(actions, style=style)
    print(bcolors.OKBLUE + "Your Selections: ")
    print(" ")
    action_item = []
    for k, v in actions.items():
        myArg = v
        action_item.append(myArg)
    for item in action_item[0]:
        print("\t" + "> " +  item)
    print(" ")
    confirm()
    for item in action_item[0]:
        if item == str("Adjust AWS Schedules"):
            aws_filter = input(bcolors.BOLD + 'Adjust ALL AWS Schedules or Add a Filter [ALL/Filter]: ')
            print(aws_filter)
            if aws_filter == "ALL":
                aws.adjust_aws_schedule_tasks()
            else:
                aws.adjust_aws_schedule_tasks(aws_filter)
        if item == str("Adjust SpotInst Schedules"):
            spotinst_filter = input(bcolors.BOLD +'Adjust ALL SpotInst Schedules or Add a Filter [ALL/Filter]: ')
            if spotinst_filter == "ALL":
                spotinst.adjust_cron_expression_for_schedule_tasks()
            else:
                spotinst.adjust_cron_expression_for_schedule_tasks(spotinst_filter)
        if item == str("Adjust Kubernetes Annotations Schedules"):
            kube_filter = input(bcolors.BOLD +'Adjust Annotations for ALL Namespaces or Add a Filter [ALL/Filter]: ')
            if kube_filter == "ALL":
                kube.update_kube_annotations()
            else:
                kube.update_kube_annotations(kube_filter)
        if item == str("Adjust ZMON Alerts which have Time Period"):
            print(" ")
            zmon_team = input(bcolors.BOLD +'Please Provide Team name: ')
            zmon_directory = "/tmp/%s" % zmon_team
            zmon.adjust_zmon_alerts(zmon_directory)
        if item == str("Adjust Local Senza Yaml FIles"):
            print(" ")
            senza_files = input(bcolors.BOLD +'Please Provide Senza Yaml files location: ')
            senza.adjust_senza_yaml_files_definitions(senza_files)
        if item == str("Adjust Local Kubernetes JSON Files"):
            print(" ")
            json_files = input(bcolors.BOLD +'Please Provide Kubernetes JSON files location: ')
            jfiles.adjust_kube_schedule_json_files(json_files)
        if item == str("Remove Protection Flag"):
            print(" ")
            senza_files = input(bcolors.BOLD +'Please Provide Senza Yaml files location to remove Protection Flag: ')
            senza.remove_protection_flag(senza_files)

        if item == str("Check SpotInst Schedules"):
            check_spot = input(bcolors.BOLD + 'Check ALl SpotInst Schedules or Add a Filter [ALL/Filter]: ')
            if check_spot == "ALL":
                spotinst.get_all_scheduled_tasks()
            else:
                spotinst.get_all_scheduled_tasks(check_spot)

        if item == str("Check AWS Schedules"):
            check_aws = input(bcolors.BOLD + 'Check ALl AWS Schedules or Add a Filter [ALL/Filter]: ')
            if check_aws == "ALL":
                aws.describe_aws_schedule_tasks()
            else:
                aws.describe_aws_schedule_tasks(check_aws)
        if item == str("Exit"):
            sys.exit()


if __name__ == "__main__":
    main()
