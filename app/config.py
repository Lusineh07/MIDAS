# app/config.py
# -----------------------------
# Purpose:
#   Handles configuration for the app.
#   Loads environment variables (like FINNHUB_API_KEY)
#   from the .env file using Pydantic Settings.

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    # env names accepted: CORS_ORIGINS (preferred) or cors_origin (alias)
    CORS_ORIGINS: str = Field(
        default="",
        validation_alias="cors_origin",  
    )
    #API  key form .env
    FINNHUB_API_KEY: str | None = None
    #Property to convert CORS_ORIGINS string into python list
    @property
    def origins(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    #tell Pydantic to load variable from .env
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore", 
    )
#Create a global setting objects so rest of app can import it
settings = Settings()
