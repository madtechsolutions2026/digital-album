"""
Unit tests for configuration management.

Tests the Settings class validation, environment variable loading,
and default value handling.
"""

import pytest
from pydantic import ValidationError
from backend.app.config import Settings


class TestSettingsValidation:
    """Test configuration validation rules."""
    
    def test_database_url_required(self):
        """Test that DATABASE_URL is required."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(_env_file=None, DATABASE_URL="")
        
        errors = exc_info.value.errors()
        assert any("DATABASE_URL" in str(error) for error in errors)
    
    def test_database_url_must_have_protocol(self):
        """Test that DATABASE_URL must contain protocol."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                _env_file=None,
                DATABASE_URL="invalid_url_without_protocol"
            )
        
        errors = exc_info.value.errors()
        assert any("protocol" in str(error).lower() for error in errors)
    
    def test_valid_database_url_accepted(self):
        """Test that valid DATABASE_URL is accepted."""
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/testdb"
        )
        assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/testdb"
    
    def test_log_level_validation(self):
        """Test that LOG_LEVEL must be valid."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                _env_file=None,
                DATABASE_URL="postgresql+asyncpg://localhost/db",
                LOG_LEVEL="INVALID"
            )
        
        errors = exc_info.value.errors()
        assert any("LOG_LEVEL" in str(error) for error in errors)
    
    def test_valid_log_levels_accepted(self):
        """Test that all valid log levels are accepted."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in valid_levels:
            settings = Settings(
                _env_file=None,
                DATABASE_URL="postgresql+asyncpg://localhost/db",
                LOG_LEVEL=level
            )
            assert settings.LOG_LEVEL == level
    
    def test_log_level_case_insensitive(self):
        """Test that LOG_LEVEL is converted to uppercase."""
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://localhost/db",
            LOG_LEVEL="info"
        )
        assert settings.LOG_LEVEL == "INFO"
    
    def test_max_file_size_must_be_positive(self):
        """Test that MAX_FILE_SIZE must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                _env_file=None,
                DATABASE_URL="postgresql+asyncpg://localhost/db",
                MAX_FILE_SIZE=0
            )
        
        errors = exc_info.value.errors()
        assert any("MAX_FILE_SIZE" in str(error) for error in errors)
    
    def test_max_dimension_must_be_positive(self):
        """Test that MAX_DIMENSION must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                _env_file=None,
                DATABASE_URL="postgresql+asyncpg://localhost/db",
                MAX_DIMENSION=-1
            )
        
        errors = exc_info.value.errors()
        assert any("MAX_DIMENSION" in str(error) for error in errors)
    
    def test_resize_threshold_must_be_positive(self):
        """Test that RESIZE_THRESHOLD must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                _env_file=None,
                DATABASE_URL="postgresql+asyncpg://localhost/db",
                RESIZE_THRESHOLD=0
            )
        
        errors = exc_info.value.errors()
        assert any("RESIZE_THRESHOLD" in str(error) for error in errors)


class TestDefaultValues:
    """Test configuration default values."""
    
    def test_default_storage_path(self):
        """Test default STORAGE_PATH value."""
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://localhost/db"
        )
        assert settings.STORAGE_PATH == "./storage"
    
    def test_default_max_file_size(self):
        """Test default MAX_FILE_SIZE is 10MB."""
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://localhost/db"
        )
        assert settings.MAX_FILE_SIZE == 10 * 1024 * 1024
    
    def test_default_max_dimension(self):
        """Test default MAX_DIMENSION is 8000."""
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://localhost/db"
        )
        assert settings.MAX_DIMENSION == 8000
    
    def test_default_resize_threshold(self):
        """Test default RESIZE_THRESHOLD is 2048."""
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://localhost/db"
        )
        assert settings.RESIZE_THRESHOLD == 2048
    
    def test_default_cors_origins(self):
        """Test default CORS_ORIGINS."""
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://localhost/db"
        )
        assert settings.CORS_ORIGINS == ["http://localhost:3000"]
    
    def test_default_log_level(self):
        """Test default LOG_LEVEL is INFO."""
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://localhost/db"
        )
        assert settings.LOG_LEVEL == "INFO"
    
    def test_default_debug_mode(self):
        """Test default DEBUG is False."""
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://localhost/db"
        )
        assert settings.DEBUG is False


class TestCORSOriginsParsing:
    """Test CORS_ORIGINS parsing from different formats."""
    
    def test_cors_origins_as_list(self):
        """Test CORS_ORIGINS passed as list."""
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://localhost/db",
            CORS_ORIGINS=["http://localhost:3000", "https://example.com"]
        )
        assert settings.CORS_ORIGINS == ["http://localhost:3000", "https://example.com"]
    
    def test_cors_origins_as_comma_separated_string(self):
        """Test CORS_ORIGINS passed as comma-separated string."""
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://localhost/db",
            CORS_ORIGINS="http://localhost:3000,https://example.com"
        )
        assert settings.CORS_ORIGINS == ["http://localhost:3000", "https://example.com"]
    
    def test_cors_origins_with_whitespace(self):
        """Test CORS_ORIGINS with whitespace in string."""
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://localhost/db",
            CORS_ORIGINS="http://localhost:3000, https://example.com , https://test.com"
        )
        assert settings.CORS_ORIGINS == [
            "http://localhost:3000",
            "https://example.com",
            "https://test.com"
        ]
    
    def test_cors_origins_empty_string(self):
        """Test CORS_ORIGINS as empty string."""
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://localhost/db",
            CORS_ORIGINS=""
        )
        assert settings.CORS_ORIGINS == []


class TestSettingsOverrides:
    """Test that environment variables can override defaults."""
    
    def test_override_storage_path(self):
        """Test overriding STORAGE_PATH."""
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://localhost/db",
            STORAGE_PATH="/custom/path"
        )
        assert settings.STORAGE_PATH == "/custom/path"
    
    def test_override_max_file_size(self):
        """Test overriding MAX_FILE_SIZE."""
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://localhost/db",
            MAX_FILE_SIZE=5242880  # 5MB
        )
        assert settings.MAX_FILE_SIZE == 5242880
    
    def test_override_debug_mode(self):
        """Test overriding DEBUG."""
        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://localhost/db",
            DEBUG=True
        )
        assert settings.DEBUG is True
