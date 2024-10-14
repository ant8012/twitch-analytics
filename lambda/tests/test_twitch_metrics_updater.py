import logging
import pandas as pd
import pytest
import re
from unittest.mock import Mock

from twitch_metrics_updater import handle, update_twitch_metrics

class TestTwitchMetricsUpdater:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.logger = logging.getLogger("TwitchMetricsUpdaterTest")
       
    def test___success___handle___return_ok_status(self):
        fake_updater_function = Mock()

        response = handle(
            None,
            None,
            update_function=fake_updater_function)

        assert response["statusCode"] == 200


    def test___fail___handle___return_fail_status(self):
        
        fake_updater_function = Mock()
        fake_updater_function.side_effect = Exception()

        response = handle(
            None,
            None,
            aws_access_key_id=None,
            aws_secret_access_key=None,
            update_function=fake_updater_function)

        assert response["statusCode"] == 500

    def test___twitch_streams___handle____writes_to_s3_path(self):
        fake_data = [
            ["12345", "other_data"]
        ]
        twitch_data = pd.DataFrame(fake_data, columns=["id", "other_column"])
        fake_bucket = "fakeBucket/"
        fake_aws_wrapper = Mock()
        fake_twitch_wrapper = Mock()
        fake_twitch_wrapper.get_current_streams.return_value = twitch_data
        
        update_twitch_metrics(
            self.logger,
            aws_access_key_id=None,
            aws_secret_access_key=None,
            aws_session=fake_aws_wrapper,
            s3_bucket_path=fake_bucket,
            twitch_wrapper=fake_twitch_wrapper)

        args = fake_aws_wrapper.write_parquet_to_s3.call_args
        # s3_bucket/YYYY/MM/DD/%Y-%m-%d_%H-%M-%S.parquet
        pattern = rf'^{re.escape(fake_bucket)}(\d{{4}})/(\d{{1,2}})/(\d{{1,2}})/(\d{{4}}-\d{{2}}-\d{{2}}_\d{{2}}-\d{{2}}-\d{{2}})\.parquet$'
        assert "stream_id" in args[0][0].columns
        assert "timestamp" in args[0][0].columns
        assert re.match(pattern, args[0][1])
