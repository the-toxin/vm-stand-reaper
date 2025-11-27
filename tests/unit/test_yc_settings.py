import json
import os
from enum import StrEnum

import pytest

from vm_stand_reaper.adapters.environment_variables import EnvironmentVariableName
from vm_stand_reaper.adapters.yc_settings import (
    YCAuthorizationKey,
    YCAuthorizationKeyKeyAlgorithm,
    YCEnvironmentSettings,
    YCSettings,
)


def clear_environ():
    for env_var in EnvironmentVariableName:
        if os.environ.get(env_var, None):
            os.environ.pop(env_var, None)


class ValidEnvironmentSettingsData(StrEnum):
    KEY_PATH = "key_path"
    IAM_TOKEN = "t1.7euelSbPyceKx87JqpuRl1qZiY-Ryi3rnpWaksrKaZqUppnLncmDnpeajZvl8_dZNAFl-e8ENXMH_t3z9xljfmT57wQ1cwf-.-LErty1vRh4S__VEp-aDnM5huB5MEfm_Iu1u2IzNgyrn0emiWDYA6rSQXDvzjE0O3HBbUlqoDeCmXYYInzZ6Cg"
    OAUTH_TOKEN = "y0_ttttttttttttTTTTTTTTTT000ttttttttttttTTTTTTTTTT"
    CLOUD_ID = "ccccCCCC0000ccccCCCC"
    FOLDER_ID = "ffffFFFF0000ffffFFFF"


class TestYCSettings:
    """YCSettings class tests"""

    def test_get_verified_settings_for_auth_token_authorization_in_cloud(self):
        environment_variables = {
            "YANDEX_OAUTH_TOKEN": ValidEnvironmentSettingsData.OAUTH_TOKEN,
            "YANDEX_CLOUD_ID": ValidEnvironmentSettingsData.CLOUD_ID,
            "YANDEX_FOLDER_ID": ValidEnvironmentSettingsData.FOLDER_ID,
        }
        os.environ.update(environment_variables)
        settings = YCSettings.get_settings()
        clear_environ()
        assert (
            settings.yandex_oauth_token == environment_variables["YANDEX_OAUTH_TOKEN"]
        )
        assert settings.yandex_cloud_id == environment_variables["YANDEX_CLOUD_ID"]
        assert settings.yandex_folder_id == environment_variables["YANDEX_FOLDER_ID"]

    def test_invalid_file_in_key_path_raises_error(self):
        environment_variables = {
            "YANDEX_SERVICE_ACCOUNT_KEY_JSON_PATH": "fail.json",
            "YANDEX_OAUTH_TOKEN": ValidEnvironmentSettingsData.OAUTH_TOKEN,
            "YANDEX_CLOUD_ID": ValidEnvironmentSettingsData.CLOUD_ID,
            "YANDEX_FOLDER_ID": ValidEnvironmentSettingsData.FOLDER_ID,
        }
        os.environ.update(environment_variables)
        with pytest.raises(ValueError, match="No such file"):
            YCSettings.get_settings()


