import logging
import json
import pytest
from unittest.mock import Mock

from aws_wrapper import AwsWrapper

class TestAWSWrapper:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.logger = logging.getLogger("AWSWTest")
        self.mock_session = Mock()
        self.mock_client = Mock()
       
    def test___fail___get_credentials___raises_exception(self):
        self.mock_session.client.get_secret_value.side_effect = Exception()
        aws_wrapper = AwsWrapper(
            "region",
            self.logger,
            mock_session=self.mock_session
        )

        with pytest.raises(Exception):
            aws_wrapper.get_credentials("fake_secret")

    def test___secret___get_credentials___returns_secret(self):
        secret_response = {
            "SecretString": json.dumps({"id": "testSecret"})
        }
        self.mock_session.client.return_value = self.mock_client
        self.mock_client.get_secret_value.return_value = secret_response
        aws_wrapper = AwsWrapper(
            "region",
            self.logger,
            mock_session=self.mock_session
        )

        secret = aws_wrapper.get_credentials("fake_secret")

        self.mock_client.get_secret_value.assert_called_once_with(
            SecretId="fake_secret"
        )
        assert json.loads(secret_response["SecretString"]) == secret
