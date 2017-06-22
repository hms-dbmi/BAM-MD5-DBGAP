def attach_volume_to_ecs_ec2(ec2_client, ecs_settings, ecs_ec2_instance):

    volume_size = ecs_settings["VOLUME_SIZE"]
    availability_zone = ecs_settings["AVAILABILITY_ZONE"]
    volume_type = ecs_settings["VOLUME_TYPE"]
    device_mount = ecs_settings["DEVICE_MOUNT"]

    new_volume = ec2_client.create_volume(Size=int(volume_size),
                                          Encrypted=True,
                                          AvailabilityZone=availability_zone,
                                          VolumeType=volume_type)

    volume_waiter = ec2_client.get_waiter('volume_available')

    volume_waiter.wait(VolumeIds=[new_volume["VolumeId"]])

    ec2_client.attach_volume(VolumeId=new_volume["VolumeId"],
                             InstanceId=ecs_ec2_instance['Reservations'][0]['Instances'][0]['InstanceId'],
                             Device=device_mount)
