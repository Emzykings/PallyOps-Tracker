# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Configuration Settings
# ============================================

"""
Application configuration using Pydantic Settings.
Loads values from environment variables with validation.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Pydantic automatically reads from .env file and validates types.
    """
    
    # --- Application Settings ---
    app_name: str = Field(
        default="Pricepally Operations Tracker",
        description="Application name"
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    debug: bool = Field(
        default=False,
        description="Debug mode flag"
    )
    
    # --- Server Settings ---
    host: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    port: int = Field(
        default=8000,
        description="Server port"
    )
    
    # --- Database Settings ---
    database_url: str = Field(
        ...,  # Required field
        description="PostgreSQL connection string"
    )
    
    # --- JWT Settings ---
    jwt_secret_key: str = Field(
        ...,  # Required field
        description="Secret key for JWT encoding"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT encoding algorithm"
    )
    jwt_expiration_hours: int = Field(
        default=24,
        description="JWT token expiration in hours"
    )
    
    # --- Timezone Settings ---
    timezone: str = Field(
        default="Africa/Lagos",
        description="Application timezone (WAT)"
    )
    
    # --- CORS Settings ---
    frontend_url: str = Field(
        default="http://localhost:3000",
        description="Frontend URL for CORS"
    )
    
    # --- Rate Limiting ---
    rate_limit_per_minute: int = Field(
        default=60,
        description="API rate limit per minute"
    )
    
    @property
    def cors_origins(self) -> List[str]:
        """
        Returns list of allowed CORS origins.
        """
        origins = [self.frontend_url]
        
        # In debug mode, allow localhost variations
        if self.debug:
            origins.extend([
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:8000",
            ])
        
        return origins
    
    class Config:
        """Pydantic configuration."""
        
        # Load from .env file
        env_file = ".env"
        env_file_encoding = "utf-8"
        
        # Case-insensitive environment variables
        case_sensitive = False
        
        # Extra fields handling
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using lru_cache ensures settings are loaded only once
    and reused across the application.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Create a global settings instance for easy access
settings = get_settings()