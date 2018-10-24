#!/usr/bin/env python3

import boto3
import yaml
import sys
import os
import time


print("START.")
print(time.ctime())


#defaults
region="eu-west-1"
kopsconf_input="demo.yaml"
kopsconf_additinalpolicies="kops-cluster-additionalpolicies.json"
kopsconf_output_file="out.yaml"
docker_awslogs_group="K8s-Docker"

#aws region
try:
    region=sys.argv[1]
except:
    print("define ARG1: region!")
    sys.exit(1)

#generated kops input config
try:
    kopsconf_input=sys.argv[2]
except:
    print("define ARG2: kops input config!")
    sys.exit(1)

#additional policies
try:
    kopsconf_additinalpolicies=sys.argv[3]
except:
    print("define ARG3: additional JSON policy files for master/nodes")
    sys.exit(1)
    

#output kops config yaml file
try:
    kopsconf_output_file=sys.argv[4]
except:
    print("define ARG4: kops output config")
    sys.exit(1)

#maxspotprice for nodes
max_spot_price_for_node=0.0
try:
    max_spot_price_for_node=sys.argv[5]
except:
    print("define ARG5: max spot price, unless 0: on-demand")
    pass

#nodes capacity max
max_nodes_capacity=None
try:
    max_nodes_capacity=sys.argv[6]
except:
    print("define ARG6: max number of nodes, unless equals min=max")
    pass

    
#mount s3fs bucket
mount_s3fs_bucket=None
try:
    mount_s3fs_bucket=str(sys.argv[7]).lower().strip()
except:
    print("define ARG8: mount S3 bucket name")
    pass
    
#goofys_url
goofys_url=""
try:
    goofys_url=str(sys.argv[8]).lower().strip()
except:
    print("define ARG9: goofys URL")
    pass

### INPUTS / end




if not os.path.exists(kopsconf_input):
  print("Missing kiops config input file!")
  sys.exit(1)

if not os.path.exists(kopsconf_additinalpolicies):
  print("Missing additonal policy file!")
  sys.exit(1)



yl=None

#[ {az-name: subnet_id} ... ]
private_subnets={}
public_subnets={}

#subnet config to replace in kops config
replace_subnets=[]

with open(kopsconf_input,"r") as f:
  yl=yaml.safe_load_all(f.read())

kops=list(yl)
vpcid=kops[0].get("spec").get("networkID")
ec2 = boto3.resource('ec2',region_name=region)
ec2client = boto3.client('ec2',region_name=region)
vpc = ec2.Vpc(vpcid)
subnet_iterator = vpc.subnets.all()

#determine private subnets by routes (NO igw in routes associated with subnet)
for s in subnet_iterator:
  public=False
  sid=s.subnet_id
  az=s.availability_zone
  #print sid
  #print az
  response = ec2client.describe_route_tables(
      Filters=[
          {
              'Name': 'association.subnet-id',
              'Values': [
                  sid
              ]
          }
      ]
  )
  rtb = response['RouteTables'][0]['Associations'][0]['RouteTableId']
  rotb = ec2.RouteTable(rtb)
  #print "Routes:"
  for r in rotb.routes:
    #print r.nat_gateway_id
    #print r.gateway_id
    if r.gateway_id:
      if r.gateway_id.startswith("igw-"):
        #print r.gateway_id
        #print "skip"
        public=True
  if public:
    public_subnets[az]=sid
    continue
  private_subnets[az]=sid

print("Private subnets in VPC: ", vpcid)
print(private_subnets)
print("Public subnets in VPC: ", vpcid)
print(public_subnets)


#replace config cidr with id
subnets = kops[0].get("spec").get('subnets')
for subnet in subnets:
  if subnet.get('type') == "Utility":
    continue
  zone=subnet.get('zone')
  zname=subnet.get('name')
  ztype=subnet.get('type')
  newprivatezone={}
  if zone in private_subnets:
    newprivatezone['id']=private_subnets[zone]
    newprivatezone['zone']=zone
    newprivatezone['name']=zname
    newprivatezone['type']=ztype
  if newprivatezone:
    replace_subnets.append(newprivatezone)

for zone,sid in public_subnets.items():
  newpubliczone={}
  newpubliczone['id']=sid
  newpubliczone['zone']=zone
  newpubliczone['name']="utility-"+zone
  newpubliczone['type']='Utility'
  if newpubliczone:
    replace_subnets.append(newpubliczone)


print("Set new subnet definitions ...")
print(replace_subnets)
kops[0]['spec']['subnets']=replace_subnets

print("Add calico inter-AZ networking ...")
kops[0]['spec']['networking'] = {"calico": {"crossSubnet":True}}

print("Add swap accept in GENERAL config")
kops[0]['spec']['kubelet'] = {"failSwapOn":False}

