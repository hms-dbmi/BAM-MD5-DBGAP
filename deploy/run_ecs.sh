#!/usr/bin/env bash

aws ecs run-task --cluster MD5S3-PROD \
                 --task-definition MD5S3-PROD-task_family \
                --overrides "{\"containerOverrides\":[{\"name\":\"MD5S3-PROD\",\"environment\": [{\"name\":\"INPUT_QUEUE_NAME\",\"value\": \"MD5\"},{\"name\":\"OUTPUT_QUEUE_NAME\",\"value\": \"MD5_DONE\"}]}]}"