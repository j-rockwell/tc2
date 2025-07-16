import os
from pathlib import Path
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    mongo_uri: str = Field(default="mongodb://0.0.0.0:27017", env="MONGO_URI")
    mongo_db_name: str = Field(default="tc2", env="MONGO_DB_NAME")
    
    redis_uri: str = Field(default="redis://0.0.0.0:6379", env="MONGO_URI")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")
    
    access_token_secret: str = Field(default="accesstoken123", env="ACCESS_TOKEN_SECRET")
    refresh_token_secret: str = Field(default="refreshtoken123", env="REFRESH_TOKEN_SECRET")
    access_token_ttl_minutes: int = Field(default=30, env="ACCESS_TOKEN_TTL_MINUTES")
    refresh_token_ttl_minutes: int = Field(default=1440, env="REFRESH_TOKEN_TTL_MINUTES")
    
    environment: str = Field(default="dev", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    class Config:
        env_file = Path(__file__).parent / ".env"
        case_sensitive = False
        
    def is_prod(self) -> bool:
        return self.environment.lower() == "prod"

settings = Settings()