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
s2Tile = "T60WVC"

buckets = {"sample": "hls-global",
    "debug": "hls-debug-output"
}

bucket_name = buckets[file_type]

paths = {"sample": ["S30/data/HLS.S30." + s2Tile],
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

ignore_list = [
"HLS.S30.T06XWR.2020097T234129.v1.5.hdf",
"HLS.S30.T10XER.2020097T220049.v1.5.hdf",
"HLS.S30.T11XML.2020097T220049.v1.5.hdf",
"HLS.S30.T11XNL.2020098T213039.v1.5.hdf",
"HLS.S30.T12XVR.2020098T213039.v1.5.hdf",
"HLS.S30.T12XWR.2020097T211031.v1.5.hdf",
"HLS.S30.T12XWR.2020098T213039.v1.5.hdf",
"HLS.S30.T13XDL.2020097T211031.v1.5.hdf",
"HLS.S30.T14XNR.2020097T201929.v1.5.hdf",
"HLS.S30.T15XVL.2020097T201929.v1.5.hdf",
"HLS.S30.T16XER.2020097T192911.v1.5.hdf",
"HLS.S30.T17XML.2020097T192911.v1.5.hdf",
"HLS.S30.T18XWR.2020097T183919.v1.5.hdf",
"HLS.S30.T19XDL.2020097T183919.v1.5.hdf",
"HLS.S30.T20XNR.2020098T180909.v1.5.hdf",
"HLS.S30.T21XVL.2020098T180909.v1.5.hdf",
"HLS.S30.T22XER.2020098T171851.v1.5.hdf",
"HLS.S30.T23XML.2020098T171851.v1.5.hdf",
"HLS.S30.T24XWR.2020098T162829.v1.5.hdf",
"HLS.S30.T25XDL.2020098T162829.v1.5.hdf",
"HLS.S30.T26XNR.2020098T153901.v1.5.hdf",
"HLS.S30.T27XVL.2020098T153901.v1.5.hdf",
"HLS.S30.T29XML.2020098T144749.v1.5.hdf",
"HLS.S30.T30XWR.2020098T135731.v1.5.hdf",
"HLS.S30.T31XDL.2020098T135731.v1.5.hdf",
"HLS.S30.T31XEL.2020098T135731.v1.5.hdf",
"HLS.S30.T33XVL.2020098T130709.v1.5.hdf",
"HLS.S30.T33XWL.2020098T130709.v1.5.hdf",
"HLS.S30.T35XML.2020098T121651.v1.5.hdf",
"HLS.S30.T35XNL.2020098T121651.v1.5.hdf",
"HLS.S30.T37XDL.2020098T112629.v1.5.hdf",
"HLS.S30.T38XMR.2020098T112629.v1.5.hdf",
"HLS.S30.T39XWL.2020098T103621.v1.5.hdf",
"HLS.S30.T40XDR.2020098T103621.v1.5.hdf",
"HLS.S30.T41XNL.2020098T094549.v1.5.hdf",
"HLS.S30.T43XEL.2020098T085551.v1.5.hdf",
"HLS.S30.T44XMR.2020098T085551.v1.5.hdf",
"HLS.S30.T45XWL.2020098T080609.v1.5.hdf",
"HLS.S30.T46XDR.2020098T080609.v1.5.hdf",
]

examples = ["HLS.S30.T14VPP.2020098T180909.v1.5.hdf",
#        "HLS.S30.T19VCH.2020098T162829.v1.5.hdf",
#        "HLS.S30.T46VCL.2020098T053641.v1.5.hdf",
#        "HLS.S30.T49QEV.2020098T030539.v1.5.hdf",
#        "HLS.S30.T52TGP.2020098T021601.v1.5.hdf",
#        "HLS.S30.T26ENU.2020098T111711.v1.5.hdf",
#        "HLS.S30.T33XUE.2020098T121651.v1.5.hdf",
]
path = ""
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
        if file_name.endswith(".v1.5.hdf") and file_name not in ignore_list:
            bucket.download_file(obj.key, file_name)
            result = Metadata(file_name).save_to_S3()
            count += 1
            print(count, ": ", file_name, " - ", result)
            os.remove(file_name)
        else:
            pass

if __name__ == "__main__":
    run_metadata()
