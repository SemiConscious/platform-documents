"""Token cache for storing authentication tokens."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("doc-spawner.auth.token_cache")


@dataclass
class CachedToken:
    """A cached token with metadata."""
    token: str
    token_type: str
    identifier: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    refresh_token: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """Check if token is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() >= (self.expires_at - timedelta(seconds=buffer_seconds))
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "token": self.token,
            "token_type": self.token_type,
            "identifier": self.identifier,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "refresh_token": self.refresh_token,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CachedToken":
        """Create from dictionary."""
        return cls(
            token=data["token"],
            token_type=data["token_type"],
            identifier=data["identifier"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            refresh_token=data.get("refresh_token"),
            metadata=data.get("metadata", {}),
        )


class TokenCache:
    """
    Simple file-based token cache.
    
    Stores tokens in a JSON file in the user's home directory.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the token cache.
        
        Args:
            cache_dir: Directory for cache files (default: ~/.doc-spawner/cache)
        """
        self.cache_dir = cache_dir or (Path.home() / ".doc-spawner" / "cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, dict[str, CachedToken]] = {}
        self._load_cache()
    
    def _get_cache_file(self, service: str) -> Path:
        """Get cache file path for a service."""
        return self.cache_dir / f"{service}_tokens.json"
    
    def _load_cache(self) -> None:
        """Load all cached tokens from files."""
        for cache_file in self.cache_dir.glob("*_tokens.json"):
            service = cache_file.stem.replace("_tokens", "")
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                
                self._cache[service] = {}
                for key, token_data in data.items():
                    try:
                        self._cache[service][key] = CachedToken.from_dict(token_data)
                    except Exception as e:
                        logger.warning(f"Failed to load cached token {key}: {e}")
                        
            except Exception as e:
                logger.warning(f"Failed to load cache file {cache_file}: {e}")
    
    def _save_cache(self, service: str) -> None:
        """Save cache for a service to file."""
        if service not in self._cache:
            return
        
        cache_file = self._get_cache_file(service)
        data = {
            key: token.to_dict()
            for key, token in self._cache[service].items()
        }
        
        with open(cache_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def get(
        self,
        service: str,
        token_type: str,
        identifier: str,
    ) -> Optional[CachedToken]:
        """
        Get a cached token.
        
        Args:
            service: Service name (e.g., "aws", "mcp")
            token_type: Type of token (e.g., "access_token", "sso_credentials")
            identifier: Unique identifier (e.g., profile name, client_id)
            
        Returns:
            CachedToken if found, None otherwise
        """
        key = f"{token_type}:{identifier}"
        if service in self._cache and key in self._cache[service]:
            return self._cache[service][key]
        return None
    
    def set(
        self,
        service: str,
        token: str,
        token_type: str,
        identifier: str,
        expires_in: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        refresh_token: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Cache a token.
        
        Args:
            service: Service name
            token: The token value
            token_type: Type of token
            identifier: Unique identifier
            expires_in: Seconds until expiration
            expires_at: Explicit expiration time
            refresh_token: Optional refresh token
            metadata: Additional metadata
        """
        if service not in self._cache:
            self._cache[service] = {}
        
        if expires_at is None and expires_in is not None:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        key = f"{token_type}:{identifier}"
        self._cache[service][key] = CachedToken(
            token=token,
            token_type=token_type,
            identifier=identifier,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            refresh_token=refresh_token,
            metadata=metadata or {},
        )
        
        self._save_cache(service)
    
    def delete(self, service: str, token_type: str, identifier: str) -> None:
        """Delete a cached token."""
        key = f"{token_type}:{identifier}"
        if service in self._cache and key in self._cache[service]:
            del self._cache[service][key]
            self._save_cache(service)
    
    def clear(self, service: Optional[str] = None) -> None:
        """Clear cached tokens."""
        if service:
            self._cache[service] = {}
            cache_file = self._get_cache_file(service)
            if cache_file.exists():
                cache_file.unlink()
        else:
            self._cache = {}
            for cache_file in self.cache_dir.glob("*_tokens.json"):
                cache_file.unlink()
