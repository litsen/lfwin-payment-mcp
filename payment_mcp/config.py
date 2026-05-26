from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PaymentSettings(BaseSettings):
    api_base_url: str = "https://api2.lfwin.com"
    api_key: str = Field(min_length=1)
    sign_key: str = Field(min_length=1)
    sign_type: str = "MD5"
    request_timeout_seconds: float = 15

    model_config = SettingsConfigDict(env_prefix="PAYMENT_", env_file=".env", extra="ignore")


def load_settings() -> PaymentSettings:
    return PaymentSettings()
