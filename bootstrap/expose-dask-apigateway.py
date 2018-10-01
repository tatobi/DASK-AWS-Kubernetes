#!/usr/bin/env python3

import boto3
import yaml
import sys
import os
import time

#init boto
boto3.setup_default_session(profile_name='tamastobi')
REGION="eu-west-1"

#gw access policy
apigw_policy='''{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": "*",
            "Action": "execute-api:Invoke",
            "Resource": "*"
        }
    ]
}'''

print("START.")
print(time.ctime())

print("Get Network Load Balancers ...")
elbv2 = boto3.client('elbv2',region_name=REGION)
nlbs=elbv2.describe_load_balancers()

#get affected NLBs
NLBS={}
NLB1_ARN=""
NLB1_DNS=""
for lb in nlbs.get("LoadBalancers"):
    NLB_DNSName=lb.get("DNSName")
    NLB_ARN=lb.get('LoadBalancerArn')
    if NLB_DNSName.startswith("test-"):
      NLBS[NLB_ARN]=NLB_DNSName
      NLB1_ARN=NLB_ARN
      NLB1_DNS=NLB_DNSName


#create api gateway vpclink
print("Create API gateway VPCLink ...")
apigw = boto3.client('apigateway',region_name=REGION)


response = apigw.create_vpc_link(
    name='Jupyter-test',
    description='Jupyter HTTPS expose',
    targetArns=[
        NLB1_ARN
    ]
)
vpclink_id=response.get('id')
vpclink_status=response.get('status')
print(vpclink_id,vpclink_status)


#vpclink_id="wwau1q"

#wait max 10 mins for VPCLink to be done
for _ in range(120):
  response = apigw.get_vpc_link(
    vpcLinkId=vpclink_id
  )
  vpclink_status=response.get('status')
  print("Wait:",vpclink_id,vpclink_status)
  if vpclink_status == "AVAILABLE":
    break
  time.sleep(5)

#create rest apigw
print("Create API gateway RestAPI ...")
response = apigw.create_rest_api(
    name='Jupyter',
    description='Jupyter HTTPS expose',
    endpointConfiguration={
        'types': [
            'REGIONAL'
        ]
    },
    policy=apigw_policy
)
restapi_id=response.get('id')
print(restapi_id)

#restapi_id="btqqa352u9"
time.sleep(3)

print("Get API gateway RESTApi resources ...")
#get restapi resources
response = apigw.get_resources(
    restApiId=restapi_id
)
resource_id=response.get("items")[0].get("id")
print(resource_id)

#put ANY method
print("Create API gateway method: ANY ...")
response = apigw.put_method(
    restApiId=restapi_id,
    resourceId=resource_id,
    httpMethod='ANY',
    authorizationType='NONE',
    apiKeyRequired=False
)
print(response)

time.sleep(3)

#put integration
print("Create API gateway integration ...")
response = apigw.put_integration(
    restApiId=restapi_id,
    resourceId=resource_id,
    httpMethod="ANY",
    integrationHttpMethod='ANY',
    type='HTTP_PROXY',
    uri='http://'+NLB1_DNS,
    connectionType='VPC_LINK',
    connectionId=vpclink_id
)
#print(response)

time.sleep(3)

#create api deployment
print("Create API gateway deployment ...")
response = apigw.create_deployment(
    restApiId=restapi_id,
    description='jupyter',
    cacheClusterEnabled=False,
    variables={
        'vpcLinkId': vpclink_id
    },
    tracingEnabled=False
)
#print(response)
deplyment_id=response.get('id')
print(deplyment_id)

#deplyment_id='iceapp'
"""
response = apigw.get_deployments(
    restApiId=restapi_id
)
print(response)
"""

#deploy jupyter production
print("Create API gateway deployment stage ...")
response = apigw.create_stage(
    restApiId=restapi_id,
    stageName='jupyter',
    deploymentId=deplyment_id,
    description='jupyter',
    cacheClusterEnabled=False
)
print(response)

JUPYTER_URL="https://"+restapi_id+".execute-api."+REGION+".amazonaws.com"+"/jupyter"
print(JUPYTER_URL)

print("END.")
print(time.ctime())







