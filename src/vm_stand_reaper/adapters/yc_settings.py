import json
import logging
from enum import StrEnum, auto
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from vm_stand_reaper.adapters.environment_variables import EnvironmentVariableName

logger = logging.getLogger(__name__)


class ValidationErrorType(StrEnum):
    MISSING = auto()
    STRING_TOO_SHORT = auto()
    STRING_TOO_LONG = auto()
    STRING_PATTERN_MISMATCH = auto()
    VALUE_ERROR = auto()
    LITERAL_ERROR = auto()
    EXTRA_FORBIDDEN = auto()


class YCAuthorizationKeyKeyAlgorithm(StrEnum):
    ALGORITHM_UNSPECIFIED = "ALGORITHM_UNSPECIFIED"
    RSA_2048 = "RSA_2048"
    RSA_4096 = "RSA_4096"


class YCAuthorizationKey(BaseModel):
    """A class to represent the structure of a Yandex Cloud authorization key file.

    Additional information about Yandex Cloud authorization key
        https://yandex.cloud/en/docs/iam/concepts/authorization/key

    Attributes:
        id (str): ID of the Key resource
        service_account_id (str): ID of the service account that the Key resource belongs to
        created_at (str): Creation timestamp
        description (str, optional): Description of the Key resource
        key_algorithm (str): An algorithm used to generate a key pair of the Key resource
        public_key (str): A public key of the Key resource
        private_key (str): A private key of the Key resource
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=20, description="ID of the Key resource")
    service_account_id: str = Field(
        ...,
        min_length=20,
        description="ID of the service account that the Key resource belongs to",
    )
    created_at: str = Field(
        ...,
        min_length=20,
        max_length=30,
        description="Creation timestamp. String in RFC3339 text format",
    )
    description: Optional[str] = Field(
        None,
        min_length=0,
        max_length=256,
        description="Description of the Key resource",
    )
    key_algorithm: Literal[
        YCAuthorizationKeyKeyAlgorithm.ALGORITHM_UNSPECIFIED,
        YCAuthorizationKeyKeyAlgorithm.RSA_2048,
        YCAuthorizationKeyKeyAlgorithm.RSA_4096,
    ] = Field(
        ..., description="An algorithm used to generate a key pair of the Key resource"
    )
    public_key: str = Field(
        ..., min_length=400, description="A public key of the Key resource"
    )
    private_key: str = Field(
        ..., min_length=400, description="A private key of the Key resource"
    )


class YCEnvironmentSettings(BaseSettings):
    """A class to represent settings from environment variables.

    Attributes:
        yandex_service_account_key_json_path (str, optional): Path
            to the service account key JSON file
        yandex_oauth_token (str, optional): Yandex Cloud authorization token
        yandex_cloud_id (str): ID of the cloud
        yandex_folder_id (str): ID of the folder in cloud
    """

    model_config = SettingsConfigDict(
        env_file=(".env.local", ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    yandex_service_account_key_json_path: Optional[str] = Field(
        None,
        min_length=1,
        title=f"{EnvironmentVariableName.YANDEX_SERVICE_ACCOUNT_KEY_JSON_PATH}",
        description="Path to the service account key JSON file",
    )
    yandex_oauth_token: Optional[str] = Field(
        None,
        min_length=50,
        title=f"{EnvironmentVariableName.YANDEX_OAUTH_TOKEN}",
        description="Yandex Cloud authorization token",
        pattern=r"^[a-zA-Z0-9-_]+$",
    )
    yandex_cloud_id: Optional[str] = Field(
        ...,
        min_length=20,
        title=f"{EnvironmentVariableName.YANDEX_CLOUD_ID}",
        description="ID of the cloud",
        pattern=r"^[a-zA-Z0-9]+$",
    )
    yandex_folder_id: Optional[str] = Field(
        ...,
        min_length=20,
        title=f"{EnvironmentVariableName.YANDEX_FOLDER_ID}",
        description="ID of the folder in cloud",
        pattern=r"^[a-zA-Z0-9]+$",
    )

    @model_validator(mode="after")
    def validate_at_least_one_auth_method(self):
        if not any(
            [self.yandex_oauth_token, self.yandex_service_account_key_json_path]
        ):
            raise ValueError(
                "At least one environment variable must be specified for authentication: "
                f"'{EnvironmentVariableName.YANDEX_SERVICE_ACCOUNT_KEY_JSON_PATH}' or "
                f"'{EnvironmentVariableName.YANDEX_OAUTH_TOKEN}'"
            )
        return self


class YCSettings:
    """A class to represent settings for Yandex Cloud connection.

    Methods:
        get_settings(): Get settings from the environment variables
    """

    @staticmethod
    def get_settings() -> YCEnvironmentSettings:
        """Get settings from the environment variables.

        Returns:
            YCEnvironmentSettings object

        Raises:
            ValueError: If environment variable validation fails
        """
        try:
            settings = YCEnvironmentSettings()  # type: ignore
        except ValidationError as exc:
            if exc.errors()[0]["type"] in [
                ValidationErrorType.MISSING,
                ValidationErrorType.STRING_TOO_SHORT,
                ValidationErrorType.STRING_PATTERN_MISMATCH,
            ]:
                raise ValueError(
                    "Validation error for environment variable "
                    f"{(repr(exc.errors()[0]['loc'][0])).upper()}. {exc.errors()[0]['msg']}"
                )
            elif exc.errors()[0]["type"] == ValidationErrorType.VALUE_ERROR:
                raise ValueError(f"{exc.errors()[0]['msg']}")
            else:
                logger.exception(
                    "Unexpected Yandex Cloud settings validation error: %s", exc
                )
                raise
        except Exception as exc:
            logger.exception("Unexpected Yandex Cloud settings error: %s", exc)
            raise
        settings_key_json_path = settings.yandex_service_account_key_json_path
        if settings_key_json_path:
            env_var_name = EnvironmentVariableName.YANDEX_SERVICE_ACCOUNT_KEY_JSON_PATH
            error_message_prefix = f"Incorrect value in '{env_var_name}' variable."
            try:
                with open(settings_key_json_path, encoding="utf-8") as key_file:
                    json_data = json.load(key_file)
                    YCAuthorizationKey(**json_data)
            except FileNotFoundError:
                raise ValueError(
                    f"{error_message_prefix} No such file '{settings_key_json_path}'"
                )
            except json.JSONDecodeError:
                raise ValueError(
                    f"{error_message_prefix} The file "
                    f"'{settings_key_json_path}' has an invalid JSON format"
                )
            except ValidationError as exc:
                if exc.errors()[0]["type"] in [
                    ValidationErrorType.MISSING,
                    ValidationErrorType.STRING_TOO_SHORT,
                    ValidationErrorType.STRING_TOO_LONG,
                    ValidationErrorType.STRING_PATTERN_MISMATCH,
                    ValidationErrorType.LITERAL_ERROR,
                    ValidationErrorType.EXTRA_FORBIDDEN,
                ]:
                    error_message_prefix = f"{error_message_prefix} "
                    raise ValueError(
                        f"{error_message_prefix} The file "
                        f"'{settings_key_json_path}' has a JSON validation error: "
                        f"{(repr(exc.errors()[0]['loc'][0]))}. {exc.errors()[0]['msg']}"
                    )
                else:
                    logger.exception(
                        "Unexpected Yandex Cloud service account key validation error: %s",
                        exc,
                    )
                    raise
            except Exception as exc:
                logger.exception(
                    "Unexpected Yandex Cloud service account key settings error: %s",
                    exc,
                )
                raise
        return settings
