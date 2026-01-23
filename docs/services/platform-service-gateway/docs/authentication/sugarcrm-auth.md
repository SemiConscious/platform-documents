# SugarCRM Authentication

## Overview

This document provides comprehensive guidance for implementing and managing authentication with SugarCRM through the Platform Service Gateway. SugarCRM uses OAuth 2.0 for API authentication, requiring proper credential management, token handling, and session lifecycle management. The gateway abstracts much of this complexity while providing a unified interface for CRM operations.

SugarCRM authentication in the Platform Service Gateway supports both SugarCRM versions 7.x and later (which use OAuth 2.0) and can be configured for on-premise or cloud-hosted SugarCRM instances. This documentation covers the complete authentication lifecycle from initial setup through token refresh and session management.

---

## Prerequisites

Before configuring SugarCRM authentication, ensure you have the following requirements in place:

### SugarCRM Instance Requirements

| Requirement | Description |
|-------------|-------------|
| SugarCRM Version | 7.0 or later (REST API v10+) |
| API Access | REST API must be enabled on your SugarCRM instance |
| OAuth2 Client | A configured OAuth2 client (platform) in SugarCRM |
| Admin Access | Administrative access to create API users and OAuth keys |

### Platform Service Gateway Requirements

- Platform Service Gateway v2.0 or later installed and running
- PHP 7.4+ with required extensions (curl, json, openssl)
- Network connectivity between gateway and SugarCRM instance
- Valid SSL certificates if using HTTPS (recommended)

### Required Credentials

You will need to obtain the following from your SugarCRM administrator:

1. **SugarCRM Instance URL** - The base URL of your SugarCRM instance (e.g., `https://yourinstance.sugarcrm.com`)
2. **OAuth2 Client ID** - The platform name registered in SugarCRM
3. **OAuth2 Client Secret** - The secret associated with the OAuth2 client (if configured)
4. **API Username** - A SugarCRM user account with appropriate API permissions
5. **API Password** - The password for the API user account

### Creating an OAuth2 Platform in SugarCRM

To register a new OAuth2 platform in SugarCRM, execute the following in the SugarCRM console or via API:

```php
// SugarCRM Administration: Create OAuth2 Platform
// Navigate to Admin > OAuth Keys and create a new key

// Alternatively, register via the database:
$platform_data = [
    'id' => 'platform-service-gateway',
    'name' => 'Platform Service Gateway',
    'client_id' => 'platform_gateway_client',
    'client_secret' => 'your_secure_client_secret',
    'description' => 'API integration for Platform Service Gateway',
    'date_entered' => date('Y-m-d H:i:s'),
    'date_modified' => date('Y-m-d H:i:s')
];
```

---

## Configuration

### Environment Configuration

Configure SugarCRM authentication parameters in your gateway's environment file:

```bash
# .env configuration for SugarCRM
SUGARCRM_ENABLED=true
SUGARCRM_INSTANCE_URL=https://yourinstance.sugarcrm.com
SUGARCRM_API_VERSION=v10
SUGARCRM_CLIENT_ID=platform_gateway_client
SUGARCRM_CLIENT_SECRET=your_secure_client_secret
SUGARCRM_USERNAME=api_user
SUGARCRM_PASSWORD=your_api_password
SUGARCRM_PLATFORM=platform-service-gateway

# Token management settings
SUGARCRM_TOKEN_CACHE_ENABLED=true
SUGARCRM_TOKEN_CACHE_DRIVER=redis
SUGARCRM_TOKEN_REFRESH_THRESHOLD=300

# Connection settings
SUGARCRM_TIMEOUT=30
SUGARCRM_VERIFY_SSL=true
SUGARCRM_DEBUG_MODE=false
```

### CodeIgniter Configuration File

Create or update the SugarCRM configuration file in your gateway application:

