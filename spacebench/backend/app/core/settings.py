from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DEVELOPMENT: bool = True

    # Defaults target a backend run on the host (run_the_app_dev.bat).
    # In Docker these are overridden by the compose environment.
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "CHANGE_ME_x9pAYwXP6T5pFtBAizps"
    POSTGRES_DB: str = "spacebench"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    POD_ENGINE_URL: str = "http://localhost:8002/pod"

    UPLOAD_DIR: str = "./uploads"

    # Show all prints in the terminal
    DEBUG_MODE: bool = False

    # Use to reset DB model (/!\ THIS DROPS EVERYTHING /!\)
    RESET_DB: bool = True

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
