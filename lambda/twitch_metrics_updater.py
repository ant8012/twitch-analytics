from datetime import datetime
import logging
import os
import sys
from zoneinfo import ZoneInfo

from aws_wrapper import AwsWrapper
from twitch_wrapper import TwitchWrapper


"""
    Gets the latest Twitch metrics and writes them to S3 in parquet

    Parameters:
    -----------
    logger : logging.Logger
        A logger instance.

    aws_access_key_id : str, optional
        Unspecified if running the context of a lambda. If running this elsewhere such as locally
        an aws_access_key_id can be provided.

    aws_secret_access_key : str, optional
        Unspecified if running the context of a lambda. If running this elsewhere such as locally
        an aws_secret_access_key can be provided.

    aws_session : AwsWrapper, optional
        An instance of AwsWrapper. If not provided will be created.

    twitch_wrapper : TwitchWrapper, optional
        An instance of TwitchWrapper. If not provided will be created.
"""

def update_twitch_metrics(
    logger: logging.Logger,
    aws_access_key_id: str = None,
    aws_secret_access_key: str = None,
    s3_bucket_path: str = None,
    aws_session: AwsWrapper=None,
    twitch_wrapper: TwitchWrapper=None,
):
    current_time = datetime.now(ZoneInfo("America/Chicago"))

    if not aws_session:
        aws_session = AwsWrapper(
            os.getenv("AWS_REGION"),
            logger,
            aws_access_key_id,
            aws_secret_access_key
        )

    if not twitch_wrapper:
        twitch_credentials = aws_session.get_credentials(
            os.getenv("TWITCH_CREDENTIALS_NAME", "twitch-client-credentials")
        )

        twitch_wrapper = TwitchWrapper(twitch_credentials, logger)

    live_streams = twitch_wrapper.get_current_streams()
    live_streams = live_streams.rename(columns={"id": "stream_id"})
    live_streams["timestamp"] = current_time
    current_time_formatted = current_time.strftime("%Y-%m-%d_%H-%M-%S")

    if not s3_bucket_path:
        s3_bucket_path = os.getenv("S3_BUCKET_PATH")
    file_path = f'{s3_bucket_path}{str(current_time.year)}/{str(current_time.month)}/{str(current_time.day)}/{current_time_formatted}.parquet'
    aws_session.write_parquet_to_s3(live_streams, file_path, logger)


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("twitch_stream_updater")
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


"""
Entrypoint for the Lambda function. Calling this will get the current live streams from twitch.tv
and write the results to an S3 bucket.

Parameters:
-----------
event : dict
    The event data passed to the Lambda function. This typically contains 
    details about the triggering event such as the input data.

context : object
    The runtime information provided by AWS Lambda, such as function 
    metadata and execution environment details. It's an object that contains 
    information like function name, execution time, etc.

aws_access_key_id : str, optional
    Unspecified if running the context of a lambda. If running this elsewhere such as locally
    an aws_access_key_id can be provided.

aws_secret_access_key : str, optional
    Unspecified if running the context of a lambda. If running this elsewhere such as locally
    an aws_secret_access_key can be provided.

update_function : function, optional
    By default will call update_twitch_metrics to perform updates. Can be overridden
    for tests.
"""
def handle(
    event: dict,
    context: object,
    aws_access_key_id: str = None,
    aws_secret_access_key: str = None,
    update_function=update_twitch_metrics
) -> dict:
    logger = setup_logging()

    try:
        file_path = update_function(logger, aws_access_key_id, aws_secret_access_key)

        return {"statusCode": 200, "body": f"File update successful: {file_path}"}
    except Exception as e:
        logger.error("Error, exiting %s", e, exc_info=True)

        return {
            "statusCode": 500,
            "body": "Update failed, see above for error details.",
        }


if __name__ == "__main__":
    # Credentials will be set in the AWS environment. This is only used for local testing
    import dotenv

    dotenv.load_dotenv()
    handle(
        None,
        None,
        os.getenv("AWS_ACCESS_KEY_ID"),
        os.getenv("AWS_SECRET_ACCESS_KEY")
    )
