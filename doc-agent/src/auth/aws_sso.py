"""AWS SSO authentication for Bedrock API access."""

import asyncio
import json
import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from .token_cache import TokenCache

logger = logging.getLogger("doc-agent.auth.aws_sso")


@dataclass
class AWSCredentials:
    """AWS credentials from SSO."""
    access_key_id: str
    secret_access_key: str
    session_token: str
    expiration: datetime
    region: str = "us-east-1"
    
    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Check if credentials are expired."""
        return datetime.utcnow() >= (self.expiration - timedelta(seconds=buffer_seconds))
    
    def to_env(self) -> dict[str, str]:
        """Convert to environment variables."""
        return {
            "AWS_ACCESS_KEY_ID": self.access_key_id,
            "AWS_SECRET_ACCESS_KEY": self.secret_access_key,
            "AWS_SESSION_TOKEN": self.session_token,
            "AWS_REGION": self.region,
            "AWS_DEFAULT_REGION": self.region,
        }


class AWSSSOAuth:
    """
    AWS SSO authentication manager.
    
    Supports:
    - AWS SSO login via aws-vault or AWS CLI
    - Token caching
    - Automatic credential refresh
    - Bedrock API access
    """
    
    def __init__(
        self,
        profile: str = "default",
        region: str = "us-east-1",
        token_cache: Optional[TokenCache] = None,
        use_aws_vault: bool = True,
    ):
        """
        Initialize AWS SSO auth.
        
        Args:
            profile: AWS profile name
            region: AWS region for Bedrock
            token_cache: Token cache instance
            use_aws_vault: Whether to use aws-vault for credential management
        """
        self.profile = profile
        self.region = region
        self.cache = token_cache or TokenCache()
        self.use_aws_vault = use_aws_vault
        
        self._credentials: Optional[AWSCredentials] = None
    
    def _get_sso_cache_dir(self) -> Path:
        """Get AWS SSO cache directory."""
        return Path.home() / ".aws" / "sso" / "cache"
    
    def _get_credentials_cache_dir(self) -> Path:
        """Get AWS CLI credentials cache directory."""
        return Path.home() / ".aws" / "cli" / "cache"
    
    async def get_credentials(
        self,
        force_refresh: bool = False,
    ) -> Optional[AWSCredentials]:
        """
        Get valid AWS credentials.
        
        Args:
            force_refresh: Force credential refresh
            
        Returns:
            AWSCredentials if available
        """
        # Check cached credentials
        if self._credentials and not self._credentials.is_expired() and not force_refresh:
            return self._credentials
        
        # Check if we're already inside an aws-vault session (env vars present)
        env_creds = self._get_credentials_from_env()
        if env_creds and not force_refresh:
            self._credentials = env_creds
            logger.info(f"Using AWS credentials from environment (aws-vault session)")
            return self._credentials
        
        # Check token cache
        cached = self.cache.get("aws", "sso_credentials", self.profile)
        if cached and not cached.is_expired() and not force_refresh:
            try:
                metadata = cached.metadata or {}
                self._credentials = AWSCredentials(
                    access_key_id=metadata.get("access_key_id", ""),
                    secret_access_key=metadata.get("secret_access_key", ""),
                    session_token=cached.token,
                    expiration=datetime.fromisoformat(cached.expires_at) if cached.expires_at else datetime.utcnow(),
                    region=self.region,
                )
                return self._credentials
            except Exception as e:
                logger.warning(f"Failed to restore cached credentials: {e}")
        
        # Get fresh credentials
        if self.use_aws_vault:
            return await self._get_credentials_aws_vault()
        else:
            return await self._get_credentials_aws_cli()
    
    def _get_credentials_from_env(self) -> Optional[AWSCredentials]:
        """Check for AWS credentials in environment variables."""
        access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        session_token = os.environ.get("AWS_SESSION_TOKEN", "")
        
        # Also check if we're in an aws-vault session
        aws_vault = os.environ.get("AWS_VAULT")
        
        if access_key and secret_key:
            # Credentials are in environment (likely aws-vault exec or similar)
            # Default expiration - assume 1 hour from now if not specified
            expiration = datetime.utcnow() + timedelta(hours=1)
            
            region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or self.region
            
            return AWSCredentials(
                access_key_id=access_key,
                secret_access_key=secret_key,
                session_token=session_token,
                expiration=expiration,
                region=region,
            )
        
        return None
    
    async def _get_credentials_aws_vault(self) -> Optional[AWSCredentials]:
        """Get credentials using aws-vault."""
        try:
            # Use aws-vault exec to get credentials
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    [
                        "aws-vault", "exec", self.profile, "--json",
                        "--", "env"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
            )
            
            if result.returncode != 0:
                # Try to initiate SSO login
                logger.info("AWS credentials not available, initiating SSO login...")
                await self._initiate_sso_login_aws_vault()
                
                # Retry
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: subprocess.run(
                        [
                            "aws-vault", "exec", self.profile, "--json",
                            "--", "env"
                        ],
                        capture_output=True,
                        text=True,
                        timeout=60,
                    )
                )
            
            if result.returncode == 0:
                # Parse environment variables from output
                env_vars = {}
                for line in result.stdout.split('\n'):
                    if '=' in line:
                        key, _, value = line.partition('=')
                        env_vars[key] = value
                
                # Also try to get JSON credentials
                creds_result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: subprocess.run(
                        [
                            "aws-vault", "exec", self.profile,
                            "--", "aws", "sts", "get-caller-identity",
                            "--output", "json"
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                )
                
                access_key = env_vars.get("AWS_ACCESS_KEY_ID", "")
                secret_key = env_vars.get("AWS_SECRET_ACCESS_KEY", "")
                session_token = env_vars.get("AWS_SESSION_TOKEN", "")
                
                if access_key and secret_key:
                    # Default expiration for aws-vault (usually 1 hour)
                    expiration = datetime.utcnow() + timedelta(hours=1)
                    
                    self._credentials = AWSCredentials(
                        access_key_id=access_key,
                        secret_access_key=secret_key,
                        session_token=session_token,
                        expiration=expiration,
                        region=self.region,
                    )
                    
                    # Cache the credentials
                    self._cache_credentials(self._credentials)
                    
                    logger.info(f"Got AWS credentials via aws-vault for profile {self.profile}")
                    return self._credentials
            
            logger.error(f"Failed to get AWS credentials: {result.stderr}")
            return None
            
        except subprocess.TimeoutExpired:
            logger.error("aws-vault command timed out")
            return None
        except FileNotFoundError:
            logger.error("aws-vault not found. Please install aws-vault.")
            return None
        except Exception as e:
            logger.error(f"Error getting AWS credentials: {e}")
            return None
    
    async def _get_credentials_aws_cli(self) -> Optional[AWSCredentials]:
        """Get credentials using AWS CLI."""
        try:
            # Check if SSO session is valid
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    [
                        "aws", "sts", "get-caller-identity",
                        "--profile", self.profile,
                        "--output", "json"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            )
            
            if result.returncode != 0:
                # Need to login
                logger.info("AWS SSO session expired, initiating login...")
                await self._initiate_sso_login_cli()
                
                # Retry
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: subprocess.run(
                        [
                            "aws", "sts", "get-caller-identity",
                            "--profile", self.profile,
                            "--output", "json"
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                )
            
            if result.returncode == 0:
                # Get credentials from cache or environment
                creds = await self._read_cli_credentials()
                if creds:
                    self._cache_credentials(creds)
                    return creds
            
            logger.error(f"Failed to get AWS credentials: {result.stderr}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting AWS credentials: {e}")
            return None
    
    async def _initiate_sso_login_aws_vault(self) -> None:
        """Initiate SSO login via aws-vault."""
        logger.info("Opening browser for AWS SSO login...")
        print(f"\nPlease complete AWS SSO login in your browser for profile: {self.profile}\n")
        
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                ["aws-vault", "login", self.profile],
                timeout=300,
            )
        )
    
    async def _initiate_sso_login_cli(self) -> None:
        """Initiate SSO login via AWS CLI."""
        logger.info("Opening browser for AWS SSO login...")
        print(f"\nPlease complete AWS SSO login in your browser for profile: {self.profile}\n")
        
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                ["aws", "sso", "login", "--profile", self.profile],
                timeout=300,
            )
        )
    
    async def _read_cli_credentials(self) -> Optional[AWSCredentials]:
        """Read credentials from AWS CLI cache."""
        cache_dir = self._get_credentials_cache_dir()
        
        if not cache_dir.exists():
            return None
        
        # Find the most recent cache file for our profile
        latest_file = None
        latest_time = None
        
        for cache_file in cache_dir.glob("*.json"):
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                
                # Check if this is for our profile
                mtime = cache_file.stat().st_mtime
                if latest_time is None or mtime > latest_time:
                    if "Credentials" in data:
                        latest_file = cache_file
                        latest_time = mtime
                        
            except Exception:
                continue
        
        if latest_file:
            try:
                with open(latest_file) as f:
                    data = json.load(f)
                
                creds_data = data["Credentials"]
                expiration = datetime.fromisoformat(
                    creds_data["Expiration"].replace("Z", "+00:00")
                ).replace(tzinfo=None)
                
                return AWSCredentials(
                    access_key_id=creds_data["AccessKeyId"],
                    secret_access_key=creds_data["SecretAccessKey"],
                    session_token=creds_data["SessionToken"],
                    expiration=expiration,
                    region=self.region,
                )
            except Exception as e:
                logger.warning(f"Failed to read CLI credentials: {e}")
        
        return None
    
    def _cache_credentials(self, credentials: AWSCredentials) -> None:
        """Cache AWS credentials."""
        self.cache.set(
            service="aws",
            token=credentials.session_token,
            token_type="sso_credentials",
            identifier=self.profile,
            expires_at=credentials.expiration,
            metadata={
                "access_key_id": credentials.access_key_id,
                "secret_access_key": credentials.secret_access_key,
                "region": credentials.region,
            },
        )
    
    def get_bedrock_client_kwargs(self) -> dict[str, Any]:
        """
        Get kwargs for creating a Bedrock client.
        
        Returns:
            Dict with credentials for boto3/anthropic Bedrock client
        """
        if not self._credentials or self._credentials.is_expired():
            raise RuntimeError("No valid AWS credentials. Call get_credentials() first.")
        
        return {
            "aws_access_key": self._credentials.access_key_id,
            "aws_secret_key": self._credentials.secret_access_key,
            "aws_session_token": self._credentials.session_token,
            "aws_region": self._credentials.region,
        }
    
    def get_env_vars(self) -> dict[str, str]:
        """
        Get environment variables for AWS credentials.
        
        Returns:
            Dict of environment variables
        """
        if not self._credentials:
            return {}
        return self._credentials.to_env()
    
    async def ensure_valid_credentials(self) -> bool:
        """
        Ensure we have valid credentials, refreshing if needed.
        
        Returns:
            True if valid credentials are available
        """
        creds = await self.get_credentials()
        return creds is not None and not creds.is_expired()
