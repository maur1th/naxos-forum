# pipenv run python3 xmas_switch.py

import boto3

client = boto3.client('s3')

bucket      = "geekattitude"
xmas_dir    = "static/img/xmas/smileys/"
regular_dir = "static/img/smileys/"
backup_dir  = "static/img/backup/"
xmas_marker = regular_dir + "xmas-on"

def list_s3_objects(bucket, prefix):
    res = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return [o["Key"] for o in res['Contents']]

def get_filename(s3_object):
    return s3_object.split('/')[-1]

def object_exists(bucket, s3_object):
    res = client.list_objects_v2(Bucket=bucket, Prefix=s3_object)
    return res['KeyCount'] > 0

regular_smileys = map(get_filename, list_s3_objects(bucket, regular_dir))
xmas_smileys = list(map(get_filename, list_s3_objects(bucket, xmas_dir)))

xmas_enabled = object_exists(bucket, xmas_marker)
if xmas_enabled:
    print("XMAS marker detected ☃️")
    for smiley in filter(lambda s: s in xmas_smileys, regular_smileys):
        print(f"Replace {smiley} with backup 🌿")
        client.copy_object(
            ACL='public-read',
            Bucket=bucket,
            CopySource=f"{bucket}/{backup_dir}{smiley}",
            Key=regular_dir + smiley)
    print("Remove XMAS marker ☀️")
    client.delete_object(
        Bucket=bucket,
        Key=xmas_marker)
else:
    print("Enabling XMAS smileys")
    for smiley in filter(lambda s: s in xmas_smileys, regular_smileys):
        print(f"Copying {smiley} to {backup_dir}")
        client.copy_object(
            Bucket=bucket,
            CopySource=f"{bucket}/{regular_dir}{smiley}",
            Key=backup_dir + smiley)
        print(f"Replace {smiley} with xmas version 🎄")
        client.copy_object(
            ACL='public-read',
            Bucket=bucket,
            CopySource=f"{bucket}/{xmas_dir}{smiley}",
            Key=regular_dir + smiley)
    print("Add XMAS marker ☃️")
    client.put_object(
        ACL='private',
        Bucket=bucket,
        Key=xmas_marker)