class TestYCEnvironmentSettings:
    """YCEnvironmentSettings class tests"""

    def test_valid_environment_variables_values(self):
        env_settings = YCEnvironmentSettings(
            yandex_service_account_key_json_path=ValidEnvironmentSettingsData.KEY_PATH,
            yandex_iam_token=ValidEnvironmentSettingsData.IAM_TOKEN,
            yandex_oauth_token=ValidEnvironmentSettingsData.OAUTH_TOKEN,
            yandex_cloud_id=ValidEnvironmentSettingsData.CLOUD_ID,
            yandex_folder_id=ValidEnvironmentSettingsData.FOLDER_ID,
        )
        assert (
            env_settings.yandex_service_account_key_json_path
            == ValidEnvironmentSettingsData.KEY_PATH
        )
        assert (
            env_settings.yandex_oauth_token == ValidEnvironmentSettingsData.OAUTH_TOKEN
        )
        assert env_settings.yandex_cloud_id == ValidEnvironmentSettingsData.CLOUD_ID
        assert env_settings.yandex_folder_id == ValidEnvironmentSettingsData.FOLDER_ID

    def test_invalid_key_path_format_raises_error(self):
        with pytest.raises(ValueError):
            YCEnvironmentSettings(
                yandex_service_account_key_json_path="",
                yandex_iam_token=None,
                yandex_oauth_token=None,
                yandex_cloud_id=ValidEnvironmentSettingsData.CLOUD_ID,
                yandex_folder_id=ValidEnvironmentSettingsData.FOLDER_ID,
            )

    @pytest.mark.parametrize(
        "iam_token", [f"?{ValidEnvironmentSettingsData.IAM_TOKEN}", ""]
    )
    def test_invalid_iam_token_format_raises_error(self, iam_token):
        with pytest.raises(ValueError):
            YCEnvironmentSettings(
                yandex_service_account_key_json_path=ValidEnvironmentSettingsData.KEY_PATH,
                yandex_iam_token=iam_token,
                yandex_oauth_token=ValidEnvironmentSettingsData.OAUTH_TOKEN,
                yandex_cloud_id=ValidEnvironmentSettingsData.CLOUD_ID,
                yandex_folder_id=ValidEnvironmentSettingsData.FOLDER_ID,
            )

    @pytest.mark.parametrize(
        "oauth_token", [f"?{ValidEnvironmentSettingsData.OAUTH_TOKEN}", ""]
    )
    def test_invalid_oauth_token_format_raises_error(self, oauth_token):
        with pytest.raises(ValueError):
            YCEnvironmentSettings(
                yandex_service_account_key_json_path=ValidEnvironmentSettingsData.KEY_PATH,
                yandex_iam_token=ValidEnvironmentSettingsData.IAM_TOKEN,
                yandex_oauth_token=oauth_token,
                yandex_cloud_id=ValidEnvironmentSettingsData.CLOUD_ID,
                yandex_folder_id=ValidEnvironmentSettingsData.FOLDER_ID,
            )

    @pytest.mark.parametrize(
        "cloud_id", [f"?{ValidEnvironmentSettingsData.CLOUD_ID}", ""]
    )
    def test_invalid_cloud_id_format_raises_error(self, cloud_id):
        with pytest.raises(ValueError):
            YCEnvironmentSettings(
                yandex_service_account_key_json_path=ValidEnvironmentSettingsData.KEY_PATH,
                yandex_iam_token=ValidEnvironmentSettingsData.IAM_TOKEN,
                yandex_oauth_token=ValidEnvironmentSettingsData.OAUTH_TOKEN,
                yandex_cloud_id=cloud_id,
                yandex_folder_id=ValidEnvironmentSettingsData.FOLDER_ID,
            )

    @pytest.mark.parametrize(
        "folder_id", [f"?{ValidEnvironmentSettingsData.FOLDER_ID}", ""]
    )
    def test_invalid_folder_id_format_raises_error(self, folder_id):
        with pytest.raises(ValueError):
            YCEnvironmentSettings(
                yandex_service_account_key_json_path=ValidEnvironmentSettingsData.KEY_PATH,
                yandex_iam_token=ValidEnvironmentSettingsData.IAM_TOKEN,
                yandex_oauth_token=ValidEnvironmentSettingsData.OAUTH_TOKEN,
                yandex_cloud_id=ValidEnvironmentSettingsData.CLOUD_ID,
                yandex_folder_id=folder_id,
            )

    @pytest.mark.parametrize("max_active_operations", [-1, 0, "e"])
    def test_invalid_max_active_operations_format_raises_error(
        self, max_active_operations
    ):
        with pytest.raises(ValueError):
            YCEnvironmentSettings(
                yandex_service_account_key_json_path=ValidEnvironmentSettingsData.KEY_PATH,
                yandex_iam_token=ValidEnvironmentSettingsData.IAM_TOKEN,
                yandex_oauth_token=ValidEnvironmentSettingsData.OAUTH_TOKEN,
                yandex_cloud_id=ValidEnvironmentSettingsData.CLOUD_ID,
                yandex_folder_id=ValidEnvironmentSettingsData.FOLDER_ID,
                yandex_max_active_operations=max_active_operations,
            )

    def test_empty_token_and_key_path_raises_error(self):
        with pytest.raises(
            ValueError,
            match="At least one environment variable must be specified",
        ):
            YCEnvironmentSettings(
                yandex_service_account_key_json_path=None,
                yandex_iam_token=None,
                yandex_oauth_token=None,
                yandex_cloud_id=ValidEnvironmentSettingsData.CLOUD_ID,
                yandex_folder_id=ValidEnvironmentSettingsData.FOLDER_ID,
            )


