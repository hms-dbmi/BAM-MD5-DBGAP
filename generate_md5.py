import boto3
import hashlib
import os
import subprocess
import errno
import sys
import time


def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise

input_queue_name = os.environ["INPUT_QUEUE_NAME"]
output_queue_name = os.environ["OUTPUT_QUEUE_NAME"]

# --------------------------
# RESOURCES
# --------------------------
s3_resource = boto3.resource("s3")
s3_client = boto3.client('s3')
sqs = boto3.resource('sqs')

print("INPUT_QUEUE_NAME " + input_queue_name)
print("OUTPUT_QUEUE_NAME " + output_queue_name)

input_queue = sqs.get_queue_by_name(QueueName=input_queue_name)
output_queue = sqs.get_queue_by_name(QueueName=output_queue_name)
# --------------------------


# --------------------------

# Temporary File Name.
tempDownloadedFile = "/scratch/md5"

# Set up output file.
timestr = time.strftime("%Y%m%d-%H%M%S")
md5_out_file = open("/scratch/md5_out" + timestr, "w+", 1)

while True:

    # --------------------------
    # LOOP THROUGH MESSAGES TO PROCESS
    # --------------------------
    print("Retrieving messages from queue - '" + input_queue_name + "'", flush=True)

    for message in input_queue.receive_messages(MaxNumberOfMessages=1,
                                          MessageAttributeNames=['UDN_ID', 'FileBucket', 'FileKey', 'sample_ID', 'file_service_uuid']):

        print("Found Messages, processing.", flush=True)

        if message.message_attributes is not None:

            UDN_ID = message.message_attributes.get('UDN_ID').get('StringValue')
            sequence_core_alias = message.message_attributes.get('sequence_core_alias').get('StringValue')

            FileBucket = message.message_attributes.get('FileBucket').get('StringValue')
            FileKey = message.message_attributes.get('FileKey').get('StringValue')

            Sample_ID = message.message_attributes.get('sample_ID').get('StringValue')
            fileservice_uuid = message.message_attributes.get('file_service_uuid').get('StringValue')

            # --------------------------
            # DOWNLOAD FILES
            # --------------------------
            print("Downloading File " + FileKey, flush=True)
            s3_client.download_file(FileBucket, FileKey, tempDownloadedFile)

            # --------------------------
            # PROCESS BAM FILES TO REPLACE IDS.
            # --------------------------

            print("Processing BAM with samtools. UDN_ID - " + UDN_ID + " Sample_ID - " + Sample_ID, flush=True)

            try:
                subprocess.call(["/output/rehead_bam.sh", sequence_core_alias, Sample_ID])
                subprocess.call(["/output/rehead_bam.sh"], UDN_ID, '')
                print("Done processing file. Begin MD5.", flush=True)
            except:
                print("Error processing BAM - ", sys.exc_info()[:2], flush=True)
                silentremove(tempDownloadedFile)
                silentremove("/scratch/md5_reheader")
                silentremove("/scratch/header.sam")
                continue

            # --------------------------
            # GENERATE MD5
            # --------------------------
            md5 = hashlib.md5(open("/scratch/md5_reheader", 'rb').read()).hexdigest()

            # --------------------------
            # OUTPUT RESULTS
            # --------------------------
            md5_out_file.write("{0},{1},{2}\n".format(fileservice_uuid, FileKey, md5))

            print("----------\n", flush=True)
            print("FileService UUID : %s\n" % fileservice_uuid, flush=True)
            print("File Name : %s\n" % FileKey, flush=True)
            print("MD5 : %s\n" % md5, flush=True)
            print("----------\n", flush=True)
            print("\n", flush=True)

            output_queue.send_message(MessageBody='boto3', MessageAttributes={
                'UDN_ID': {
                    'StringValue': UDN_ID,
                    'DataType': 'String'
                },
                'FileBucket': {
                    'StringValue': FileBucket,
                    'DataType': 'String'
                },
                'FileKey': {
                    'StringValue': FileKey,
                    'DataType': 'String'
                },
                'sample_ID': {
                    'StringValue': Sample_ID,
                    'DataType': 'String'
                },
                'file_service_uuid': {
                    'StringValue': fileservice_uuid,
                    'DataType': 'String'
                },
                'md5': {
                    'StringValue': md5,
                    'DataType': 'String'
                },
                'file_type': {
                    'StringValue': 'BAM',
                    'DataType': 'String'
                }
            })

            message.delete()
            silentremove(tempDownloadedFile)
            silentremove("/scratch/md5_reheader")
            silentremove("/scratch/header.sam")

    time.sleep(10)
