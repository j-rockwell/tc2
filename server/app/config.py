import os
from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    mongo_uri: str = "mongodb://0.0.0.0:55001"
    mongo_db_name: str = "tc2"
    
    access_token_secret: str = "accesstoken123"
    refresh_token_secret: str = "refreshtoken123"
    access_token_ttl_minutes: int = 30
    refresh_token_ttl_minutes: int = 1440
    
    environment: str = "dev"
    debug: bool = False
    
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        validate_assignment = False
        
    def is_prod(self) -> bool:
        return self.environment.lower() == "prod"

settings = Settings()