print("Enable POD autoscaling ...")
kops[0]['spec']['kubeAPIServer'] = {"runtimeConfig": {"autoscaling/v2beta1":"true"}}

##########################
# node configs
##########################
#print "Add swap accept in MASTER config
kops[1]['spec']['kubelet'] = {"failSwapOn":False}
kops[1]['spec']['additionalUserData'] = [{'content': '#!/bin/bash -xe\ndd if=/dev/zero of=/swapfile count=8192 bs=1MiB\nchmod 600 /swapfile\nmkswap /swapfile\nswapon /swapfile\nsysctl vm.swappiness=10\nsysctl vm.vfs_cache_pressure=50\n', 'type': 'text/x-shellscript', 'name': 'swap.sh'},{'content': '#!/bin/bash -xe\napt-get update\napt-get -y install nfs-common\n', 'type': 'text/x-shellscript', 'name': 'nfs.sh'},{'content': '#!/bin/bash -xe\necho "* * * * * root sed -i \'0,/^$/ s/^$/exit 0/\' /opt/kubernetes/helpers/docker-healthcheck" >> /etc/crontab\n', 'type': 'text/x-shellscript', 'name': 'docker-healthcheck.sh'}]


#print "Add swap accept in NODES config
kops[2]['spec']['kubelet'] = {"failSwapOn":False}
kops[2]['spec']['additionalUserData'] = [{'content': '#!/bin/bash -xe\ndd if=/dev/zero of=/swapfile count=8192 bs=1MiB\nmkswap /swapfile\nswapon /swapfile\nsysctl vm.swappiness=10\nsysctl vm.vfs_cache_pressure=50\n', 'type': 'text/x-shellscript', 'name': 'swap.sh'},{'content': '#!/bin/bash -xe\napt-get update\napt-get -y install nfs-common\n', 'type': 'text/x-shellscript', 'name': 'nfs.sh'},{'content': '#!/bin/bash -xe\necho "* * * * * root sed -i \'0,/^$/ s/^$/exit 0/\' /opt/kubernetes/helpers/docker-healthcheck" >> /etc/crontab\n', 'type': 'text/x-shellscript', 'name': 'docker-healthcheck.sh'}]


#append goofys s3fs mount to nodes config
if mount_s3fs_bucket and goofys_url:
  if ((mount_s3fs_bucket != "NONE") and (goofys_url != "NONE")):
    kops[2]['spec']['additionalUserData'].append({'content': '#!/bin/bash -xe\nwget -O /usr/local/bin/goofys '+goofys_url+' --no-verbose\nchmod +x /usr/local/bin/goofys\necho "allow_other" >> /etc/fuse.conf\n', 'type': 'text/x-shellscript', 'name': 'goofys.sh'})
    kops[2]['spec']['additionalUserData'].append({'content': '#!/bin/bash -xe\nmkdir -p /mnt/s3fs\nchmod 777 /mnt/s3fs\n/usr/local/bin/goofys -o allow_other -o nonempty -o rw --dir-mode 0777 --file-mode 0777 --uid 0 --gid 0 --region '+region+' '+mount_s3fs_bucket+' /mnt/s3fs\n', 'type': 'text/x-shellscript', 'name': 'mounts3fs.sh'})

kops[2]['spec']['nodeLabels']["beta.kubernetes.io/fluentd-ds-ready"]="true"
##########################


if max_spot_price_for_node:
  if max_spot_price_for_node != "NONE":
    print("Set MAX SPOT price for NODES: ",str(max_spot_price_for_node))
    try:
      max_spot_price_for_node=float(max_spot_price_for_node)
      if max_spot_price_for_node > 0.0:
        kops[2]['spec']['maxPrice']=str(max_spot_price_for_node)
    except Exception as e:
      print("SPOT ERROR:",str(e))
      pass

#set maximum size for NODES
if max_nodes_capacity:
  if max_nodes_capacity != "NONE":
    print("Set MAX ASG size for NODES: ",str(max_nodes_capacity))
    try:
      kops[2]['spec']['maxSize']=int(max_nodes_capacity)
    except Exception as e:
      print("MAXSIZE ERROR:",str(e))
      pass
      
print("Apply new policies ...")
if os.path.exists(kopsconf_additinalpolicies):
  print("Add policy file: ", kopsconf_additinalpolicies)
  ap=""
  with open(kopsconf_additinalpolicies,"r") as f:
    ap=f.read()
  additionalpolicies = {'node': ap, 'master': ap}
  #print additionalpolicies
  kops[0]['spec']['additionalPolicies']=additionalpolicies

out=yaml.safe_dump_all(kops, default_flow_style=False)
print(out)
with open(kopsconf_output_file,"w") as f:
  f.write(out)

sys.exit(0)