```php
<?php
// application/config/sugarcrm.php

defined('BASEPATH') OR exit('No direct script access allowed');

$config['sugarcrm'] = [
    // Instance Configuration
    'instance_url' => getenv('SUGARCRM_INSTANCE_URL') ?: 'https://localhost/sugarcrm',
    'api_version' => getenv('SUGARCRM_API_VERSION') ?: 'v10',
    
    // OAuth2 Credentials
    'client_id' => getenv('SUGARCRM_CLIENT_ID') ?: '',
    'client_secret' => getenv('SUGARCRM_CLIENT_SECRET') ?: '',
    'platform' => getenv('SUGARCRM_PLATFORM') ?: 'base',
    
    // User Credentials
    'username' => getenv('SUGARCRM_USERNAME') ?: '',
    'password' => getenv('SUGARCRM_PASSWORD') ?: '',
    
    // Token Management
    'token_cache' => [
        'enabled' => filter_var(getenv('SUGARCRM_TOKEN_CACHE_ENABLED'), FILTER_VALIDATE_BOOLEAN),
        'driver' => getenv('SUGARCRM_TOKEN_CACHE_DRIVER') ?: 'file',
        'prefix' => 'sugarcrm_token_',
        'refresh_threshold' => (int) getenv('SUGARCRM_TOKEN_REFRESH_THRESHOLD') ?: 300,
    ],
    
    // HTTP Client Settings
    'http' => [
        'timeout' => (int) getenv('SUGARCRM_TIMEOUT') ?: 30,
        'connect_timeout' => 10,
        'verify_ssl' => filter_var(getenv('SUGARCRM_VERIFY_SSL'), FILTER_VALIDATE_BOOLEAN),
        'debug' => filter_var(getenv('SUGARCRM_DEBUG_MODE'), FILTER_VALIDATE_BOOLEAN),
    ],
    
    // Retry Configuration
    'retry' => [
        'max_attempts' => 3,
        'delay_ms' => 1000,
        'multiplier' => 2,
    ],
];
```

### Database Configuration for Token Storage

If using database-backed token storage, ensure the following table exists:

```sql
-- Migration for SugarCRM token storage
CREATE TABLE IF NOT EXISTS `sugarcrm_tokens` (
    `id` INT(11) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `user_identifier` VARCHAR(255) NOT NULL,
    `access_token` TEXT NOT NULL,
    `refresh_token` TEXT NOT NULL,
    `token_type` VARCHAR(50) DEFAULT 'bearer',
    `expires_at` DATETIME NOT NULL,
    `download_token` TEXT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY `idx_user_identifier` (`user_identifier`),
    KEY `idx_expires_at` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## Authentication Flow

### OAuth 2.0 Password Grant Flow

The Platform Service Gateway uses the OAuth 2.0 Resource Owner Password Credentials grant type for SugarCRM authentication. This flow is appropriate for server-to-server communication where the gateway acts on behalf of a configured service account.

```
┌─────────────────┐                                    ┌──────────────────┐
│                 │                                    │                  │
│  Gateway Client │                                    │    SugarCRM      │
│                 │                                    │    Instance      │
└────────┬────────┘                                    └────────┬─────────┘
         │                                                      │
         │  1. POST /rest/v10/oauth2/token                     │
         │     grant_type=password                              │
         │     client_id, client_secret                         │
         │     username, password, platform                     │
         │─────────────────────────────────────────────────────>│
         │                                                      │
         │  2. 200 OK                                           │
         │     {access_token, refresh_token, expires_in}        │
         │<─────────────────────────────────────────────────────│
         │                                                      │
         │  3. API Request with Bearer Token                    │
         │     Authorization: Bearer {access_token}             │
         │─────────────────────────────────────────────────────>│
         │                                                      │
         │  4. 200 OK - API Response                            │
         │<─────────────────────────────────────────────────────│
         │                                                      │
```

### Authentication Service Implementation

```php
<?php
// application/libraries/SugarCRM_Auth.php

defined('BASEPATH') OR exit('No direct script access allowed');

class SugarCRM_Auth {
    
    protected $CI;
    protected $config;
    protected $http_client;
    protected $token_storage;
    
    const GRANT_TYPE_PASSWORD = 'password';
    const GRANT_TYPE_REFRESH = 'refresh_token';
    
    public function __construct($params = [])
    {
        $this->CI =& get_instance();
        $this->CI->config->load('sugarcrm', TRUE);
        $this->config = $this->CI->config->item('sugarcrm');
        
        $this->initialize_http_client();
        $this->initialize_token_storage();
    }
    
