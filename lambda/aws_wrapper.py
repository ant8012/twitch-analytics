import logging
import json

import boto3
from pandas import DataFrame
import awswrangler as wr

"""
A wrapper class for interacting with AWS

Parameters:
-----------
    region_name : str
        The AWS region to connect to.

    logger : logging.Logger
        A logger instance.

    aws_access_key_id : str, optional
        Unspecified if running the context of a lambda. If running this elsewhere such as locally
        an aws_access_key_id can be provided.

    aws_secret_access_key : str, optional
        Unspecified if running the context of a lambda. If running this elsewhere such as locally
        an aws_secret_access_key can be provided.

    mock_session
        Used by tests for dependency injection.

"""
class AwsWrapper:
    def __init__(
        self,
        region_name: str,
        logger: logging.Logger,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        mock_session=None,
    ):
        if mock_session:
            self._session = mock_session
        elif aws_access_key_id and aws_secret_access_key:
            self._session = boto3.Session(
                region_name=region_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )
        else:
            self._session = boto3.Session(region_name=region_name)
        self._logging = logger

    """
    Get a secret from AWS Secret Manager

    Parameters:
    -----------
    secret_name : str
        Name of the secret.

    logger : logging.Logger
        A logger instance.
    """
    def get_credentials(self, secret_name: str) -> dict:
        self._logging.debug("Downloading secret %s", secret_name)

        try:
            response = self._session.client("secretsmanager").get_secret_value(
                SecretId=secret_name
            )
            secret = json.loads(response["SecretString"])
            return secret
        except Exception as e:
            self._logging.error(f"Error retrieving secret, exiting: {e}")
            raise e

    """
    Write a dataframe to a parquet file in S3

    Parameters:
    -----------
    df : Dataframe
        Dataframe to export.

    s3_path : str
        S3 path to export to.

    logger : logging.Logger
        A logger instance.
    """
    def write_parquet_to_s3(self, df: DataFrame, s3_path: str, logger: logging.Logger):
        logger.debug("Writing parquet to S3")
        wr.s3.to_parquet(
            df=df, path=s3_path, compression="gzip", boto3_session=self._session
        )
