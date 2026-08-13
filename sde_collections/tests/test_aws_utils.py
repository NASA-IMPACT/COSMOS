# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_aws_utils.py

from unittest.mock import patch

from django.test import override_settings

from ..utils.aws import get_boto3_session


class TestGetBoto3Session:
    def test_default_chain_when_sde_keys_blank(self):
        """With the SDE_AWS_* keys at their blank base.py defaults, the session must use the
        default credential chain (instance role in AWS) — no explicit keys passed."""
        with patch("sde_collections.utils.aws.boto3.Session") as mock_session:
            session = get_boto3_session()

        mock_session.assert_called_once_with(region_name="us-east-1")
        assert session is mock_session.return_value

    @override_settings(SDE_AWS_ACCESS_KEY_ID="AKIATEST", SDE_AWS_SECRET_ACCESS_KEY="secret")
    def test_explicit_keys_when_set(self):
        with patch("sde_collections.utils.aws.boto3.Session") as mock_session:
            session = get_boto3_session()

        mock_session.assert_called_once_with(
            aws_access_key_id="AKIATEST",
            aws_secret_access_key="secret",
            region_name="us-east-1",
        )
        assert session is mock_session.return_value

    @override_settings(SDE_AWS_ACCESS_KEY_ID="AKIATEST", SDE_AWS_SECRET_ACCESS_KEY="")
    def test_partial_keys_fall_back_to_default_chain(self):
        """One key without the other is a misconfiguration — fall back to the default chain
        rather than passing an incomplete credential pair to boto3."""
        with patch("sde_collections.utils.aws.boto3.Session") as mock_session:
            get_boto3_session()

        mock_session.assert_called_once_with(region_name="us-east-1")

    @override_settings(AWS_REGION="us-west-2")
    def test_region_comes_from_settings(self):
        with patch("sde_collections.utils.aws.boto3.Session") as mock_session:
            get_boto3_session()

        mock_session.assert_called_once_with(region_name="us-west-2")
