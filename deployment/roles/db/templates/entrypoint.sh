#!/bin/sh -ex

export S3_BUCKET={{aws_storage_bucket_name}}
export AWS_ACCESS_KEY_ID={{aws_access_key_id}}
export AWS_SECRET_ACCESS_KEY={{aws_secret_access_key}}

pg_dumpall -h db -p 5432 -U postgres > db.out
apt-get update
apt-get install -y \
    python-pip \
    xz-utils
pip install awscli
tar cvJf db-backup-$(date -I'seconds' | tr : -).tar.xz db.out
aws s3 cp db-backup-*.tar.xz s3://$S3_BUCKET/db-backup/
