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

logger = logging.getLogger("doc-spawner.auth.aws_sso")


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
    AWS SSO authentication manager using aws-vault.
    
    Uses aws-vault exec to get temporary credentials for Bedrock access.
    """
    
    def __init__(
        self,
        profile: str = "sso-dev03-admin",
        region: str = "us-east-1",
        token_cache: Optional[TokenCache] = None,
    ):
        """
        Initialize AWS SSO auth.
        
        Args:
            profile: AWS profile name (default: sso-dev03-admin)
            region: AWS region for Bedrock
            token_cache: Token cache instance
        """
        self.profile = profile
        self.region = region
        self.cache = token_cache or TokenCache()
        self._credentials: Optional[AWSCredentials] = None
    
    async def get_credentials(
        self,
        force_refresh: bool = False,
    ) -> Optional[AWSCredentials]:
        """
        Get valid AWS credentials via aws-vault.
        
        Args:
            force_refresh: Force credential refresh
            
        Returns:
            AWSCredentials if available
        """
        # Check cached credentials
        if self._credentials and not self._credentials.is_expired() and not force_refresh:
            return self._credentials
        
        # Check if we're already inside an aws-vault session
        env_creds = self._get_credentials_from_env()
        if env_creds and not force_refresh:
            self._credentials = env_creds
            logger.info("Using AWS credentials from environment (aws-vault session)")
            return self._credentials
        
        # Get fresh credentials via aws-vault
        return await self._get_credentials_aws_vault()
    
    def _get_credentials_from_env(self) -> Optional[AWSCredentials]:
        """Check for AWS credentials in environment variables."""
        access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        session_token = os.environ.get("AWS_SESSION_TOKEN", "")
        
        if access_key and secret_key:
            # Default expiration - assume 1 hour from now
            expiration = datetime.utcnow() + timedelta(hours=1)
            
            return AWSCredentials(
                access_key_id=access_key,
                secret_access_key=secret_key,
                session_token=session_token,
                expiration=expiration,
                region=self.region,
            )
        
        return None
    
    async def _get_credentials_aws_vault(self) -> Optional[AWSCredentials]:
        """Get credentials using aws-vault exec."""
        try:
            logger.info(f"Getting AWS credentials via aws-vault for profile: {self.profile}")
            
            # Use aws-vault exec to get environment with credentials
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ["aws-vault", "exec", self.profile, "--", "env"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
            )
            
            if result.returncode != 0:
                logger.error(f"aws-vault exec failed: {result.stderr}")
                logger.info("You may need to run: aws-vault login " + self.profile)
                return None
            
            # Parse environment variables from output
            env_vars = {}
            for line in result.stdout.split('\n'):
                if '=' in line:
                    key, _, value = line.partition('=')
                    env_vars[key] = value
            
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
                
                logger.info(f"Got AWS credentials via aws-vault for profile {self.profile}")
                return self._credentials
            
            logger.error("No credentials found in aws-vault output")
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
    
    def get_bedrock_client_kwargs(self) -> dict[str, Any]:
        """
        Get kwargs for creating a Bedrock client.
        
        Returns:
            Dict with credentials for anthropic Bedrock client
        """
        if not self._credentials or self._credentials.is_expired():
            raise RuntimeError("No valid AWS credentials. Call get_credentials() first.")
        
        return {
            "aws_access_key": self._credentials.access_key_id,
            "aws_secret_key": self._credentials.secret_access_key,
            "aws_session_token": self._credentials.session_token,
            "aws_region": self._credentials.region,
        }
