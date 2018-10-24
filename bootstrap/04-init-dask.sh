#!/bin/bash

echo "#################"
echo "DASK-INIT START..."

AWSRegion=${1}
AWSCfnStackName=${2}
BastionSecurityGroup=${3}
DASKJupyterPassword=${4}
DASKFinishedSetupSNSArn=${5}
Ec2K8sNodeCapacityMin=${6}
DASKCustomJupyterDockerImage=${7}
DASKCustomWorkerDockerImage=${8}
DASKExtraCondaPackages=${9}
DASKExtraPipPackages=${10}
Ec2K8sNodeCapacityMax=${11}
LambdaGenerateKubernetesStateS3Bucket=${12}

echo "#################"
echo "START INIT-DASK."

echo "$@"

DASKExtraCondaPackages_NO_WHITESPACE=""
if [[ -n ${DASKExtraCondaPackages} ]];
then
    DASKExtraCondaPackages_NO_WHITESPACE="$(echo -e "${DASKExtraCondaPackages}" | tr -d '[:space:]')"
fi

DASKExtraPipPackages_NO_WHITESPACE=""
if [[ -n ${DASKExtraPipPackages} ]];
then
    DASKExtraPipPackages_NO_WHITESPACE="$(echo -e "${DASKExtraPipPackages}" | tr -d '[:space:]')"
fi

randomstuff=`cat /dev/urandom | tr -dc 'a-z0-9' | head -c 8`
instance_id=`curl http://169.254.169.254/latest/meta-data/instance-id`
AWSCfnStackName=`echo "${AWSCfnStackName}" | tr '[:upper:]' '[:lower:]'`
DASKCluserName=${AWSCfnStackName}
AWSStackName=${AWSCfnStackName}

export KOPS_STATE_STORE=`cat /opt/kops-state/KOPS_STATE_STORE`
export KOPS_CLUSTER_NAME=`cat /opt/kops-state/KOPS_CLUSTER_NAME`
export AWS_DEFAULT_REGION=${AWSRegion}
export HOME="/opt"

kops export kubecfg --name ${KOPS_CLUSTER_NAME}

####################################
#init helm
####################################
helm init

tilrun=""
for _ in {1..30};
do
    tilrun=`kubectl get pods --all-namespaces | grep "tiller" | grep "Running"`
    if [[ -n "${tilrun}" ]];
    then
        echo "Tiller POD running ... ${tilrun}"
        break
    else
        sleep 5
    fi
done

sleep 15

tilsvc=""
for _ in {1..30};
do
    tilsvc=`kubectl get svc --all-namespaces | grep "tiller-deploy"`
    if [[ -n "${tilsvc}" ]];
    then
        echo "Tiller SVC running ... ${tilsvc}"
        break
    else
        sleep 5
    fi
done

sleep 5

helm version

####################################
#install DASK
####################################

echo "Install DASK STABLE with HELM ..."
helm repo update

sleep 3

helm install --name ${DASKCluserName} stable/dask >> /tmp/helm-dask-install.out

sleep 3

helm_name=`cat /tmp/helm-dask-install.out | grep "NAME:" | awk '{print $2}'`
jupyter_svc=""
scheduler_svc=""
jupyter_deploy=""
scheduler_deploy=""
worker_deploy=""

echo "Helm name: ${helm_name}"

####################################
#get service and deployment names
####################################

echo "Get K8s DASK services and deployments names ..."

#get SVCs
for _ in {1..120};
do
    jupyter_svc=`kubectl get svc | grep jupy | grep "${helm_name}" | awk '{print $1}'`
    if [[ -n "${jupyter_svc}" ]];
    then
        echo "Jupyter SVC: ${jupyter_svc}"
        break
    else
        echo "Waiting for Jupyter SVC ..."
        sleep 10
        continue
    fi
done

for _ in {1..120};
do
    scheduler_svc=`kubectl get svc | grep sche | grep "${helm_name}" | awk '{print $1}'`
    if [[ -n "${scheduler_svc}" ]];
    then
        echo "Scheduler SVC: ${scheduler_svc}"
        break
    else
        echo "Waiting for Scheduler SVC ..."
        sleep 10
        continue
    fi
