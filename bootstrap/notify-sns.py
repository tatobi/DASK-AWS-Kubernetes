#!/usr/bin/env python3

import sys
import boto3

aws_region=sys.argv[1]
snstopicarn=sys.argv[2]
cfnstackname=sys.argv[3]
jupyter_password=sys.argv[4]
jupyter_url=sys.argv[5]
scheduler_url=sys.argv[6]

sns = boto3.client('sns', region_name=aws_region)

try:
    snsmessage="AWS SNS notification: DASK Kubernetes cluser creation has been finished.\n\n-------------\n\nAWS CFN stack name: %s\n\nJupyter HTTPS URL: %s\n\nJupyter login password: %s\n\nScheduler HTTPS URL: %s\n\n-------------\n\n" % (cfnstackname,jupyter_url,jupyter_password,scheduler_url)

    response = sns.publish(
        TopicArn=snstopicarn,
        Message=snsmessage,
        Subject='DASK Kubernetes cluster on AWS creation has been finished: '+cfnstackname,
    )
except Exception as e:
    print(e)
