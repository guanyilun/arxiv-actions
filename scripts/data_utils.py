import os
import logging
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


class B2Resource:
    def __init__(self):
        endpoint = os.getenv("ENDPOINT")
        key_id = os.getenv("KEY_ID")
        application_key = os.getenv("APPLICATION_KEY")
        self.bucket_name = os.getenv("BUCKET_NAME")
        self.b2 = boto3.resource(
            service_name='s3',
            endpoint_url=endpoint,
            aws_access_key_id=key_id,
            aws_secret_access_key=application_key,
            config=Config(signature_version='s3v4')
        )

    def upload(self, local_path, remote_path):
        try:
            self.b2.Bucket(self.bucket_name).upload_file(local_path, remote_path)
        except ClientError as ce:
            logging.error(ce)

    def download(self, remote_path, local_path):
        try:
            self.b2.Bucket(self.bucket_name).download_file(remote_path, local_path)
        except ClientError as ce:
            logging.error(ce)