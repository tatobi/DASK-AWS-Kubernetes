#!/bin/bash

aws s3 sync ./ s3://tatobi-dask-aws-deploy/latest/ --profile=tamastobi --exclude ".git/*" --exclude "deploy-s3.sh" --delete