done


#get workers
for _ in {1..120};
do
    jupyter_deploy=`kubectl get deploy | grep jupy | grep "${helm_name}" | awk '{print $1}'`
    if [[ -n "${jupyter_deploy}" ]];
    then
        echo "Jupyter deploy: ${jupyter_deploy}"
        break
    else
        echo "Waiting for Jupyter deploy ..."
        sleep 10
        continue
    fi
done

for _ in {1..120};
do
    scheduler_deploy=`kubectl get deploy | grep sche | grep "${helm_name}" | awk '{print $1}'`
    if [[ -n "${scheduler_deploy}" ]];
    then
        echo "Scheduler deploy: ${scheduler_deploy}"
        break
    else
        echo "Waiting for Scheduler deploy ..."
        sleep 10
        continue
    fi
done

for _ in {1..120};
do
    worker_deploy=`kubectl get deploy | grep work | grep "${helm_name}" | awk '{print $1}'`
    if [[ -n "${worker_deploy}" ]];
    then
        echo "Worker deploy: ${worker_deploy}"
        break
    else
        echo "Waiting for Worker deploy ..."
        sleep 10
        continue
    fi
done


####################################
#SETUP Jupyter password
####################################
echo "Setup new Jupyter password in Dask configmap ..."
JUPY_PASSWD=`./modify-jupyter-passwd.py ${DASKJupyterPassword}`
NEW_PASSWD="c.NotebookApp.password = '${JUPY_PASSWD}'"

echo "New password hash: ${NEW_PASSWD}"

#modify confligmap
kubectl get configmap ${DASKCluserName}-jupyter-config --export -o yaml > configmap.yaml
sed -i "s/c.NotebookApp.password.*/${NEW_PASSWD}/" configmap.yaml
kubectl replace -f configmap.yaml --force

sleep 5


####################################
#Modify Jupyter LB to ingress only
####################################
echo "Modify Jupyter SVC deployment to ingress only..."
kubectl get svc ${jupyter_svc} -o yaml --export > "${jupyter_svc}.yml"

./modify-jupyter-scheduler-ingress.py "${jupyter_svc}.yml" "${jupyter_svc}.MOD.yml"
kubectl replace -f "${jupyter_svc}.MOD.yml" --force

sleep 5

####################################
#Modify Scheduler LB to ingress only
####################################
echo "Modify Scheduler SVC deployment to ingress only..."
kubectl get svc ${scheduler_svc} -o yaml --export > "${scheduler_svc}.yml"

./modify-jupyter-scheduler-ingress.py "${scheduler_svc}.yml" "${scheduler_svc}.MOD.yml"
kubectl replace -f "${scheduler_svc}.MOD.yml" --force

sleep 5

####################################
#CREATE new notebook config CM json
####################################

kubectl create -f jupyter-nbconfig-cm.yml

####################################
#modify worker deployment
####################################
echo "Modify DASK Worker deployment to use AWS S3FS and user custom Image ..."
kubectl get deploy ${worker_deploy} -o yaml --export > "${worker_deploy}.yml"
./modify-worker-img.py "${worker_deploy}.yml" "${DASKCustomWorkerDockerImage}" "${AWSRegion}" "${worker_deploy}.MOD.yml" "${Ec2K8sNodeCapacityMin}" "${DASKExtraCondaPackages_NO_WHITESPACE}" "${DASKExtraPipPackages_NO_WHITESPACE}"
kubectl replace -f "${worker_deploy}.MOD.yml" --force

sleep 5

####################################
#modify scheduler deployment
####################################
echo "Modify DASK Scheduler deployment to use AWS S3FS via S3FS and user custom Image ..."
kubectl get deploy ${scheduler_deploy} -o yaml --export > "${scheduler_deploy}.yml"
./modify-worker-img.py "${scheduler_deploy}.yml" "${DASKCustomWorkerDockerImage}" "${AWSRegion}" "${scheduler_deploy}.MOD.yml" "1"
kubectl replace -f "${scheduler_deploy}.MOD.yml" --force

