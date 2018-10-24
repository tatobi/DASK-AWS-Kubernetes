# DASK-AWS-Kubernetes

A "One-Click solution" to deploy a scalable and secure Kubernes + DASK cluster in one step on AWS in 10 minutes. 

The solution has many advanced and configurable options via AWS CloudFormation, only requires minimal knowledge of AWS and Kubernetes. It is ideal if you need a secure, private DASK cluster to process your own data.

It is hihly recommended to use an S3 bucket and mount it to persist your notebook files. (see below)

The Jupyter notebook data persisted to private, mounted S3 buckets.

**NOTE:** [DASK](https://dask.org/) is a scalable, distributed Python based data analytics / data science tool.

# Main features

* One-click, automated Kubernetes + DASK deployment
* Kubernetes cluster node and pod auto-scaling, 100% Kubernetes compatibility using [KOPS](https://github.com/kubernetes/kops/blob/master/README.md)
* Automated OpenVPN setup, immediate private access to JupyterLab (notebooks) and DASK scheduler via VPN
* SPOT EC2 worker node usage possibility to cut costs
* S3 bucket mount on all nodes to persist notebooks and access S3 data easily
* Custom Jupyter password setup
* Install custom PIP and Conda packages (list) during bootstrap
* Ability to us customized DASK Docker images
* Notify via SNS when cluster is deployed and ready to use
* One-click deployment tear-down
* AWS region independent dynamic AMI image selection

**NOTE:** I always keep focus on security and flexibility, so the deployed cluster is running in private AWS VPC and accessible only via OpenVPN. The VPN setup is automated so only a client application needed to sue it. I do not change the original Docker images. All deployment running on separately created AWS VPC. 


# Architecture and details

## AWS architecture

The deployment architecture consist of two parts, the first is the Kubernetes running on AWS and the DASK deployment on the Kubernetes cluster.

[![N|Solid](https://raw.githubusercontent.com/tatobi/DASK-AWS-Kubernetes/master/docs/k8s-small-footprint.png)](https://raw.githubusercontent.com/tatobi/DASK-AWS-Kubernetes/master/docs/k8s-small-footprint.png)


## One-Click solution - AWS Quick-Start

One-click setup on AWS via CloudFormation:

[Quck-Start Deploy to AWS-EU Ireland region](https://console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks/new?stackName=DASK-AWS-Kubernetes&templateURL=https://s3-eu-west-1.amazonaws.com/tatobi-dask-aws-deploy/latest/cfn-templates/dask-aws-deploy-template.yaml)


[Quick-Start Deploy to AWS-US North Virginia region](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=DASK-AWS-Kubernetes&templateURL=https://s3-eu-west-1.amazonaws.com/tatobi-dask-aws-deploy/latest/cfn-templates/dask-aws-deploy-template.yaml)

## Template

View / copy and paste the template to your AWS CloudFormation / create - stack page:
[https://s3-eu-west-1.amazonaws.com/tatobi-dask-aws-deploy/latest/cfn-templates/dask-aws-deploy-template.yaml](https://s3-eu-west-1.amazonaws.com/tatobi-dask-aws-deploy/latest/cfn-templates/dask-aws-deploy-template.yaml)



## CloudFormation parameters


**NOTE:** There are default CFN parameters, you do not need to change them to deploy your cluster. The above documentation helps you customize the deployment according your needs.


### AWS and Kubernetes Configuration

- **Creates a new VPC with defined CIDR block**: the newly created VPC Ipv4 CIDR

- **Bastion Allowed Access - IPv4 CIDR**: from where the bastion host accessible, 0.0.0.0/0 means public.


### AWS EC2 / Kubernetes Configuration

- **Existing EC2 keypair name for instances**: previously created Ec2 keypair name (access the cluster via SSH, [EC2 KeyPair](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html)) **!REQUIRED!**

- **Bastion instance type**: the bastion host AWS EC2 instance type ([EC2 types and prices](https://aws.amazon.com/ec2/pricing/on-demand/))

- **K8s Master Instances Type**: Kubernetes cluster MASTER node EC2 instance type ([EC2 types and prices](https://aws.amazon.com/ec2/pricing/on-demand/))

- **K8s Nodes Instances Type**: Kubernetes cluster NODES EC2 instance type ([EC2 types and prices](https://aws.amazon.com/ec2/pricing/on-demand/))

- **K8s Nodes SPOT MAX Bid price /h**: Kubernetes nodes maximum SPOT price. If you leave 0, empty or negative, on-demand instances deployed. ([EC2 SPOT types and prices](https://aws.amazon.com/ec2/spot/pricing/))

- **K8s AutoScaling MINIMUM Node Number**: The minimum number of deployed as Kubernetes NODES. 3 is required as the minimum.

- **K8s AutoScaling MAXIMUM Node Number**: The maximum number of deployed as Kubernetes NODES. The maximum used by the cluster-autoscaling. The [cluster-autoscaler](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler) plugin is deployed by default.

- **K8s AutoScaling MINIMUM Node Number**: The minimum number of deployed as Kubernetes NODES. 3 is required as the minimum.

- **K8s Instances Disk Size**: The AWS EBS volume attached to Kubernetes cluster members as a root volume (GB).

- **S3 bucket NAME for CFN Bootstrap Files**: The S3 bucket name, where the Kubernetes cluster bootstrap files and DASK bootstrap files are located. The default used **tatobi-dask-aws-deploy** is public read-only, you can fork the whole solution, modify the files and replace this bucket with your one.

- **S3 key prefix for CFN Bootstrap Files**: The above bootstrap bucket "subfolder" (or S3 key) where the boostrap files are located.

- **DASK mounted S3 bucket name to work subfolder**: If NOT empty, this S3 bucket will be mounted to: **/home/jovyan/work** You can store the processed data, the results and Jupyter notebooks here.

- **KOPS relese number**: Which [KOPS](https://github.com/kubernetes/kops/blob/master/README.md) version is used to deploy the cluster. Keep default **1.10.0**

- **kubectl release number**: Which [Kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) version is used to deploy the cluster. Keep default **1.10.7**

- **helm release number**: Which [HELM](https://helm.sh/) version is used to deploy the cluster. Keep default **2.10.0**

- **Kubernetes and bastion host OS**: Ubuntu 16.04LTS is the currently supported OS verion only. The latest 18.04LTS support coming soon (depends on KOPS).

- **Download link for Goofys S3FS binary**: The S3FS mount uses [Goofys](https://github.com/kahing/goofys), it is the download URL of binary.


### Advanced DASK Configuration

- **Password for access DASK JupyterLab notebook**: The login password for JupyterLab notebook

- **AWS SNS topic ARN for DASK setup finsihed notifications**: If you have and already existing [AWS SNS](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/receiving-email-action-sns.html) notification topic, this ARN can be used to notify you when the deployment is ready.

- **Password for access DASK JupyterLab notebook**: The login password for JupyterLab notebook

- **Custom DASK Jupyter Docker image URI**: We use the default HELM and [DASK Docker images](https://github.com/dask/dask-docker) if you leave empty, if not, paste here your own DASK Jupyter Docker image path. It maybe useful if you have many pre-installed pip, conda packages, custom binaries or data placed in your images.

- **Custom DASK Worker Docker image URI**: We use the default HELM and [DASK Docker images](https://github.com/dask/dask-docker) if you leave empty, if not, paste here your own DASK Worker Docker image path.

- **Comma separated list of extra CONDA packages to install**: Define here which [CONDA](https://conda.io/docs/) packages need to be installed during the deployment.

- **Comma separated list of extra Python PIP packages to install**: Define here which [Python PIP](https://packaging.python.org/tutorials/installing-packages/) packages need to be installed during the deployment.


**NOTE:** "I acknowledge that AWS CloudFormation might create IAM resources." should be checked.


# Access DASK

Because the deployment does not need HTTPS (SSL) connection, but the secure access is essential I've chosen [OpenVPN](https://openvpn.net/private-tunnel/) to connect your machine or your on-premises to the Kubernetes - DASK cluster running on AWS.

## OpenVPN

**[1]:** Download and install OpenVPN on your client Operating System:

- **LINUX:** is your OS:

RedHat / Fedora / CentOS:

```sudo yum install openvpn ```

Ubuntu / Debian:

```sudo apt install openvpn ```

- **WINDOWS:** use WINDOWS INSTALLER (NSIS) :

[OpenVPN Download](https://openvpn.net/community-downloads/)

- **Apple MAC OSX**:

[TunnelBlick](https://tunnelblick.net/downloads.html)

- **Android**:

[Googl App store / OpenVPN](https://play.google.com/store/apps/details?id=net.openvpn.openvpn)


**[2]:** Download OpenVPN connection profile from your AWS CloudFormation stack output

- Go to the AWS console **CloudFormation** page

- Choose your Stack Name checkbox (default: "DASK-AWS-Kubernetes")

- Click on **Outputs** TAB (below)

- Click on **DownloadOpenVPNConfigURL** URL and save it **openvpn-secrets.zip**

- UNZIP the **openvpn-secrets.zip** file with your **DASJupyterAndUnZIPPassword** Output password ans save one of the *.ovpn file to you machine, the example file name is: DASK.OVPN.dask-aws-kubernetes.1.ovpn

- Connect OpenVPN: WINDOWS: double click file / import OpenVPN profile / connect, on Linux:

```
sudo openvpn --config DASK.OVPN.dask-aws-kubernetes.1.ovpn
```

- Download DASK URL file: on **Output** tab, choose **DownloadDASKAccessURL** download and save the **dask-connection.zip** file, UNZIP it with the same **DASJupyterAndUnZIPPassword** password, save and open text file: **dask-connection.zip**

- open the **dask-connection.txt** and extract information: 

Open URLs:

**Jupyter Lab URL:** http://internal-........elb.amazonaws.com/

**DASK scheduler URL:** http://internal-........elb.amazonaws.com/

Login to Jupyter Lab with **DASJupyterAndUnZIPPassword**

**NOTE:** These are AWS internal Loadbalancers, they have internal private IP addresses, so there is no external public acccess, only via OpenVPN.


**[3]:** OPTIONAL: if you use S3FS S3 bucket mounts, save your data (from cluster or remotely), notebooks to **/home/jovyan/work** 

**NOTE:** Every node has this S3 mount path accessible, not just the JupyterLab!


# Delete stack

There is a seamless tear-down integration in the deployment. If you don't need the deployment anymore, go to AWS Console , CloudFormation page, chosse your stack and choose Actions -> Delete stack.


# References

There are 3 open source projects I created previously, the current solution consists common parts from them:

[#1: kubernetes-aws](https://github.com/totalcloudconsulting/kubernetes-aws)

[#2: aws-dask-kubernetes](https://github.com/OpenSatori/AWS-DASK-Kubernetes)

[#3: easy-openvpn](https://github.com/tatobi/easy-openvpn)


