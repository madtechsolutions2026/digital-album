"""
Configuration management using Pydantic Settings.

This module defines the application configuration loaded from environment variables
and validated using Pydantic. It supports loading from .env files via python-dotenv.
"""

from typing import List, Union
from pydantic import Field, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be configured via environment variables or .env file.
    Required settings will raise validation errors if not provided.
    """
    
    # Database configuration
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL database URL with asyncpg driver (e.g., postgresql+asyncpg://user:pass@host:port/db)"
    )
    
    # File storage configuration
    STORAGE_PATH: str = Field(
        default="./storage",
        description="Base directory path for storing uploaded images (local mode only)"
    )
    
    STORAGE_TYPE: str = Field(
        default="local",
        description="Storage type: 'local' or 'r2'"
    )
    
    # Cloudflare R2 configuration
    R2_ACCOUNT_ID: str = Field(
        default="",
        description="Cloudflare R2 account ID"
    )
    
    R2_ACCESS_KEY_ID: str = Field(
        default="",
        description="Cloudflare R2 access key ID"
    )
    
    R2_SECRET_ACCESS_KEY: str = Field(
        default="",
        description="Cloudflare R2 secret access key"
    )
    
    R2_BUCKET_NAME: str = Field(
        default="",
        description="Cloudflare R2 bucket name"
    )
    
    R2_PUBLIC_URL: str = Field(
        default="",
        description="Cloudflare R2 public URL (optional custom domain)"
    )
    
    # Image validation limits
    MAX_FILE_SIZE: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum allowed file size in bytes"
    )
    
    MAX_DIMENSION: int = Field(
        default=8000,
        description="Maximum allowed image dimension (width or height) in pixels"
    )
    
    RESIZE_THRESHOLD: int = Field(
        default=2048,
        description="Images larger than this dimension will be resized before face detection"
    )

    MAX_CONCURRENT_UPLOADS: int = Field(
        default=8,
        description=(
            "Maximum number of photos processed (validate/compress/upload) at the "
            "same time, regardless of how many upload requests arrive concurrently. "
            "Bounds CPU and memory usage under large batch uploads; excess requests "
            "queue rather than all running at once."
        )
    )
    
    # CORS configuration
    # Using Union to accept both string and list, validator will normalize to list
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default="http://localhost:3000",
        description="Allowed CORS origins as comma-separated string or list"
    )

    # Gallery access token signing. Change this in production - the default
    # is dev-only and not a secret.
    JWT_SECRET: str = Field(
        default="dev-only-insecure-secret-change-me",
        description="Secret used to sign gallery access tokens (event code/password login)"
    )
    
    # Logging configuration
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    # Application mode
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode (verbose logging, SQLAlchemy echo)"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra environment variables
        # Don't try to parse env vars as JSON - let validators handle it
        env_parse_none_str=None
    )
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str, info: ValidationInfo) -> str:
        """
        Validate DATABASE_URL is not empty and contains required components.
        
        Args:
            v: The DATABASE_URL value
            info: Validation context
            
        Returns:
            The validated DATABASE_URL
            
        Raises:
            ValueError: If DATABASE_URL is invalid
        """
        if not v:
            raise ValueError("DATABASE_URL is required and cannot be empty")
        
        # Automatically rewrite standard postgresql scheme to use asyncpg driver (required by SQLAlchemy async engine)
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        if "://" not in v:
            raise ValueError("DATABASE_URL must be a valid database URL with protocol")
        
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str, info: ValidationInfo) -> str:
        """
        Validate LOG_LEVEL is a valid logging level.
        
        Args:
            v: The LOG_LEVEL value
            info: Validation context
            
        Returns:
            The validated LOG_LEVEL in uppercase
            
        Raises:
            ValueError: If LOG_LEVEL is not valid
        """
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        
        return v_upper
    
    @field_validator("MAX_FILE_SIZE")
    @classmethod
    def validate_max_file_size(cls, v: int, info: ValidationInfo) -> int:
        """
        Validate MAX_FILE_SIZE is positive.
        
        Args:
            v: The MAX_FILE_SIZE value
            info: Validation context
            
        Returns:
            The validated MAX_FILE_SIZE
            
        Raises:
            ValueError: If MAX_FILE_SIZE is not positive
        """
        if v <= 0:
            raise ValueError("MAX_FILE_SIZE must be a positive integer")
        
        return v
    
    @field_validator("MAX_DIMENSION")
    @classmethod
    def validate_max_dimension(cls, v: int, info: ValidationInfo) -> int:
        """
        Validate MAX_DIMENSION is positive.
        
        Args:
            v: The MAX_DIMENSION value
            info: Validation context
            
        Returns:
            The validated MAX_DIMENSION
            
        Raises:
            ValueError: If MAX_DIMENSION is not positive
        """
        if v <= 0:
            raise ValueError("MAX_DIMENSION must be a positive integer")
        
        return v
    
    @field_validator("RESIZE_THRESHOLD")
    @classmethod
    def validate_resize_threshold(cls, v: int, info: ValidationInfo) -> int:
        """
        Validate RESIZE_THRESHOLD is positive.
        
        Args:
            v: The RESIZE_THRESHOLD value
            info: Validation context
            
        Returns:
            The validated RESIZE_THRESHOLD
            
        Raises:
            ValueError: If RESIZE_THRESHOLD is not positive
        """
        if v <= 0:
            raise ValueError("RESIZE_THRESHOLD must be a positive integer")

        return v

    @field_validator("MAX_CONCURRENT_UPLOADS")
    @classmethod
    def validate_max_concurrent_uploads(cls, v: int, info: ValidationInfo) -> int:
        """
        Validate MAX_CONCURRENT_UPLOADS is positive.

        Args:
            v: The MAX_CONCURRENT_UPLOADS value
            info: Validation context

        Returns:
            The validated MAX_CONCURRENT_UPLOADS

        Raises:
            ValueError: If MAX_CONCURRENT_UPLOADS is not positive
        """
        if v <= 0:
            raise ValueError("MAX_CONCURRENT_UPLOADS must be a positive integer")

        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """
        Parse CORS_ORIGINS from string or list.
        
        Supports both list format and comma-separated string format for environment variables.
        When loading from .env file, this will receive a string and parse it into a list.
        
        Args:
            v: The CORS_ORIGINS value (list or string)
            
        Returns:
            List of origin strings
        """
        if isinstance(v, str):
            # Split comma-separated string and strip whitespace
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        else:
            return []


# Global settings instance
# This will be initialized when the module is imported
# and will raise validation errors if required environment variables are missing
def get_settings() -> Settings:
    """
    Get the application settings instance.
    
    This function creates and returns a Settings instance that loads
    configuration from environment variables and .env file.
    
    Returns:
        Settings: The application settings
        
    Raises:
        ValidationError: If required environment variables are missing or invalid
    """
    return Settings()


# For backward compatibility and convenience, create a default instance
# only if not in testing mode
try:
    settings = Settings()
except Exception:
    # If settings cannot be loaded (e.g., in test environment without .env),
    # settings will be None and should be created explicitly
    settings = None