class TestYCAuthorizationKey:
    """YCAuthorizationKey class tests"""

    @staticmethod
    def get_json_data_from_authorization_key(
        id="id_000000000000000001",
        service_account_id="sa_id_00000000000001",
        created_at="2025-01-01T01:01:01.000000001Z",
        description="Test description",
        key_algorithm="RSA_2048",
        public_key="-----BEGIN PUBLIC KEY-----\npublic_key+public_key+public_key+"
        "public_key+public_key+public_key+public_key+public_key+public_key+"
        "public_key+public_key+public_key+public_key+public_key+public_key+"
        "public_key+public_key+public_key+public_key+public_key+public_key+"
        "public_key+public_key+public_key+public_key+public_key+public_key+"
        "public_key+public_key+public_key+public_key+public_key+public_key"
        "+++++++++++",
        private_key="PLEASE DO NOT REMOVE THIS LINE! Yandex.Cloud SA Key ID private_key+"
        "private_key+private_key+private_key+private_key+private_key+private_key+"
        "private_key+private_key+private_key+private_key+private_key+private_key+"
        "private_key+private_key+private_key+private_key+private_key+private_key+"
        "private_key+private_key+private_key+private_key+private_key+private_key+"
        "private_key+private_key+private_key++++++++++",
    ) -> str:
        key_file_data = {
            "id": id,
            "service_account_id": service_account_id,
            "created_at": created_at,
            "description": description,
            "key_algorithm": key_algorithm,
            "public_key": public_key,
            "private_key": private_key,
        }
        return json.dumps(key_file_data)

    def test_valid_yc_authorization_key(self):
        json_key_file_data = self.get_json_data_from_authorization_key()
        assert YCAuthorizationKey.model_validate_json(json_key_file_data)

    @pytest.mark.parametrize(
        "key_algorithm",
        [
            YCAuthorizationKeyKeyAlgorithm.ALGORITHM_UNSPECIFIED,
            YCAuthorizationKeyKeyAlgorithm.RSA_4096,
            YCAuthorizationKeyKeyAlgorithm.RSA_4096,
        ],
    )
    def test_valid_key_algorithm_value(self, key_algorithm):
        json_key_file_data = self.get_json_data_from_authorization_key(
            key_algorithm=key_algorithm
        )
        assert YCAuthorizationKey.model_validate_json(json_key_file_data)

    def test_invalid_yc_authorization_key_raises_error(self):
        json_key_file_data = json.dumps("{}")
        with pytest.raises(ValueError):
            YCAuthorizationKey.model_validate_json(json_key_file_data)

    def test_id_length_smaller_than_required_raises_error(self):
        json_key_file_data = self.get_json_data_from_authorization_key(id="")
        with pytest.raises(ValueError):
            YCAuthorizationKey.model_validate_json(json_key_file_data)

    def test_service_account_id_length_smaller_than_required_raises_error(self):
        json_key_file_data = self.get_json_data_from_authorization_key(
            service_account_id=""
        )
        with pytest.raises(ValueError):
            YCAuthorizationKey.model_validate_json(json_key_file_data)

    @pytest.mark.parametrize("created_at", ["2025-01-01T01:01:01.000000001Z?", ""])
    def test_invalid_created_at_format_raises_error(self, created_at):
        json_key_file_data = self.get_json_data_from_authorization_key(
            created_at=created_at
        )
        with pytest.raises(ValueError):
            YCAuthorizationKey.model_validate_json(json_key_file_data)

    def test_description_length_greater_than_required_raises_error(self):
        description = "d" * 257
        json_key_file_data = self.get_json_data_from_authorization_key(
            description=description
        )
        with pytest.raises(ValueError):
            YCAuthorizationKey.model_validate_json(json_key_file_data)

    def test_invalid_key_algorithm_value_raises_error(self):
        json_key_file_data = self.get_json_data_from_authorization_key(
            key_algorithm="UNKNOWN"
        )
        with pytest.raises(ValueError):
            YCAuthorizationKey.model_validate_json(json_key_file_data)