sleep 5


####################################
#modify jupyter deployment
####################################
echo "Modify DASK Jupyter deployment to use AWS S3FS and use custom Image ..."
kubectl get deploy ${jupyter_deploy} -o yaml --export > "${jupyter_deploy}.yml"
./modify-jupyter-img.py "${jupyter_deploy}.yml" "${DASKCustomJupyterDockerImage}" "${AWSRegion}" "${jupyter_deploy}.MOD.yml" "${DASKExtraCondaPackages_NO_WHITESPACE}" "${DASKExtraPipPackages_NO_WHITESPACE}"
kubectl replace -f "${jupyter_deploy}.MOD.yml" --force


sleep 5

## check if all pods are running well
for _ in {1..120};
do
    daskstatus=`kubectl get pods --all-namespaces | grep "ContainerCreating"`
    if [[ -n ${daskstatus} ]];
    then
        echo "Waiting for DASK UP ALL CONTAINERS ...";
        sleep 10;
        continue;
    else
        echo "DASK IS UP!"
        break;
    fi
done

sleep 10

####################################
#setup horizontal autoscaling for workers
####################################

for rs in `kubectl get rs  -o wide | grep worker | awk '{print $1}'`;do 
    echo "Horizontal autoscaling for $rs ...";
    kubectl autoscale rs ${rs} --min=${Ec2K8sNodeCapacityMin} --max=${Ec2K8sNodeCapacityMax} --cpu-percent=90 
done

####################################
#fix elb subnet registrations bug
####################################
echo "fix elb subnet registrations bug ..."
./fix-public-elb-subnets-registrations.sh ${AWSRegion}


####################################
#extract information
####################################

for _ in {1..90};
do
    Jupyter_LB_DNS=`kubectl get svc -o wide | grep ${jupyter_svc} | awk '{print $4}'`
    if [[ -n ${Jupyter_LB_DNS} ]];
    then
        break;
    else
        echo "Wait for Jupyter_LB_DNS .. ${Jupyter_LB_DNS}"
        sleep 3
        continue;
    fi
done

for _ in {1..90};
do
    Scheduler_LB_DNS=`kubectl get svc -o wide | grep ${scheduler_svc} | awk '{print $4}'`
    if [[ -n ${Scheduler_LB_DNS} ]];
    then
        break;
    else
        echo "Wait for Scheduler_LB_DNS .. ${Scheduler_LB_DNS}"
        sleep 3
        continue;
    fi
done

echo "Jupyter_LB_DNS: ${Jupyter_LB_DNS}"
echo "Scheduler_LB_DNS: ${Scheduler_LB_DNS}"


cat <<'EOF' >> dask-connection.txt
########################
# DASK Jupyter Lab URL
########################

Jupyter Lab URL: http://__Jupyter_URL__

Jupyter Lab login password: __DASKJupyterPassword__

########################
# DASK Scheduler URL
########################

DASK scheduler URL: http://__Scheduler_URL__

EOF

sed -i 's/__Jupyter_URL__/'${Jupyter_LB_DNS}'/g' dask-connection.txt
sed -i 's/__DASKJupyterPassword__/'${DASKJupyterPassword}'/g' dask-connection.txt
sed -i 's/__Scheduler_URL__/'${Scheduler_LB_DNS}'/g' dask-connection.txt

zip --password ${DASKJupyterPassword} dask-connection.zip dask-connection.txt

aws s3 cp dask-connection.zip s3://${LambdaGenerateKubernetesStateS3Bucket}/dask-secrets/ --region ${AWSRegion}

####################################
#notify SNS when finished
####################################
if [[ -n ${DASKFinishedSetupSNSArn} ]];
then
    ./notify-sns.py ${AWSRegion} "${DASKFinishedSetupSNSArn}" "${AWSStackName}" "${DASKJupyterPassword}" "${Jupyter_URL}" "${Scheduler_URL}"
fi

echo "DASK-INIT DONE. EXIT 0"
echo "#################"
exit 0
