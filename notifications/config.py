from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    rabbitmq_url: str = "amqp://microshop:microshop@localhost:5672/"


settings = Settings()
