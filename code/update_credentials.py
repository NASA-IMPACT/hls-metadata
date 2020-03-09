import boto3
import os

def assume_role(role_arn,role_session_name):
    '''
    This method allows users to assume roles using boto3.
    Requires the role_arn and a session name. Returns
    the credentials dictionary (Note that this is not
    the default dictionary we return creds['Credentials']
    which means extracting the AWS_ACCESS_KEY_ID should be done
    simply by providing ['AccessKeyId']. AWS_SECRET_ACCESS_KEY,
    and AWS_SESSION_TOKEN are extracted similarly using
    ['SecretAccessKey'],['SessionToken'] respectively.
    '''
    client = boto3.client('sts')
    creds = client.assume_role(RoleArn=role_arn, RoleSessionName=role_session_name)
    access_key_id = creds.get('Credentials').get('AccessKeyId')
    secret_access_key = creds.get('Credentials').get('SecretAccessKey')
    session_token = creds.get('Credentials').get('SessionToken')

    return creds['Credentials']
