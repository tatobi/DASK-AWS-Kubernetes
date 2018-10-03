#!/bin/bash

VPCIPv4CIDRBlock=${1}
VPNCACountryISOCode=${2}
VPNCAProvince=${3}
VPNCACity=${4}
VPNCAOrganization=${5}
VPNCAOrgEmail=${6}
VPNCAOrgUnit=${7}
VPNNumberOfPreGeneratedCerts=${8}
AWSCfnStackName=${9}
LambdaGenerateKubernetesStateS3Bucket=${10}
ZipPEncryptPassword=${11}
AWSRegion=${12}

echo "#################"
echo "INIT-OPENVPN START..."

echo "$@"

mv /opt/easy-openvpn/keygen /etc/openvpn/
cd /etc/openvpn/keygen
chmod +x /etc/openvpn/keygen/*

export openvpnvars="/etc/openvpn/keygen/vars"

AWSCfnStackName=`echo "${AWSCfnStackName}" | tr '[:upper:]' '[:lower:]'`

ip=`curl http://169.254.169.254/latest/meta-data/public-ipv4`
awsdns=$(echo $VPCIPv4CIDRBlock | tr "." " " | awk '{ print $1"."$2"."$3".2" }')

echo ${ip}
echo ${awsdns}

sed -i 's/CHANGE_SERVER_IP/'${ip}'/g' ${openvpnvars}
sed -i 's/CC/'${VPNCACountryISOCode}'/g' ${openvpnvars}
sed -i 's/CHANGE_PROVINCE/'${VPNCAProvince}'/g' ${openvpnvars}
sed -i 's/CHANGE_CITY/'${VPNCACity}'/g' ${openvpnvars}
sed -i 's/CHANGE_ORG/'${VPNCAOrganization}'/g' ${openvpnvars}
sed -i 's/CHANGE_ORG_EMAIL/'${VPNCAOrgEmail}'/g' ${openvpnvars}
sed -i 's/CHANGE_OU/'${VPNCAOrgUnit}'/g' ${openvpnvars}

echo "push \"route $VPCIPv4CIDRBlock 255.255.0.0\"" | tee --append server-tcp-template.conf

./create-server-tcp
service openvpn@server start
systemctl enable openvpn@server

i=1
while [[ "$i" -le "${VPNNumberOfPreGeneratedCerts}" ]];
do 
    ./build-key-embed-tcp "DASK.OVPN.${AWSCfnStackName}.${i}"; 
    cp /etc/openvpn/keys/DASK.OVPN.${AWSCfnStackName}.${i}/DASK.OVPN.${AWSCfnStackName}.${i}.ovpn /opt/openvpn-keys/; 
    i=$((i + 1))
done

cd /opt/openvpn-keys/
zip --password ${ZipPEncryptPassword} openvpn-secrets.zip *

aws s3 cp openvpn-secrets.zip s3://${LambdaGenerateKubernetesStateS3Bucket}/dask-secrets/ --region ${AWSRegion}

chown ubuntu:ubuntu /opt/openvpn-keys/*

echo "INIT-OPENVPN DONE."
echo "#################"

exit 0

