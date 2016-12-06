import boto3
import hashlib
import os
import copy
import subprocess
import errno
import sys


def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


# --------------------------
# RESOURCES
# --------------------------
s3_resource = boto3.resource("s3")
s3_client = boto3.client('s3')
# --------------------------

# --------------------------
# PARSING ID FILE
# --------------------------
ID_FILE = "/output/s3_fileservice"
SAMPLE_ID_FILE = "/output/sample_fileservice"

file_keys = []

with open(ID_FILE, "r") as id_file_handle:
    for entry in id_file_handle:
        tmp = str(entry).strip().split(",")
        try:
            file_keys.append([tmp[0], tmp[1]])
        except: pass

file_keys_copy = copy.deepcopy(file_keys)

file_sample_map = {}

with open(SAMPLE_ID_FILE, "r") as id_file_handle:
    for entry in id_file_handle:
        tmp = str(entry).strip().split(",")
        try:
            file_sample_map[tmp[0]] = [tmp[1], tmp[2]]
        except: pass

# --------------------------

# Temporary File Name
tempDownloadedFile = "/scratch/md5"

print(file_sample_map)
print(file_keys)

# --------------------------
# LOOP THROUGH FILES TO PROCESS
# --------------------------
for file_key in file_keys:

    # --------------------------
    # DOWNLOAD FILES
    # --------------------------
    file_s3_url = file_key[1]
    fileservice_uuid = file_key[0]
    bucket, key = file_s3_url.split('/', 2)[-1].split('/', 1)

    print("Downloading File " + key)
    s3_client.download_file(bucket, key, tempDownloadedFile)

    # --------------------------
    # PROCESS BAM FILES TO REPLACE IDS.
    # --------------------------

    UDN_ID = file_sample_map[fileservice_uuid][0]
    Sample_ID = file_sample_map[fileservice_uuid][1]

    print("Processing BAM with samtools. UDN_ID - " + UDN_ID + " Sample_ID - " + Sample_ID, flush=True)

    try:
        subprocess.call(["/output/rehead_bam.sh", UDN_ID, Sample_ID])
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

    silentremove(tempDownloadedFile)
    silentremove("/scratch/md5_reheader")
    silentremove("/scratch/header.sam")

    # --------------------------
    # OUTPUT RESULTS
    # --------------------------
    print("----------\n")
    print("FileService UUID : %s\n" % fileservice_uuid)
    print("File Name : %s\n" % file_key)
    print("MD5 : %s\n" % md5)
    print("----------\n")
    print("\n")

    # --------------------------
    # UPDATE FILES TO BE PROCESSED
    # --------------------------
    if len(file_keys_copy) > 0:
        file_keys_copy.remove(file_key)

        with open(ID_FILE, 'w') as fp:
            fp.truncate()
            for x in file_keys_copy:
                fp.write("{0},{1}\n".format(x[0], x[1]))