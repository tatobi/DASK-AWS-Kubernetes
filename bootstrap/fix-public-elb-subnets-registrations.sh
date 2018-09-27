#!/bin/bash

AWSRegion=${1}

for i in `cat /opt/kops-state/KOPS_PUBLIC_SUBNETS`; 
do 
    echo $i; 
    zone=`aws ec2 describe-subnets --subnet-ids ${i} --output text --region ${AWSRegion} | grep 'SUBNETS' | awk '{print $3}'`;
    echo ${zone};

    for j in `aws elb describe-load-balancers --region ${AWSRegion} | grep "LoadBalancerName" | grep -v api | cut -d ':' -f 2 | cut -d '"' -f 2`; 
    do 
      echo "Adjust ELB: $j, attach to Subnet: $i ...";
      aws elb attach-load-balancer-to-subnets --load-balancer-name ${j} --subnets ${i} --region ${AWSRegion}
    done
done
