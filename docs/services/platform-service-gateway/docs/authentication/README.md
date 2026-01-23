# Platform Service Gateway - Authentication Guide

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/)
[![PHP Version](https://img.shields.io/badge/PHP-7.4%2B-blue)](https://php.net)
[![Framework](https://img.shields.io/badge/framework-Kohana-orange)](https://kohanaframework.org/)
[![Docker](https://img.shields.io/badge/docker-supported-blue)](https://docker.com)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platforms](https://img.shields.io/badge/platforms-6%2B-purple)]()

A unified API gateway providing seamless integration with multiple CRM and enterprise platforms including Salesforce, Microsoft Dynamics, Zendesk, SugarCRM, Oracle Fusion, and custom data sources. This comprehensive guide covers all authentication mechanisms supported by the gateway.

---

## Table of Contents

- [Authentication Overview](#authentication-overview)
- [Quick Start](#quick-start)
- [Login/Logout Flow](#loginlogout-flow)
- [Token Management](#token-management)
- [Platform Authentication Index](#platform-authentication-index)
- [Architecture Overview](#architecture-overview)
- [Configuration Reference](#configuration-reference)
- [Troubleshooting](#troubleshooting)
- [Related Documentation](#related-documentation)

---

## Authentication Overview

The Platform Service Gateway implements a multi-layered authentication system designed to securely connect with diverse enterprise platforms. The gateway supports several authentication mechanisms to accommodate the varying requirements of different CRM systems and data sources.

### Supported Authentication Methods

| Method | Description | Supported Platforms |
|--------|-------------|---------------------|
| **OAuth 2.0** | Industry-standard authorization framework | Salesforce, Microsoft Dynamics, Zendesk |
| **Token-Based** | API key and bearer token authentication | SugarCRM, Custom Data Sources |
| **LDAP** | Directory-based authentication | Enterprise LDAP servers |
| **GoodData SSO** | Single sign-on for analytics platforms | GoodData |
| **Session-Based** | Traditional session management | Internal gateway access |

### Authentication Flow Diagram

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Client    │────▶│  Service Gateway │────▶│  Target Platform │
│ Application │     │   (Auth Layer)   │     │   (CRM/Source)   │
└─────────────┘     └──────────────────┘     └─────────────────┘
      │                      │                        │
      │  1. Auth Request     │                        │
      │─────────────────────▶│                        │
      │                      │  2. Validate/Forward   │
      │                      │───────────────────────▶│
      │                      │                        │
      │                      │  3. Platform Token     │
      │                      │◀───────────────────────│
      │  4. Gateway Token    │                        │
      │◀─────────────────────│                        │
```

---

## Quick Start

### Prerequisites

Before getting started, ensure you have the following installed:

- **PHP 7.4+** with required extensions (curl, json, mbstring, openssl)
- **Composer** (PHP package manager)
- **Docker** and **Docker Compose** (for containerized deployment)
- Access credentials for target CRM platforms

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/platform-service-gateway.git
cd platform-service-gateway

# Install dependencies via Composer
composer install

# Copy environment configuration
cp .env.example .env

# Configure your authentication credentials
nano .env
```

### Docker Deployment

```bash
# Build and start containers
docker-compose up -d

# Verify the gateway is running
docker-compose ps

# View logs
docker-compose logs -f gateway
```

### Basic Authentication Test

```php
<?php
// Example: Testing gateway authentication
require_once 'vendor/autoload.php';

use Gateway\Auth\TokenManager;
use Gateway\Client\GatewayClient;

$client = new GatewayClient([
    'base_url' => 'http://localhost:8080/api/v1',
    'api_key' => getenv('GATEWAY_API_KEY')
]);

// Authenticate with the gateway
$response = $client->authenticate([
    'platform' => 'salesforce',
    'credentials' => [
        'client_id' => getenv('SF_CLIENT_ID'),
        'client_secret' => getenv('SF_CLIENT_SECRET'),
        'username' => getenv('SF_USERNAME'),
        'password' => getenv('SF_PASSWORD')
    ]
]);

echo "Authentication successful. Token: " . $response->getToken();
```

---

## Login/Logout Flow

### Gateway Authentication Endpoints

The gateway exposes standardized authentication endpoints for all supported platforms:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | Initiate authentication |
| `/api/v1/auth/logout` | POST | Terminate session and revoke tokens |
| `/api/v1/auth/refresh` | POST | Refresh an expired access token |
| `/api/v1/auth/validate` | GET | Validate current token status |
| `/api/v1/auth/platforms` | GET | List available platforms |

### Login Flow Implementation

#### Step 1: Initiate Platform Authentication

```php
<?php
// Controller: application/classes/Controller/Auth.php

class Controller_Auth extends Controller_REST {
    
    /**
     * Handle login requests for multiple platforms
     */
    public function action_login()
    {
        $platform = $this->request->post('platform');
        $credentials = $this->request->post('credentials');
        
        // Validate required fields
        if (empty($platform) || empty($credentials)) {
            return $this->response_error(400, 'Missing required parameters');
        }
        
        try {
            // Get the appropriate authenticator for the platform
            $authenticator = Auth_Factory::create($platform);
            
            // Perform authentication
            $result = $authenticator->authenticate($credentials);
            
            // Generate gateway token
            $gateway_token = Token_Manager::generate([
                'platform' => $platform,
                'platform_token' => $result->access_token,
                'user_id' => $result->user_id,
                'expires_at' => time() + $result->expires_in
            ]);
            
            return $this->response_success([
                'token' => $gateway_token,
                'expires_in' => $result->expires_in,
                'platform' => $platform,
                'user' => $result->user_info
            ]);
            
        } catch (Auth_Exception $e) {
            Log::error('Authentication failed: ' . $e->getMessage());
            return $this->response_error(401, 'Authentication failed');
        }
    }
}
```

#### Step 2: Client-Side Login Request

```bash
# cURL example for Salesforce authentication
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "salesforce",
    "credentials": {
      "client_id": "your_client_id",
      "client_secret": "your_client_secret",
      "username": "user@example.com",
      "password": "password+security_token"
    }
  }'
```

**Response:**

```json
{
  "success": true,
  "data": {
    "token": "gw_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 7200,
    "platform": "salesforce",
    "user": {
      "id": "005xx000001Sv1IAAS",
      "email": "user@example.com",
      "display_name": "John Doe"
    }
  }
}
```

### Logout Flow Implementation

```php
<?php
// Logout handler with token revocation

class Controller_Auth extends Controller_REST {
    
    public function action_logout()
    {
        $token = $this->get_bearer_token();
        
        if (empty($token)) {
            return $this->response_error(401, 'No token provided');
        }
        
        try {
            // Decode and validate gateway token
            $token_data = Token_Manager::decode($token);
            
            // Revoke platform token if supported
            $authenticator = Auth_Factory::create($token_data->platform);
            if ($authenticator->supports_revocation()) {
                $authenticator->revoke($token_data->platform_token);
            }
            
            // Invalidate gateway token
            Token_Manager::invalidate($token);
            
            // Clear any session data
            Session::instance()->destroy();
            
            return $this->response_success([
                'message' => 'Successfully logged out'
            ]);
            
        } catch (Token_Exception $e) {
            return $this->response_error(400, 'Invalid token');
        }
    }
}
```

---

## Token Management

### Token Structure

The gateway uses JSON Web Tokens (JWT) with the following structure:

```php
<?php
// Token payload structure

$payload = [
    'iss' => 'platform-service-gateway',      // Issuer
    'sub' => 'user_identifier',               // Subject (user ID)
    'aud' => 'api_client',                    // Audience
    'exp' => time() + 7200,                   // Expiration time
    'iat' => time(),                          // Issued at
    'nbf' => time(),                          // Not before
    'jti' => uniqid('gw_', true),             // Token ID
    'platform' => 'salesforce',               // Target platform
    'platform_token' => 'encrypted_token',    // Encrypted platform token
    'scopes' => ['read', 'write'],            // Granted permissions
    'metadata' => [                           // Additional metadata
        'instance_url' => 'https://na1.salesforce.com',
        'org_id' => '00Dxx0000001gER'
    ]
];
```

### Token Manager Class

```php
<?php
// application/classes/Token/Manager.php

class Token_Manager {
    
    private static $secret_key;
    private static $algorithm = 'HS256';
    private static $token_ttl = 7200; // 2 hours default
    
    /**
     * Generate a new gateway token
     */
    public static function generate(array $data): string
    {
        $header = [
            'alg' => self::$algorithm,
            'typ' => 'JWT'
        ];
        
        $payload = array_merge([
            'iss' => 'platform-service-gateway',
            'iat' => time(),
            'exp' => $data['expires_at'] ?? time() + self::$token_ttl,
            'jti' => uniqid('gw_', true)
        ], $data);
        
        // Encrypt sensitive platform token
        if (isset($payload['platform_token'])) {
            $payload['platform_token'] = self::encrypt($payload['platform_token']);
        }
        
        return self::encode($header, $payload);
    }
    
    /**
     * Validate and decode a gateway token
     */
    public static function decode(string $token): object
    {
        $parts = explode('.', $token);
        
        if (count($parts) !== 3) {
            throw new Token_Exception('Invalid token format');
        }
        
        [$header, $payload, $signature] = $parts;
        
        // Verify signature
        $expected_signature = self::sign("$header.$payload");
        if (!hash_equals($expected_signature, $signature)) {
            throw new Token_Exception('Invalid token signature');
        }
        
        $payload_data = json_decode(base64_decode($payload));
        
        // Check expiration
        if ($payload_data->exp < time()) {
            throw new Token_Expired_Exception('Token has expired');
        }
        
        // Check if token is blacklisted
        if (self::is_blacklisted($payload_data->jti)) {
            throw new Token_Exception('Token has been revoked');
        }
        
        // Decrypt platform token
        if (isset($payload_data->platform_token)) {
            $payload_data->platform_token = self::decrypt($payload_data->platform_token);
        }
        
        return $payload_data;
    }
    
    /**
     * Refresh an existing token
     */
    public static function refresh(string $token): string
    {
        $data = self::decode($token);
        
        // Get fresh platform token if needed
        $authenticator = Auth_Factory::create($data->platform);
        $refreshed = $authenticator->refresh($data->platform_token);
        
        // Invalidate old token
        self::invalidate($token);
        
        // Generate new gateway token
        return self::generate([
            'platform' => $data->platform,
            'platform_token' => $refreshed->access_token,
            'user_id' => $data->sub,
            'expires_at' => time() + $refreshed->expires_in,
            'scopes' => $data->scopes ?? [],
            'metadata' => $data->metadata ?? []
        ]);
    }
    
    /**
     * Invalidate a token by adding to blacklist
     */
    public static function invalidate(string $token): void
    {
        $data = self::decode($token);
        
        // Store in Redis/cache with TTL matching token expiry
        $cache = Cache::instance();
        $ttl = $data->exp - time();
        
        if ($ttl > 0) {
            $cache->set("blacklist:{$data->jti}", true, $ttl);
        }
    }
    
    private static function is_blacklisted(string $jti): bool
    {
        return Cache::instance()->get("blacklist:$jti") === true;
    }
}
```

### Token Refresh Endpoint

```php
<?php
// Refresh token endpoint

public function action_refresh()
{
    $current_token = $this->get_bearer_token();
    
    try {
        $new_token = Token_Manager::refresh($current_token);
        
        return $this->response_success([
            'token' => $new_token,
            'expires_in' => 7200
        ]);
        
    } catch (Token_Expired_Exception $e) {
        return $this->response_error(401, 'Token expired, please re-authenticate');
    } catch (Token_Exception $e) {
        return $this->response_error(400, $e->getMessage());
    }
}
```

---

## Platform Authentication Index

The gateway supports authentication with multiple enterprise platforms. Each platform has specific requirements and authentication flows.

### Supported Platforms Overview

| Platform | Auth Type | Token Lifetime | Refresh Support | Documentation |
|----------|-----------|----------------|-----------------|---------------|
| **Salesforce** | OAuth 2.0 | 2 hours | ✅ Yes | [View Guide](docs/authentication/salesforce-auth.md) |
| **Microsoft Dynamics** | OAuth 2.0 | 1 hour | ✅ Yes | [View Guide](docs/authentication/msdynamics-auth.md) |
| **Zendesk** | OAuth 2.0 / API Token | Variable | ✅ Yes | [View Guide](docs/authentication/zendesk-auth.md) |
| **SugarCRM** | OAuth 2.0 | 1 hour | ✅ Yes | [View Guide](docs/authentication/sugarcrm-auth.md) |
| **Oracle Fusion** | OAuth 2.0 | 1 hour | ✅ Yes | [View Guide](docs/authentication/oracle-auth.md) |
| **LDAP** | Directory Auth | Session-based | ❌ No | [View Guide](docs/authentication/ldap-auth.md) |
| **GoodData** | SSO Token | Variable | ✅ Yes | [View Guide](docs/authentication/gooddata-auth.md) |

### Platform-Specific Configuration

```php
<?php
// config/platforms.php

return [
    'salesforce' => [
        'auth_type' => 'oauth2',
        'auth_url' => 'https://login.salesforce.com/services/oauth2/authorize',
        'token_url' => 'https://login.salesforce.com/services/oauth2/token',
        'revoke_url' => 'https://login.salesforce.com/services/oauth2/revoke',
        'scopes' => ['api', 'refresh_token'],
        'token_ttl' => 7200,
        'supports_refresh' => true
    ],
    
    'msdynamics' => [
        'auth_type' => 'oauth2',
        'auth_url' => 'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize',
        'token_url' => 'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token',
        'scopes' => ['https://org.crm.dynamics.com/.default'],
        'token_ttl' => 3600,
        'supports_refresh' => true
    ],
    
    'zendesk' => [
        'auth_type' => 'oauth2',
        'auth_url' => 'https://{subdomain}.zendesk.com/oauth/authorizations/new',
        'token_url' => 'https://{subdomain}.zendesk.com/oauth/tokens',
        'scopes' => ['read', 'write'],
        'token_ttl' => 7200,
        'supports_api_token' => true
    ],
    
    'sugarcrm' => [
        'auth_type' => 'oauth2',
        'token_url' => '{instance_url}/rest/v11_4/oauth2/token',
        'token_ttl' => 3600,
        'supports_refresh' => true
    ],
    
    'ldap' => [
        'auth_type' => 'ldap',
        'host' => getenv('LDAP_HOST'),
        'port' => getenv('LDAP_PORT') ?: 389,
        'base_dn' => getenv('LDAP_BASE_DN'),
        'use_ssl' => getenv('LDAP_USE_SSL') === 'true'
    ],
    
    'gooddata' => [
        'auth_type' => 'sso',
        'sso_url' => getenv('GOODDATA_SSO_URL'),
        'provider_id' => getenv('GOODDATA_PROVIDER_ID')
    ]
];
```

### Platform Authenticator Factory

```php
<?php
// application/classes/Auth/Factory.php

class Auth_Factory {
    
    private static $authenticators = [
        'salesforce' => 'Auth_Salesforce',
        'msdynamics' => 'Auth_MSDynamics',
        'zendesk' => 'Auth_Zendesk',
        'sugarcrm' => 'Auth_SugarCRM',
        'oracle' => 'Auth_Oracle',
        'ldap' => 'Auth_LDAP',
        'gooddata' => 'Auth_GoodData'
    ];
    
    /**
     * Create an authenticator instance for the specified platform
     */
    public static function create(string $platform): Auth_Interface
    {
        $platform = strtolower($platform);
        
        if (!isset(self::$authenticators[$platform])) {
            throw new Auth_Exception("Unsupported platform: $platform");
        }
        
        $class = self::$authenticators[$platform];
        $config = Kohana::$config->load("platforms.$platform");
        
        return new $class($config);
    }
    
    /**
     * Get list of available platforms
     */
    public static function available_platforms(): array
    {
        return array_keys(self::$authenticators);
    }
}
```

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                     Platform Service Gateway                        │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │   REST API  │  │  Auth Layer │  │Token Manager│                │
│  │  Controller │──│   Factory   │──│   (JWT)     │                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
│         │                │                │                        │
│         ▼                ▼                ▼                        │
│  ┌─────────────────────────────────────────────────┐              │
│  │              Platform Authenticators             │              │
│  ├──────────┬──────────┬──────────┬────────────────┤              │
│  │Salesforce│ Dynamics │ Zendesk  │    LDAP       │              │
│  │  OAuth   │  OAuth   │  OAuth   │   Bind        │              │
│  └──────────┴──────────┴──────────┴────────────────┘              │
│         │          │          │           │                        │
└─────────┼──────────┼──────────┼───────────┼────────────────────────┘
          ▼          ▼          ▼           ▼
    ┌──────────┐┌──────────┐┌──────────┐┌──────────┐
    │Salesforce││ MS 365   ││ Zendesk  ││  LDAP    │
    │   API    ││   API    ││   API    ││  Server  │
    └──────────┘└──────────┘└──────────┘└──────────┘
```

### Key Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **Auth Factory** | Creates platform-specific authenticators | `application/classes/Auth/Factory.php` |
| **Token Manager** | JWT generation and validation | `application/classes/Token/Manager.php` |
| **Platform Authenticators** | Individual platform auth logic | `application/classes/Auth/{Platform}.php` |
| **REST Controllers** | API endpoint handlers | `application/classes/Controller/` |
| **Configuration** | Platform and auth settings | `application/config/` |

---

## Configuration Reference

### Environment Variables

```bash
# Gateway Configuration
GATEWAY_SECRET_KEY=your-256-bit-secret-key
GATEWAY_TOKEN_TTL=7200
GATEWAY_DEBUG=false

# Salesforce
SF_CLIENT_ID=your_salesforce_client_id
SF_CLIENT_SECRET=your_salesforce_client_secret
SF_CALLBACK_URL=http://localhost:8080/auth/salesforce/callback

# Microsoft Dynamics
MSDYNAMICS_TENANT_ID=your_tenant_id
MSDYNAMICS_CLIENT_ID=your_client_id
MSDYNAMICS_CLIENT_SECRET=your_client_secret
MSDYNAMICS_RESOURCE_URL=https://your-org.crm.dynamics.com

# Zendesk
ZENDESK_SUBDOMAIN=your_subdomain
ZENDESK_CLIENT_ID=your_client_id
ZENDESK_CLIENT_SECRET=your_client_secret

# SugarCRM
SUGARCRM_URL=https://your-instance.sugarondemand.com
SUGARCRM_CLIENT_ID=sugar
SUGARCRM_CLIENT_SECRET=your_client_secret

# LDAP
LDAP_HOST=ldap.example.com
LDAP_PORT=389
LDAP_BASE_DN=dc=example,dc=com
LDAP_USE_SSL=false

# GoodData
GOODDATA_SSO_URL=https://secure.gooddata.com
GOODDATA_PROVIDER_ID=your_provider_id
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  gateway:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:80"
    environment:
      - GATEWAY_SECRET_KEY=${GATEWAY_SECRET_KEY}
      - GATEWAY_DEBUG=${GATEWAY_DEBUG:-false}
    volumes:
      - ./application:/var/www/html/application
      - ./logs:/var/www/html/logs
    depends_on:
      - redis
    networks:
      - gateway-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - gateway-network

volumes:
  redis-data:

networks:
  gateway-network:
    driver: bridge
```

---

## Troubleshooting

### Common Authentication Issues

#### 1. Token Expired Errors

```json
{
  "error": "token_expired",
  "message": "Token has expired, please re-authenticate"
}
```

**Solution:** Implement automatic token refresh in your client:

```php
<?php
// Auto-refresh middleware example
class Token_Refresh_Middleware {
    
    public function handle($request, $next)
    {
        try {
            return $next($request);
        } catch (Token_Expired_Exception $e) {
            // Attempt to refresh
            $new_token = Token_Manager::refresh($request->token);
            $request->set_token($new_token);
            return $next($request);
        }
    }
}
```

#### 2. Platform Connection Failures

```bash
# Check platform connectivity
curl -X GET http://localhost:8080/api/v1/health/platforms

# Test specific platform
curl -X POST http://localhost:8080/api/v1/auth/test \
  -H "Content-Type: application/json" \
  -d '{"platform": "salesforce"}'
```

#### 3. LDAP Bind Failures

Check LDAP configuration and ensure proper DN format:

```php
// Correct DN format
$dn = "cn=username,ou=users,dc=example,dc=com";

// Common mistakes
// ❌ "username@example.com" (for some LDAP servers)
// ❌ "example\\username" (AD format may require special handling)
```

### Debug Mode

Enable debug logging for detailed authentication traces:

```php
// config/development/auth.php
return [
    'debug' => true,
    'log_level' => 'DEBUG',
    'log_requests' => true,
    'log_responses' => false  // Disable in production (contains tokens)
];
```

---

## Related Documentation

For detailed platform-specific authentication guides, please refer to:

- **[SugarCRM Authentication](docs/authentication/sugarcrm-auth.md)** - Complete guide for SugarCRM OAuth 2.0 integration
- **[Microsoft Dynamics Authentication](docs/authentication/msdynamics-auth.md)** - Azure AD and Dynamics 365 authentication setup
- **[Zendesk Authentication](docs/authentication/zendesk-auth.md)** - OAuth and API token authentication for Zendesk
- **[LDAP Authentication](docs/authentication/ldap-auth.md)** - Enterprise directory authentication configuration
- **[GoodData Authentication](docs/authentication/gooddata-auth.md)** - SSO integration with GoodData analytics platform

### Additional Resources

| Resource | Description |
|----------|-------------|
| [API Reference](docs/api/README.md) | Complete REST API documentation (59 endpoints) |
| [Data Models](docs/models/README.md) | Entity and model documentation (100 models) |
| [Configuration Guide](docs/config/README.md) | All configuration options (50 variables) |
| [Deployment Guide](docs/deployment/README.md) | Production deployment instructions |
| [Security Best Practices](docs/security/README.md) | Security hardening recommendations |

---

## Support

For issues and feature requests, please use the GitHub issue tracker or contact the platform team.

**Maintained by:** Platform Integration Team  
**Last Updated:** 2024