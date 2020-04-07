import os
import boto3
import datetime
import click
import update_credentials
import numpy as np

from metadata_creator import Metadata

"""
This is essentially a wrapper function for the metadata_creator class.
Here we access establish the product_id and the object path for accessing
the data files to pass into Metadata method.

We also assume the gcc role to access the data buckets and reset the
credentials and the s3 resource every 15 minutes. Note that the script
ignores the hdr file and only accesses the hdf files in the data bucket.
"""

file_type = "debug"
s2Tile = "T54HTD"

buckets = {"sample": "hls-global",
    "debug": "hls-debug-output"
}

bucket_name = buckets[file_type]

paths = {"sample": ["S30/data/HLS.S30.17MPP"],
    "debug": [
        "HLS.S30.T06WWA",
        "HLS.S30.T12RTS",
        "HLS.S30.T54HTD",
        "HLS.S30.T55MCP",
        "HLS.S30.T55MEP",
        "HLS.S30.T60UXF",
        "HLS.S30.T60UXG",
        "HLS.S30.T60WVC",
    ]
}

index = np.argwhere(np.char.find(np.asarray(paths[file_type]),s2Tile) >= 0)[0][0]
path = paths[file_type][index]
print(path)

creds = update_credentials.assume_role(
    "arn:aws:iam::611670965994:role/gcc-S3Test", "brian_test"
)

if file_type == "sample":
    s3 = boto3.resource(
        "s3",
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
    )
if file_type == "debug":
    s3 = boto3.resource("s3")
bucket = s3.Bucket(bucket_name)


@click.command()
def run_metadata():
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
        if file_name.endswith(".v1.5.hdf"):
            bucket.download_file(obj.key, file_name)
            result = Metadata(file_name).save_to_S3()
            count += 1
            print(count, ": ", file_name, " - ", result)
            os.remove(file_name)
        else:
            pass

if __name__ == "__main__":
    run_metadata()
