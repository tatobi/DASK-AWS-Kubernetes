# DASK-AWS-Kubernetes

A "One-Click solution" to deploy a scalable and secure DASK deployment on AWS in 10 minutes. My solution has many advanced and configurable options via AWS CloudFormation.

I always keep focus on security and flexibility, so the deployed cluster is running in private AWS VPC and accessible only via OpenVPN. The VPN setup is automated so only a client application needed to sue it.

The Jupyter notebook data persisted to private, mounted S3 buckets.

**NOTE:** [DASK](https://dask.org/) is a scalable, distributed Python based data analytics / data science tool.

# Main features

* One-click, automated Kubernetes + DASK deployment
* Kubernetes cluster node and pod auto-scaling, 100% Kubernetes compatibility using [KOPS](https://github.com/kubernetes/kops/blob/master/README.md)
* Automated OpenVPN setup, immediate private access to JupyterLab (notebooks) and DASK scheduler via VPN
* SPOT EC2 worker node usage possibility to reduce costs
* S3 bucket mount on all nodes to persist notebooks and access S3 data easily
* Custom Jupyter password setup
* Install custom PIP and Conda packages (list) during bootstrap
* Ability to us customized DASK Docker images
* Notify via SNS when cluster is deployed and ready to use
* One-click deployment tear-down


# Deployment

## One-Click solution

One-click setup on AWS via CloudFormation:

[Deploy to AWS-EU Ireland region](https://console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks/new?stackName=DASK-AWS-Kubernetes&templateURL=https://s3-eu-west-1.amazonaws.com/tatobi-dask-aws-deploy/latest/cfn-templates/dask-aws-deploy-template.yaml)


[Deploy to AWS-US North Virginia region](https://console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks/new?stackName=DASK-AWS-Kubernetes&templateURL=https://s3-eu-west-1.amazonaws.com/tatobi-dask-aws-deploy/latest/cfn-templates/dask-aws-deploy-template.yaml)

## Template

View / copy and paste the template to your AWS CloudFormation / create - stack page:
[https://s3-eu-west-1.amazonaws.com/tatobi-dask-aws-deploy/latest/cfn-templates/dask-aws-deploy-template.yaml](https://s3-eu-west-1.amazonaws.com/tatobi-dask-aws-deploy/latest/cfn-templates/dask-aws-deploy-template.yaml)

# Architecture

The deployment architecture consist of two parts, the first is the Kubernetes running on AWS and the DASK deployment on the Kubernetes cluster.

[![N|Solid](https://raw.githubusercontent.com/totalcloudconsulting/kubernetes-aws/master/docs/k8s-small-footprint.png)](https://raw.githubusercontent.com/totalcloudconsulting/kubernetes-aws/master/docs/k8s-small-footprint.png)


# Parameters

# References

There are 3 open source projects I created previously, the current solution consists common parts from them:

[#1: kubernetes-aws](https://github.com/totalcloudconsulting/kubernetes-aws)

[#2: aws-dask-kubernetes](https://github.com/OpenSatori/AWS-DASK-Kubernetes)

[#3: easy-openvpn](https://github.com/tatobi/easy-openvpn)


