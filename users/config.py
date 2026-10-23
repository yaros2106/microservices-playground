from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str
    jwt_private_key_path: str = "keys/private.pem"
    jwt_expire_minutes: int = 30


settings = Settings()
