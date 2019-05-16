#! /bin/bash
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"
rm ./deploy.zip
cd ./s3pglambda/lib/python3.6/site-packages
zip -r9 "${parent_path}/deploy.zip" ./*
cd "$parent_path"
zip -g ./deploy.zip ./app.py
zip -g ./deploy.zip ./rds_config.py
zip -g ./deploy.zip ./sunrise.py
