import logging
import pandas as pd
import pytest

from twitch_wrapper import TwitchWrapper, AUTH_ENDPOINT, STREAM_ENDPOINT

class TestTwitchWrapper:
    @pytest.fixture(autouse=True)
    def setup_method(self, responses):
        self.logger = logging.getLogger("TwitchWrapperTest")
        self.credentials = {
            "client_id": "1234",
            "client_secret": "ABCD"
        }
        responses.add(
            responses.POST,
            AUTH_ENDPOINT,
            json={
                "access_token": "1111"
            },
            status=200
        )
        self.twitch_wrapper = TwitchWrapper(
            self.credentials,
            self.logger
        )

    def test___missing_credentials___init___raises_exception(self):
        with pytest.raises(KeyError):
            TwitchWrapper({}, self.logger)

    def test___credentials_present___init___no_exception(self):
        TwitchWrapper(self.credentials, self.logger)
        
    def test___no_stream_data___get_current_stream___returns_no_data(self, responses):
        responses.add(
            responses.GET,
            STREAM_ENDPOINT,
            json={},
            status=200
        )

        df = self.twitch_wrapper.get_current_streams()

        assert df.empty

    def test___non_paginated_data___get_current_streams___returns_twitch_streams(self, responses):
        stream_data = [
            {
                "viewer_count": 1000,
                "title": "A random stream"  
            },
            {
                "viewer_count": 2000,
                "title": "A random stream 2"  
            }
        ]
        twitch_data = {
            "data": stream_data,
            "pagination": {}
        }
        responses.add(
            responses.GET,
            STREAM_ENDPOINT,
            json=twitch_data,
            status=200
        )

        actual_df = self.twitch_wrapper.get_current_streams()

        assert pd.DataFrame(stream_data).equals(actual_df)

    def test___paginated_data___get_current_streams___returns_twitch_streams(self, responses):
        stream_data_1 = [
            {
                "viewer_count": 1000,
                "title": "A random stream"  
            },
            {
                "viewer_count": 2000,
                "title": "A random stream 2"  
            }
        ]
        stream_data_2 = [
            {
                "viewer_count": 3000,
                "title": "A random stream 3"  
            },
            {
                "viewer_count": 4000,
                "title": "A random stream 4"  
            }
        ]
        twitch_data_1 = {
            "data": stream_data_1,
            "pagination": {
                "cursor": "1234"
            }
        }
        twitch_data_2 = {
            "data": stream_data_2,
            "pagination": {}
        }
        responses.add(
            responses.GET,
            STREAM_ENDPOINT,
            json=twitch_data_1,
            status=200
        )
        responses.add(
            responses.GET,
            STREAM_ENDPOINT,
            json=twitch_data_2,
            status=200
        )

        actual_df = self.twitch_wrapper.get_current_streams()

        assert pd.DataFrame(stream_data_1 + stream_data_2).equals(actual_df)
        # Assert the last call passed the cursor for pagination
        assert responses.calls[-1].request.params["after"] == twitch_data_1["pagination"]["cursor"]
