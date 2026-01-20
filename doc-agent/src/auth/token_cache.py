"""Token caching with secure storage and automatic expiry handling."""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict
import hashlib
import base64

logger = logging.getLogger("doc-agent.auth.token_cache")

# Try to import cryptography for encryption, fall back to base64 obfuscation
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    logger.warning("cryptography not installed - tokens will be obfuscated but not encrypted")


@dataclass
class CachedToken:
    """A cached token with metadata."""
    token: str
    token_type: str  # access_token, refresh_token, sso_token
    service: str  # github, confluence, jira, aws
    expires_at: Optional[str] = None  # ISO format
    refresh_token: Optional[str] = None
    scopes: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None
    
    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Check if token is expired (with buffer for safety)."""
        if not self.expires_at:
            return False
        
        try:
            expires = datetime.fromisoformat(self.expires_at)
            return datetime.utcnow() >= (expires - timedelta(seconds=buffer_seconds))
        except ValueError:
            return True
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CachedToken":
        """Create from dictionary."""
        return cls(**data)


class TokenCache:
    """
    Secure token cache with persistence.
    
    Stores OAuth tokens and other credentials with:
    - Encryption at rest (if cryptography is available)
    - Automatic expiry tracking
    - Service-specific namespacing
    """
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        encryption_key: Optional[str] = None,
    ):
        """
        Initialize the token cache.
        
        Args:
            cache_dir: Directory for token storage (default: ~/.doc-agent/tokens)
            encryption_key: Key for encryption (default: derived from machine ID)
        """
        self.cache_dir = cache_dir or Path.home() / ".doc-agent" / "tokens"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Set restrictive permissions on cache directory
        try:
            os.chmod(self.cache_dir, 0o700)
        except OSError:
            pass
        
        self._cache_file = self.cache_dir / "tokens.json"
        self._tokens: dict[str, CachedToken] = {}
        
        # Initialize encryption
        self._fernet: Optional[Any] = None
        if HAS_CRYPTO:
            self._init_encryption(encryption_key)
        
        # Load existing tokens
        self._load()
    
    def _init_encryption(self, key: Optional[str]) -> None:
        """Initialize Fernet encryption."""
        if not HAS_CRYPTO:
            return
        
        # Derive key from provided key or machine identifier
        if key:
            key_material = key.encode()
        else:
            # Use a combination of factors for machine-specific key
            machine_id = self._get_machine_id()
            key_material = machine_id.encode()
        
        # Derive a proper Fernet key using PBKDF2
        salt = b"doc-agent-token-cache-v1"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key_material))
        self._fernet = Fernet(derived_key)
    
    def _get_machine_id(self) -> str:
        """Get a machine-specific identifier."""
        # Try various sources for a stable machine ID
        sources = []
        
        # Username
        sources.append(os.environ.get("USER", os.environ.get("USERNAME", "")))
        
        # Home directory
        sources.append(str(Path.home()))
        
        # Hostname
        import socket
        sources.append(socket.gethostname())
        
        # Combine and hash
        combined = ":".join(sources)
        return hashlib.sha256(combined.encode()).hexdigest()[:32]
    
    def _encrypt(self, data: str) -> str:
        """Encrypt data."""
        if self._fernet:
            return self._fernet.encrypt(data.encode()).decode()
        # Fallback to base64 (not secure, just obfuscation)
        return base64.b64encode(data.encode()).decode()
    
    def _decrypt(self, data: str) -> str:
        """Decrypt data."""
        if self._fernet:
            return self._fernet.decrypt(data.encode()).decode()
        # Fallback from base64
        return base64.b64decode(data.encode()).decode()
    
    def _load(self) -> None:
        """Load tokens from cache file."""
        if not self._cache_file.exists():
            return
        
        try:
            with open(self._cache_file, "r") as f:
                encrypted_data = f.read()
            
            if not encrypted_data.strip():
                return
            
            decrypted = self._decrypt(encrypted_data)
            data = json.loads(decrypted)
            
            self._tokens = {
                key: CachedToken.from_dict(value)
                for key, value in data.items()
            }
            
            logger.debug(f"Loaded {len(self._tokens)} cached tokens")
            
        except Exception as e:
            logger.warning(f"Failed to load token cache: {e}")
            self._tokens = {}
    
    def _save(self) -> None:
        """Save tokens to cache file."""
        try:
            data = {
                key: token.to_dict()
                for key, token in self._tokens.items()
            }
            
            json_data = json.dumps(data, indent=2)
            encrypted = self._encrypt(json_data)
            
            with open(self._cache_file, "w") as f:
                f.write(encrypted)
            
            # Set restrictive permissions on cache file
            os.chmod(self._cache_file, 0o600)
            
        except Exception as e:
            logger.error(f"Failed to save token cache: {e}")
    
    def _make_key(self, service: str, token_type: str, identifier: str = "default") -> str:
        """Create a cache key."""
        return f"{service}:{token_type}:{identifier}"
    
    def get(
        self,
        service: str,
        token_type: str = "access_token",
        identifier: str = "default",
    ) -> Optional[CachedToken]:
        """
        Get a cached token.
        
        Args:
            service: Service name (github, confluence, jira, aws)
            token_type: Type of token
            identifier: Optional identifier for multiple accounts
            
        Returns:
            CachedToken if found and not expired, None otherwise
        """
        key = self._make_key(service, token_type, identifier)
        token = self._tokens.get(key)
        
        if token and not token.is_expired():
            return token
        
        return None
    
    def set(
        self,
        service: str,
        token: str,
        token_type: str = "access_token",
        identifier: str = "default",
        expires_at: Optional[datetime] = None,
        expires_in: Optional[int] = None,
        refresh_token: Optional[str] = None,
        scopes: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> CachedToken:
        """
        Cache a token.
        
        Args:
            service: Service name
            token: The token value
            token_type: Type of token
            identifier: Optional identifier
            expires_at: Expiration datetime
            expires_in: Seconds until expiration (alternative to expires_at)
            refresh_token: Optional refresh token
            scopes: OAuth scopes
            metadata: Additional metadata
            
        Returns:
            The cached token object
        """
        # Calculate expiration
        if expires_at:
            exp_str = expires_at.isoformat()
        elif expires_in:
            exp_str = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
        else:
            exp_str = None
        
        cached = CachedToken(
            token=token,
            token_type=token_type,
            service=service,
            expires_at=exp_str,
            refresh_token=refresh_token,
            scopes=scopes,
            metadata=metadata,
        )
        
        key = self._make_key(service, token_type, identifier)
        self._tokens[key] = cached
        self._save()
        
        logger.debug(f"Cached {token_type} for {service}")
        return cached
    
    def delete(
        self,
        service: str,
        token_type: str = "access_token",
        identifier: str = "default",
    ) -> bool:
        """Delete a cached token."""
        key = self._make_key(service, token_type, identifier)
        if key in self._tokens:
            del self._tokens[key]
            self._save()
            return True
        return False
    
    def clear_service(self, service: str) -> int:
        """Clear all tokens for a service."""
        keys_to_delete = [k for k in self._tokens if k.startswith(f"{service}:")]
        for key in keys_to_delete:
            del self._tokens[key]
        
        if keys_to_delete:
            self._save()
        
        return len(keys_to_delete)
    
    def clear_all(self) -> None:
        """Clear all cached tokens."""
        self._tokens.clear()
        self._save()
    
    def list_tokens(self) -> list[dict[str, Any]]:
        """List all cached tokens (without exposing actual token values)."""
        return [
            {
                "service": t.service,
                "token_type": t.token_type,
                "expires_at": t.expires_at,
                "is_expired": t.is_expired(),
                "has_refresh_token": t.refresh_token is not None,
                "scopes": t.scopes,
            }
            for t in self._tokens.values()
        ]