    /**
     * Authenticate and obtain access token
     * 
     * @param string|null $username Override configured username
     * @param string|null $password Override configured password
     * @return array Token response containing access_token, refresh_token, expires_in
     * @throws SugarCRM_Auth_Exception
     */
    public function authenticate($username = null, $password = null)
    {
        $username = $username ?: $this->config['username'];
        $password = $password ?: $this->config['password'];
        
        // Check for cached valid token
        $cached_token = $this->get_cached_token($username);
        if ($cached_token && !$this->is_token_expiring_soon($cached_token)) {
            log_message('debug', 'SugarCRM: Using cached access token');
            return $cached_token;
        }
        
        // Try refresh token if available
        if ($cached_token && !empty($cached_token['refresh_token'])) {
            try {
                return $this->refresh_access_token($cached_token['refresh_token'], $username);
            } catch (Exception $e) {
                log_message('warning', 'SugarCRM: Token refresh failed, re-authenticating: ' . $e->getMessage());
            }
        }
        
        // Perform full authentication
        return $this->perform_password_grant($username, $password);
    }
    
    /**
     * Perform OAuth2 password grant authentication
     */
    protected function perform_password_grant($username, $password)
    {
        $token_url = $this->build_api_url('/oauth2/token');
        
        $payload = [
            'grant_type' => self::GRANT_TYPE_PASSWORD,
            'client_id' => $this->config['client_id'],
            'client_secret' => $this->config['client_secret'],
            'username' => $username,
            'password' => $password,
            'platform' => $this->config['platform'],
        ];
        
        try {
            $response = $this->http_client->post($token_url, [
                'form_params' => $payload,
                'headers' => [
                    'Content-Type' => 'application/x-www-form-urlencoded',
                    'Accept' => 'application/json',
                ],
            ]);
            
            $token_data = json_decode($response->getBody()->getContents(), true);
            
            if (empty($token_data['access_token'])) {
                throw new SugarCRM_Auth_Exception('Invalid token response from SugarCRM');
            }
            
            // Calculate expiration timestamp
            $token_data['expires_at'] = time() + ($token_data['expires_in'] ?? 3600);
            $token_data['obtained_at'] = time();
            
            // Cache the token
            $this->cache_token($username, $token_data);
            
            log_message('info', 'SugarCRM: Successfully authenticated user ' . $username);
            
            return $token_data;
            
        } catch (GuzzleHttp\Exception\ClientException $e) {
            $this->handle_auth_error($e);
        }
    }
    
    /**
     * Refresh an expired access token
     */
    public function refresh_access_token($refresh_token, $username = null)
    {
        $token_url = $this->build_api_url('/oauth2/token');
        
        $payload = [
            'grant_type' => self::GRANT_TYPE_REFRESH,
            'client_id' => $this->config['client_id'],
            'client_secret' => $this->config['client_secret'],
            'refresh_token' => $refresh_token,
            'platform' => $this->config['platform'],
        ];
        
        try {
            $response = $this->http_client->post($token_url, [
                'form_params' => $payload,
                'headers' => [
                    'Content-Type' => 'application/x-www-form-urlencoded',
                    'Accept' => 'application/json',
                ],
            ]);
            
            $token_data = json_decode($response->getBody()->getContents(), true);
            $token_data['expires_at'] = time() + ($token_data['expires_in'] ?? 3600);
            $token_data['obtained_at'] = time();
            
            $this->cache_token($username ?: $this->config['username'], $token_data);
            
            log_message('info', 'SugarCRM: Successfully refreshed access token');
            
            return $token_data;
            
        } catch (Exception $e) {
            throw new SugarCRM_Auth_Exception('Token refresh failed: ' . $e->getMessage());
        }
    }
    
