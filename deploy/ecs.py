import time

def create_ecs_cluster(ecs_client, cluster_name):
    ecs_client.create_cluster(clusterName=cluster_name)


def create_ecs_task(ecs_client, task_family, cluster_name, container_memory, container_memory_reservation, app_image_repo, cpu_units, task_role_arn):

    app_image_enviro_repo = app_image_repo

    container_definition = [{
        'name': cluster_name,
        'image': app_image_enviro_repo,
        'memoryReservation': int(container_memory_reservation),
        'memory': int(container_memory),
        'cpu': int(cpu_units),
        'mountPoints': [
            {
                "sourceVolume": "scratch",
                "containerPath": "/scratch/"
            }
        ]
    }]

    volume_definition = [{'name': 'scratch', 'host': {"sourcePath": "/scratch/"}}]

    ecs_client.register_task_definition(family=task_family, containerDefinitions=container_definition, volumes=volume_definition, taskRoleArn=task_role_arn)


def create_ecs_ec2(stack_name, cluster_name, vpc, ec2, userdata_string, ecs_settings, machine_tags):

    machine_tags.append({"Key": "Name", "Value": cluster_name})

    ec2_security_groups = list(vpc.security_groups.filter(Filters=[{'Name': 'tag:Name', 'Values': [stack_name + '_SG']}]))[0]

    new_instance = ec2.create_instances(ImageId=ecs_settings['AMI_IMAGE_ID'],
                                        MinCount=1,
                                        MaxCount=1,
                                        InstanceType=ecs_settings['EC2_INSTANCE_TYPE'],
                                        SecurityGroupIds=[ec2_security_groups.id],
                                        KeyName=ecs_settings['EC2_KEY_NAME'],
                                        UserData=userdata_string,
                                        IamInstanceProfile={"Arn": ecs_settings['EC2_IAM_INSTANCE_PROFILE_ARN']},
                                        Placement={'AvailabilityZone': ecs_settings['AVAILABILITY_ZONE']})
    time.sleep(10)
    new_instance[0].create_tags(Tags=machine_tags)
    new_instance[0].wait_until_running()
















