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
    snsmessage="AWS SNS notification: DASK Kubernetes cluser creation has been finished.\n\n-------------\nPLEASE WAIT A FEW MINUTES FOR DNS SYNC BEFORE ACCESS URLs!\n-------------\n\nAWS CFN stack name: %s\n\nJupyter access URL: %s\n\nJupyter notebook login password: %s\n\nScheduler access URL: %s\n\n-------------\n\nPLEASE DOWNLOAD THE VPN CONFIGURATION FROM CFN OUTPUT LINK URL FIRST.\n\n-------------\n" % (cfnstackname,jupyter_url,jupyter_password,scheduler_url)

    response = sns.publish(
        TopicArn=snstopicarn,
        Message=snsmessage,
        Subject='AWS DASK cluster creation has been finished: '+cfnstackname,
    )
except Exception as e:
    print(e)

