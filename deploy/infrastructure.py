import argparse

import boto3

from ecs_volumes import attach_volume_to_ecs_ec2
from ecs import create_ecs_cluster, create_ecs_task, create_ecs_ec2
from iam_roles import create_iam_roles
from security_group import create_security_groups
from utilities import read_settings_file

# Be sure to export correct profile using something like this... export AWS_PROFILE=68
ASSUME_ROLE_POLICY_DOCUMENT = '{"Version": "2012-10-17","Statement": [{"Sid": "","Effect": "Allow","Principal": {"Service": "ec2.amazonaws.com"},"Action": "sts:AssumeRole"}]}'

parser = argparse.ArgumentParser()
parser.add_argument("settings_file")
args = parser.parse_args()

settings = read_settings_file(args.settings_file)

# Verify settings here.
vpc_id = settings["VPC_ID"]

ENVIRONMENT = "PROD"
stack_name = settings["STACK_NAME"]

MACHINE_TAGS = [{"Key": "owner", "Value": settings["MACHINE_OWNER"]},
                {"Key": "environment", "Value": ENVIRONMENT},
                {"Key": "project", "Value": settings["STACK_NAME"]},
                {"Key": "department", "Value": settings["GROUP_OWNER"]}]

PROTECTED_CIDR = settings["PROTECTED_CIDR"]

ec2 = boto3.resource('ec2')
vpc = ec2.Vpc(vpc_id)
ecs_client = boto3.client('ecs')
ec2_client = boto3.client('ec2')

INSTANCE_GROUP = ["4", "5"]

ecs_cluster_name = settings["STACK_NAME"] + "-" + ENVIRONMENT
ecs_task_family = ecs_cluster_name + "-" + "task_family"
S3_BUCKET_ARN = settings["S3_BUCKET_ARN"]
TASK_ROLE_ARN = settings["TASK_ROLE_ARN"]

userdata_string = "#!/bin/bash\necho ECS_CLUSTER=" + ecs_cluster_name + " >> /etc/ecs/ecs.config\ncd /tmp\ncurl https://amazon-ssm-us-east-1.s3.amazonaws.com/latest/linux_amd64/amazon-ssm-agent.rpm -o amazon-ssm-agent.rpm\nyum install -y amazon-ssm-agent.rpm"

if settings["CREATE_SECURITY_GROUP"] == "True":
    create_security_groups(stack_name, vpc, PROTECTED_CIDR)

if settings["CREATE_IAM_ROLES"] == "True":
    iam = boto3.resource('iam')
    iam_client = boto3.client('iam')

    create_iam_roles(stack_name, iam, iam_client, S3_BUCKET_ARN, ASSUME_ROLE_POLICY_DOCUMENT)

if settings["CREATE_CLUSTER"] == "True":
    create_ecs_cluster(ecs_client, ecs_cluster_name)

if settings["CREATE_ECS_EC2"] == "True":
    for instance_counter in INSTANCE_GROUP:

        print("Create EC2 - " + ecs_cluster_name + instance_counter)

        create_ecs_ec2(stack_name, ecs_cluster_name + instance_counter, vpc, ec2, userdata_string, settings, MACHINE_TAGS)

if settings["ATTACH_VOLUME_TO_ECS_EC2"] == "True":
    for instance_counter in INSTANCE_GROUP:
        filters = [{
            'Name': 'tag:Name',
            'Values': [ecs_cluster_name + instance_counter]
        }, {
            'Name': 'instance-state-name',
            'Values': ['running']}]

        ecs_ec2_instance = ec2_client.describe_instances(Filters=filters)

        print("Wait on EC2 - " + ecs_cluster_name + instance_counter)

        ec2_waiter = ec2_client.get_waiter('instance_status_ok')
        ec2_waiter.wait(InstanceIds=[ecs_ec2_instance['Reservations'][0]['Instances'][0]['InstanceId']])

        print("Attach Volume to EC2 - " + ecs_cluster_name + instance_counter)

        attach_volume_to_ecs_ec2(ec2_client, settings, ecs_ec2_instance)

if settings["MOUNT_VOLUME_TO_EC2"] == "True":

    for instance_counter in INSTANCE_GROUP:

        filters = [{
            'Name': 'tag:Name',
            'Values': [ecs_cluster_name + instance_counter]}, {
            'Name': 'instance-state-name',
            'Values': ['running']}
        ]

        ecs_ec2_instance1 = ec2_client.describe_instances(Filters=filters)

        print("Wait on EC2 - " + ecs_cluster_name + instance_counter)

        ec2_waiter = ec2_client.get_waiter('instance_status_ok')
        ec2_waiter.wait(InstanceIds=[ecs_ec2_instance1['Reservations'][0]['Instances'][0]['InstanceId']])

        print("Mount Volume to EC2 - " + ecs_cluster_name + instance_counter)

        ssm_client = boto3.client('ssm')
        print(ecs_ec2_instance1['Reservations'][0]['Instances'][0]['InstanceId'])
        ssm_client.send_command(InstanceIds=[ecs_ec2_instance1['Reservations'][0]['Instances'][0]['InstanceId']],
                                DocumentName="AWS-RunShellScript",
                                Parameters={'commands': ["sudo mkfs -t ext4 /dev/xvdg",
                                                         "sudo mkdir /scratch",
                                                         "sudo mount /dev/xvdg /scratch",
                                                         "sudo service docker restart",
                                                         "sudo start ecs"]})

if settings["CREATE_TASK"] == "True":
    APP_IMAGE_REPO = settings["APP_IMAGE_REPO"]
    ECS_CONTAINER_MEMORY = settings["CONTAINER_MEMORY"]
    ECS_CONTAINER_MEMORY_RESERVATION = settings["CONTAINER_MEMORY_RESERVATION"]
    CPU_UNITS = settings["CPU_UNITS"]

    create_ecs_task(ecs_client, ecs_task_family, ecs_cluster_name, ECS_CONTAINER_MEMORY, ECS_CONTAINER_MEMORY_RESERVATION, APP_IMAGE_REPO, CPU_UNITS, TASK_ROLE_ARN)
