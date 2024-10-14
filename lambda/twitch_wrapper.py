from datetime import datetime
from enum import Enum
import logging
import requests
import time

import pandas as pd

AUTH_ENDPOINT = "https://id.twitch.tv/oauth2/token"
STREAM_ENDPOINT = "https://api.twitch.tv/helix/streams"

BACKOFF_INTERVAL_SECONDS = 5
BACKOFF_MAX_SECONDS = 30


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"

"""
A wrapper class for interacting with the Twitch API

Parameters:
-----------
twitch_credentials : dict
    Dictionary containing the client id and client secret to use the Twitch api.

logger : logging.Logger
    A logger instance.
"""
class TwitchWrapper:
    def __init__(self, twitch_credentials: dict, logger: logging.Logger):
        self._logger = logger
        self._twitch_credentials = twitch_credentials
        self._session = requests.Session()
        self._headers = self._get_twitch_authorization_headers()

    def __del__(self):
        self._session.close()

    """
    Get the latest stream data from Twitch. See the Twitch api for details
    https://dev.twitch.tv/docs/api/reference/#get-streams
    Returns a dataframe.
    """
    def get_current_streams(self) -> pd.DataFrame:
        stream_params = {"first": 100}
        live_streams = pd.DataFrame()
        try:
            while True:
                stream_data = self._handle_api_call_with_backoff(
                    STREAM_ENDPOINT, HttpMethod.GET, params=stream_params
                )

                if not stream_data.get("data"):
                    break

                # Log the first stream of each batch to measure progress.
                stream_info = stream_data.get("data")[0]
                viewers = stream_info.get("viewer_count")
                title = stream_info.get("title")
                self._logger.info(f"Title: {title}, Viewers: {viewers}")

                df = pd.DataFrame(stream_data["data"])
                live_streams = pd.concat([live_streams, df], ignore_index=True)

                cursor = stream_data.get("pagination").get("cursor")
                if cursor:
                    stream_params["after"] = cursor
                else:
                    break

        except Exception as e:
            self._logger.error(
                "Error getting stream info Exception: %s", e, exc_info=True
            )
            raise

        return live_streams

    def _get_twitch_authorization_headers(self) -> dict:
        self._logger.debug("Getting twitch OAuth token")

        try:
            if (
                "client_id" not in self._twitch_credentials
                or "client_secret" not in self._twitch_credentials
            ):
                raise KeyError("Twitch Credentials missing")

            client_id = self._twitch_credentials["client_id"]
            client_secret = self._twitch_credentials["client_secret"]

            auth_params = {
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            }

            auth_data = self._handle_api_call_with_backoff(
                AUTH_ENDPOINT, HttpMethod.POST, params=auth_params
            )

            if "access_token" not in auth_data:
                raise KeyError("Twitch Access Token missing")

            return {
                "Client-ID": client_id,
                "Authorization": f'Bearer {auth_data["access_token"]}',
            }

        except requests.exceptions.RequestException as e:
            self._logger.error(
                "Error encountered getting auth token, exiting", e, exc_info=True
            )
            raise e

    def _handle_api_call_with_backoff(
        self, url: str, type: HttpMethod, params: dict = None
    ) -> dict:
        currentBackoff = 0

        while currentBackoff <= BACKOFF_MAX_SECONDS:
            try:
                if type == HttpMethod.GET:
                    response = self._session.get(
                        url, headers=self._headers, params=params
                    )
                elif type == HttpMethod.POST:
                    response = self._session.post(url, params=params)
                else:
                    break

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                self._logger.error(
                    "Error encountered for app id, skipping: %s", e, exc_info=True
                )
                currentBackoff += BACKOFF_INTERVAL_SECONDS
                time.sleep(currentBackoff)

        raise TimeoutError("%s hit max backoff", url)

    def _print_api_limit_info(self, response: dict, logger: logging.Logger):
        rate_limit = response.headers.get("Ratelimit-Limit")
        rate_remaining = response.headers.get("Ratelimit-Remaining")
        rate_reset = response.headers.get("Ratelimit-Reset")
        rate_reset_time = datetime.fromtimestamp(int(rate_reset))

        self._logger.debug("Rate limit stats")
        self._logger.debug(rate_limit)
        self._logger.debug(rate_remaining)
        self._logger.debug(rate_reset_time)