    /**
     * Revoke/logout the current session
     */
    public function logout($access_token = null)
    {
        $token = $access_token ?: $this->get_current_access_token();
        
        if (!$token) {
            return true;
        }
        
        $logout_url = $this->build_api_url('/oauth2/logout');
        
        try {
            $this->http_client->post($logout_url, [
                'headers' => [
                    'Authorization' => 'Bearer ' . $token,
                    'Accept' => 'application/json',
                ],
            ]);
            
            $this->clear_cached_token($this->config['username']);
            
            log_message('info', 'SugarCRM: Successfully logged out');
            
            return true;
            
        } catch (Exception $e) {
            log_message('error', 'SugarCRM: Logout failed: ' . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Build SugarCRM API URL
     */
    protected function build_api_url($endpoint)
    {
        $base = rtrim($this->config['instance_url'], '/');
        $version = $this->config['api_version'];
        return "{$base}/rest/{$version}" . $endpoint;
    }
    
    /**
     * Check if token is expiring soon
     */
    protected function is_token_expiring_soon($token_data)
    {
        $threshold = $this->config['token_cache']['refresh_threshold'];
        return ($token_data['expires_at'] - time()) < $threshold;
    }
    
    /**
     * Handle authentication errors with detailed messages
     */
    protected function handle_auth_error($exception)
    {
        $response = $exception->getResponse();
        $body = json_decode($response->getBody()->getContents(), true);
        
        $error_map = [
            'invalid_grant' => 'Invalid username or password',
            'invalid_client' => 'Invalid client ID or secret',
            'need_login' => 'Authentication required - session expired',
            'invalid_platform' => 'The specified platform is not registered in SugarCRM',
        ];
        
        $error_code = $body['error'] ?? 'unknown_error';
        $message = $error_map[$error_code] ?? ($body['error_message'] ?? 'Authentication failed');
        
        log_message('error', "SugarCRM Auth Error [{$error_code}]: {$message}");
        
        throw new SugarCRM_Auth_Exception($message, 0, $exception);
    }
}

class SugarCRM_Auth_Exception extends Exception {}
```

---

## Session Management

### Token Lifecycle Management

Proper session management is critical for maintaining reliable connections to SugarCRM. The gateway implements several strategies to ensure continuous availability:

```php
<?php
// application/libraries/SugarCRM_Session_Manager.php

class SugarCRM_Session_Manager {
    
    protected $auth;
    protected $cache;
    protected $config;
    
    /**
     * Get valid access token, refreshing if necessary
     * 
     * @return string Valid access token
     */
    public function get_valid_token()
    {
        $token_data = $this->auth->authenticate();
        return $token_data['access_token'];
    }
    
    /**
     * Execute API call with automatic token refresh
     * 
     * @param callable $api_call The API call to execute
     * @return mixed API response
     */
    public function execute_with_retry(callable $api_call)
    {
        $max_retries = 2;
        $attempt = 0;
        
        while ($attempt < $max_retries) {
            try {
                $token = $this->get_valid_token();
                return $api_call($token);
                
            } catch (SugarCRM_Unauthorized_Exception $e) {
                $attempt++;
                log_message('warning', "SugarCRM: Auth retry {$attempt}/{$max_retries}");
                
                // Force token refresh
                $this->invalidate_current_token();
                
                if ($attempt >= $max_retries) {
                    throw $e;
                }
            }
        }
    }
    
    /**
     * Invalidate current cached token
     */
    public function invalidate_current_token()
    {
        $cache_key = $this->get_token_cache_key();
        $this->cache->delete($cache_key);
        log_message('info', 'SugarCRM: Invalidated cached token');
    }
    
    /**
     * Check session health
     * 
     * @return array Session status information
     */
    public function get_session_status()
    {
        $token_data = $this->cache->get($this->get_token_cache_key());
        
        if (!$token_data) {
            return [
                'status' => 'no_session',
                'authenticated' => false,
            ];
        }
        
        $now = time();
        $expires_at = $token_data['expires_at'] ?? 0;
        $time_remaining = $expires_at - $now;
        
        return [
            'status' => $time_remaining > 0 ? 'active' : 'expired',
            'authenticated' => $time_remaining > 0,
            'expires_at' => date('Y-m-d H:i:s', $expires_at),
            'time_remaining_seconds' => max(0, $time_remaining),
            'obtained_at' => date('Y-m-d H:i:s', $token_data['obtained_at'] ?? 0),
            'has_refresh_token' => !empty($token_data['refresh_token']),
        ];
    }
}
```

### Concurrent Request Handling

When multiple requests need authentication simultaneously, implement token locking to prevent race conditions:

```php
<?php
// Token locking implementation for concurrent requests

class SugarCRM_Token_Lock {
    
    protected $redis;
    protected $lock_ttl = 10; // seconds
    
    /**
     * Acquire lock for token refresh
     */
    public function acquire_refresh_lock($identifier)
    {
        $lock_key = "sugarcrm_token_lock:{$identifier}";
        
        $acquired = $this->redis->set(
            $lock_key,
            getmypid(),
            ['NX', 'EX' => $this->lock_ttl]
        );
        
        return $acquired;
    }
    
    /**
     * Release token refresh lock
     */
    public function release_refresh_lock($identifier)
    {
        $lock_key = "sugarcrm_token_lock:{$identifier}";
        
        // Only release if we own the lock
        $script = <<<LUA
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        LUA;
        
        return $this->redis->eval($script, [$lock_key, getmypid()], 1);
    }
    
    /**
     * Wait for token refresh to complete
     */
    public function wait_for_token($identifier, $timeout = 10)
    {
        $start = time();
        $lock_key = "sugarcrm_token_lock:{$identifier}";
        
        while ($this->redis->exists($lock_key)) {
            if ((time() - $start) > $timeout) {
                throw new Exception('Timeout waiting for token refresh');
            }
            usleep(100000); // 100ms
        }
    }
}
```

---

## Code Examples

### Basic Authentication Example

```php
<?php
// Example: Basic authentication and API call

$this->load->library('sugarcrm_auth');
$this->load->library('sugarcrm_client');

try {
    // Authenticate
    $token_data = $this->sugarcrm_auth->authenticate();
    
    echo "Successfully authenticated\n";
    echo "Token expires in: " . $token_data['expires_in'] . " seconds\n";
    
    // Make an API call
    $accounts = $this->sugarcrm_client->get('Accounts', [
        'max_num' => 10,
        'fields' => ['id', 'name', 'billing_address_city'],
    ]);
    
    foreach ($accounts['records'] as $account) {
        echo "Account: " . $account['name'] . "\n";
    }
    
} catch (SugarCRM_Auth_Exception $e) {
    log_message('error', 'Authentication failed: ' . $e->getMessage());
}
```

### Controller Implementation

```php
<?php
// application/controllers/api/Sugarcrm.php

defined('BASEPATH') OR exit('No direct script access allowed');

class Sugarcrm extends REST_Controller {
    
    public function __construct()
    {
        parent::__construct();
        $this->load->library('sugarcrm_auth');
        $this->load->library('sugarcrm_session_manager');
    }
    
    /**
     * GET /api/sugarcrm/auth/status
     * Check current authentication status
     */
    public function auth_status_get()
    {
        $status = $this->sugarcrm_session_manager->get_session_status();
        
        $this->response([
            'success' => true,
            'data' => $status,
        ], REST_Controller::HTTP_OK);
    }
    
    /**
     * POST /api/sugarcrm/auth/login
     * Authenticate with SugarCRM
     */
    public function auth_login_post()
    {
        $username = $this->post('username');
        $password = $this->post('password');
        
        try {
            $token_data = $this->sugarcrm_auth->authenticate($username, $password);
            
            $this->response([
                'success' => true,
                'message' => 'Authentication successful',
                'data' => [
                    'expires_in' => $token_data['expires_in'],
                    'token_type' => $token_data['token_type'],
                ],
            ], REST_Controller::HTTP_OK);
            
        } catch (SugarCRM_Auth_Exception $e) {
            $this->response([
                'success' => false,
                'error' => 'authentication_failed',
                'message' => $e->getMessage(),
            ], REST_Controller::HTTP_UNAUTHORIZED);
        }
    }
    
    /**
     * POST /api/sugarcrm/auth/logout
     * Revoke current session
     */
    public function auth_logout_post()
    {
        $result = $this->sugarcrm_auth->logout();
        
        $this->response([
            'success' => $result,
            'message' => $result ? 'Logged out successfully' : 'Logout failed',
        ], REST_Controller::HTTP_OK);
    }
    
    /**
     * POST /api/sugarcrm/auth/refresh
     * Manually refresh access token
     */
    public function auth_refresh_post()
    {
        try {
            $token_data = $this->sugarcrm_auth->authenticate();
            
            $this->response([
                'success' => true,
                'message' => 'Token refreshed',
                'data' => [
                    'expires_in' => $token_data['expires_in'],
                ],
            ], REST_Controller::HTTP_OK);
            
        } catch (SugarCRM_Auth_Exception $e) {
            $this->response([
                'success' => false,
                'error' => 'refresh_failed',
                'message' => $e->getMessage(),
            ], REST_Controller::HTTP_UNAUTHORIZED);
        }
    }
}
```

### Middleware for Authenticated Requests

```php
<?php
// application/hooks/SugarCRM_Auth_Hook.php

class SugarCRM_Auth_Hook {
    
    protected $CI;
    
    public function __construct()
    {
        $this->CI =& get_instance();
    }
    
    /**
     * Pre-controller hook to ensure valid SugarCRM session
     */
    public function ensure_authenticated()
    {
        // Skip for non-SugarCRM routes
        if (!$this->is_sugarcrm_route()) {
            return;
        }
        
        $this->CI->load->library('sugarcrm_auth');
        
        try {
            // This will automatically refresh if needed
            $this->CI->sugarcrm_auth->authenticate();
        } catch (SugarCRM_Auth_Exception $e) {
            log_message('error', 'SugarCRM pre-auth failed: ' . $e->getMessage());
            
            // Allow the request to proceed - individual endpoints will handle auth errors
        }
    }
    
    protected function is_sugarcrm_route()
    {
        $uri = $this->CI->uri->uri_string();
        return strpos($uri, 'sugarcrm') !== false;
    }
}
```

### Docker Integration

```yaml
# docker-compose.yml - SugarCRM authentication configuration

version: '3.8'

services:
  gateway:
    build: .
    environment:
      - SUGARCRM_ENABLED=true
      - SUGARCRM_INSTANCE_URL=${SUGARCRM_URL}
      - SUGARCRM_CLIENT_ID=${SUGARCRM_CLIENT_ID}
      - SUGARCRM_CLIENT_SECRET=${SUGARCRM_CLIENT_SECRET}
      - SUGARCRM_USERNAME=${SUGARCRM_USERNAME}
      - SUGARCRM_PASSWORD=${SUGARCRM_PASSWORD}
      - SUGARCRM_TOKEN_CACHE_DRIVER=redis
    depends_on:
      - redis
    secrets:
      - sugarcrm_credentials

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

secrets:
  sugarcrm_credentials:
    file: ./secrets/sugarcrm.env

volumes:
  redis_data:
```

---

## Troubleshooting

### Common Authentication Errors

| Error Code | Description | Solution |
|------------|-------------|----------|
| `invalid_grant` | Wrong username/password | Verify credentials in SugarCRM admin |
| `invalid_client` | Client ID/secret mismatch | Check OAuth key configuration |
| `invalid_platform` | Platform not registered | Register platform in SugarCRM Admin > OAuth Keys |
| `need_login` | Session expired | Token will auto-refresh; check refresh token validity |
| `rate_limit_exceeded` | Too many auth attempts | Implement request throttling |

### Debug Logging

Enable debug mode for detailed authentication logs:

```php
// Enable in configuration
$config['sugarcrm']['http']['debug'] = true;

// Or via environment
// SUGARCRM_DEBUG_MODE=true
```

---

## Security Best Practices

1. **Never log access tokens** - Tokens should be treated as secrets
2. **Use HTTPS** - Always connect to SugarCRM over TLS
3. **Rotate credentials regularly** - Update API user passwords periodically
4. **Limit API user permissions** - Grant only necessary module access
5. **Monitor authentication failures** - Alert on repeated auth failures
6. **Secure token storage** - Use encrypted cache backends in production

---

## Related Documentation

- [SugarCRM REST API v10 Documentation](https://support.sugarcrm.com/Documentation/Sugar_Developer/Sugar_Developer_Guide/)
- [Platform Service Gateway - Unified Query Interface](./unified-query-interface.md)
- [OAuth 2.0 Configuration Guide](./oauth-configuration.md)
- [Token Cache Configuration](./token-cache-setup.md)