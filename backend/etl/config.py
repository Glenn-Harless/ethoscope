from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CollectorConfig(BaseModel):
    """Configuration for data collectors"""

    alchemy_api_key: str
    alchemy_api_url: Optional[str]
    collection_interval: int = Field(
        default=15, description="Collection interval in seconds"
    )
    batch_size: int = Field(default=100, description="Batch size for processing")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    retry_delay: int = Field(default=5, description="Delay between retries in seconds")


class DatabaseConfig(BaseModel):
    """Database configuration"""

    url: str
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max overflow connections")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")


class RedisConfig(BaseModel):
    """Redis configuration"""

    url: str
    decode_responses: bool = Field(
        default=True, description="Decode responses to strings"
    )
    max_connections: int = Field(default=50, description="Maximum connections")


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # API Keys
    alchemy_api_key: str = Field(..., env="ALCHEMY_API_KEY")
    alchemy_api_url: str = Field(..., env="ALCHEMY_API_URL")
    dune_api_key: Optional[str] = Field(None, env="DUNE_API_KEY")
    flashbots_api_key: Optional[str] = Field(None, env="FLASHBOTS_API_KEY")

    # Database
    database_url: str = Field(
        default="postgresql://ethoscope:ethoscope_password@localhost:5432/ethoscope",
        env="DATABASE_URL",
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")

    # Application
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Nested configs
    @property
    def collector(self) -> CollectorConfig:
        return CollectorConfig(
            alchemy_api_key=self.alchemy_api_key,
            alchemy_api_url=self.alchemy_api_url,
        )

    @property
    def database(self) -> DatabaseConfig:
        return DatabaseConfig(
            url=self.database_url,
        )

    @property
    def redis(self) -> RedisConfig:
        return RedisConfig(
            url=self.redis_url,
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",  # Allow extra fields from .env
    )


# Create global settings instance
settings = Settings()

# For backwards compatibility
config = settings
