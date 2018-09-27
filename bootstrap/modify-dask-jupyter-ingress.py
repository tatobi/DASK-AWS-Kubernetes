#!/usr/bin/env python3

import boto3
import yaml
import sys
import os
import time


print("START.")
print(time.ctime())

#input_file
try:
    input_file=sys.argv[1]
except:
    print("define input_file!")
    sys.exit(1)

#output_file
try:
    output_file=sys.argv[2]
except:
    print("define output_file!")
    sys.exit(1)

with open(input_file,"r") as f:
  yl=yaml.safe_load_all(f.read())

dask=list(yl)

print(dask)

print("Set internal LB ...")
#dask[0]['spec']['type']='NodePort'
dask[0]['metadata']['annotations']=[{'service.beta.kubernetes.io/aws-load-balancer-internal': '0.0.0.0/0'},{'service.beta.kubernetes.io/aws-load-balancer-type': 'nlb'}]

out=yaml.safe_dump_all(dask, default_flow_style=False)
print(out)
with open(output_file,"w") as f:
  f.write(out)

sys.exit(0)
