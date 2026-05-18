from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    nvidia_api_key: str = ""
    nvidia_nim_model: str = "meta/llama-3.3-70b-instruct"
    nvidia_nim_base_url: str = "https://integrate.api.nvidia.com/v1"
    
    ticker: str = "AAPL"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()