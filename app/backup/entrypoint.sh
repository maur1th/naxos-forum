#!/bin/sh -ex

pg_dumpall -h db -p 5432 -U postgres > db.out
yarn add --no-cache \
    aws-cli \
    xz
tar cvJf db-backup-$(date -I'seconds').tar.xz db.out
aws s3 cp db-backup-*.tar.xz s3://$S3_BUCKET/db-backup
