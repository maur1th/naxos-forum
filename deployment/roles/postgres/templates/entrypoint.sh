#!/bin/sh
set -ex

export S3_BUCKET={{aws_storage_bucket_name}}

pg_dumpall -h db -p 5432 -U postgres > db.out
apt-get update
apt-get install -y \
    xz-utils \
    awscli
tar cvJf db-backup-$(date -I'seconds' | tr : -).tar.xz db.out
aws s3 cp db-backup-*.tar.xz s3://$S3_BUCKET/db-backup/
