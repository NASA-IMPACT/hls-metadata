import os
import boto3
import datetime
import update_credentials

from metadata_creator import Metadata

"""
This is essentially a wrapper function for the metadata_creator class.
Here we access establish the product_id and the object path for accessing
the data files to pass into Metadata method.

We also assume the gcc role to access the data buckets and reset the
credentials and the s3 resource every 15 minutes. Note that the script
ignores the hdr file and only accesses the hdf files in the data bucket.
"""

bucket_name = "hls-global"
product_id = "L30"
folder = "data"
path = "/".join([product_id, folder, ""])

creds = update_credentials.assume_role(
    "arn:aws:iam::611670965994:role/gcc-S3Test", "brian_test"
)

s3 = boto3.resource(
    "s3",
    aws_access_key_id=creds["AccessKeyId"],
    aws_secret_access_key=creds["SecretAccessKey"],
    aws_session_token=creds["SessionToken"],
)
bucket = s3.Bucket(bucket_name)

reset_credentials = True
count = 0

for obj in bucket.objects.filter(Prefix=path):
    if datetime.datetime.now().minute % 15 == 0 and reset_credentials is True:
        creds = update_credentials.assume_role(
            "arn:aws:iam::611670965994:role/gcc-S3Test", "brian_test"
        )
        s3 = boto3.resource(
            "s3",
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"],
        )
        reset_credentials = False
        print("Successfully updated the credentials:\n", creds)
    elif datetime.datetime.now().minute % 15 == 0:
        reset_credentials = False
    else:
        reset_credentials = True

    file_name = obj.key.split("/")[-1]
    if file_name.endswith("hdf") and not os.path.exists(
        "output/" + product_id + "/" + file_name.replace("hdf", "cmr.xml")
    ):
        bucket.download_file(obj.key, file_name)
        result = Metadata(file_name, obj).extract_and_store()
        count += 1
        print(count, ": ", file_name, " - ", result)
        os.remove(file_name)
    elif file_name.endswith("hdf"):
        count += 1
    else:
        pass
