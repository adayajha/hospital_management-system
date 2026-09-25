from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "hospital_support"
    jwt_secret: str = "development-secret-change-me"
    access_token_expire_minutes: int = 480
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
