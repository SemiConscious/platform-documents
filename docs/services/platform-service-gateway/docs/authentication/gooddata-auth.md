# GoodData Authentication

## Overview

GoodData authentication in the Platform Service Gateway enables secure integration with GoodData analytics platform, allowing your applications to access powerful business intelligence and data visualization capabilities. This document provides comprehensive guidance on setting up, configuring, and implementing GoodData authentication within the gateway service.

GoodData is an enterprise analytics platform that provides embedded analytics, dashboards, and data visualization tools. The Platform Service Gateway implements a robust authentication mechanism that supports GoodData's Super Secure Token (SST) and Temporary Token (TT) authentication flow, enabling seamless integration with your CRM data sources.

---

## Prerequisites

Before implementing GoodData authentication, ensure you have the following prerequisites in place:

### GoodData Account Requirements

1. **Active GoodData Account**: A valid GoodData enterprise or developer account with API access enabled
2. **Project Access**: At least one GoodData project/workspace that your integration will access
3. **API Credentials**: Your GoodData domain, username, and password or API token
4. **White-label Domain** (optional): If using a custom domain, ensure it's properly configured in GoodData

### Platform Service Gateway Requirements

1. **Gateway Installation**: Platform Service Gateway v2.0 or higher installed and running
2. **PHP Version**: PHP 7.4 or higher with the following extensions:
   - `curl`
   - `json`
   - `openssl`
3. **Composer Dependencies**: All required packages installed via Composer
4. **Network Access**: Outbound HTTPS access to GoodData API endpoints (typically `secure.gooddata.com` or your custom domain)

### Environment Setup

```bash
# Verify PHP version and extensions
php -v
php -m | grep -E "(curl|json|openssl)"

# Install/update Composer dependencies
composer install --no-dev --optimize-autoloader
```

### Required Configuration Files

Ensure these configuration files exist and are writable:

- `application/config/gooddata.php` - Main GoodData configuration
- `application/config/auth.php` - General authentication settings
- `.env` or `application/config/database.php` - Database configuration for token storage

---

## Configuration

### Basic Configuration

Create or modify the GoodData configuration file at `application/config/gooddata.php`:

```php
<?php
defined('BASEPATH') OR exit('No direct script access allowed');

/**
 * GoodData Authentication Configuration
 * 
 * This configuration file defines all settings required for
 * GoodData analytics platform integration.
 */

$config['gooddata'] = [
    // GoodData API endpoint
    'api_endpoint' => getenv('GOODDATA_API_ENDPOINT') ?: 'https://secure.gooddata.com',
    
    // Authentication credentials
    'username' => getenv('GOODDATA_USERNAME'),
    'password' => getenv('GOODDATA_PASSWORD'),
    
    // Project/Workspace configuration
    'project_id' => getenv('GOODDATA_PROJECT_ID'),
    
    // Token settings
    'token_ttl' => 3600, // Token time-to-live in seconds
    'token_refresh_threshold' => 300, // Refresh token when less than 5 minutes remain
    
    // SSL/TLS settings
    'verify_ssl' => true,
    'ssl_cert_path' => null, // Path to custom CA bundle if needed
    
    // Request settings
    'timeout' => 30,
    'connect_timeout' => 10,
    
    // Caching
    'cache_enabled' => true,
    'cache_driver' => 'redis', // Options: redis, memcached, file
    'cache_prefix' => 'gooddata_auth_',
    
    // Logging
    'log_requests' => true,
    'log_level' => 'info', // debug, info, warning, error
];
```

### Environment Variables

For security, store sensitive credentials in environment variables. Add these to your `.env` file:

```bash
# GoodData Authentication Settings
GOODDATA_API_ENDPOINT=https://secure.gooddata.com
GOODDATA_USERNAME=your-username@domain.com
GOODDATA_PASSWORD=your-secure-password
GOODDATA_PROJECT_ID=your-project-id

# Optional: Custom domain configuration
GOODDATA_CUSTOM_DOMAIN=analytics.yourcompany.com

# Token storage configuration
GOODDATA_TOKEN_STORAGE=database  # Options: database, redis, session
GOODDATA_TOKEN_ENCRYPTION_KEY=your-32-character-encryption-key
```

### Database Schema for Token Storage

If using database storage for tokens, execute the following migration:

```sql
-- GoodData authentication tokens table
CREATE TABLE IF NOT EXISTS `gooddata_tokens` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` VARCHAR(255) NOT NULL,
    `sst_token` TEXT NOT NULL,
    `tt_token` TEXT NULL,
    `project_id` VARCHAR(100) NOT NULL,
    `issued_at` DATETIME NOT NULL,
    `expires_at` DATETIME NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_user_project` (`user_id`, `project_id`),
    INDEX `idx_expires_at` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Token refresh log for auditing
CREATE TABLE IF NOT EXISTS `gooddata_token_log` (
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` VARCHAR(255) NOT NULL,
    `action` ENUM('login', 'refresh', 'logout', 'expire') NOT NULL,
    `ip_address` VARCHAR(45) NULL,
    `user_agent` VARCHAR(255) NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_user_action` (`user_id`, `action`),
    INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Multi-Project Configuration

For organizations with multiple GoodData projects, configure project mappings:

```php
<?php
// application/config/gooddata_projects.php

$config['gooddata_projects'] = [
    'sales' => [
        'project_id' => 'sales-project-id',
        'display_name' => 'Sales Analytics',
        'allowed_roles' => ['admin', 'sales_manager', 'sales_rep'],
    ],
    'marketing' => [
        'project_id' => 'marketing-project-id',
        'display_name' => 'Marketing Analytics',
        'allowed_roles' => ['admin', 'marketing_manager'],
    ],
    'finance' => [
        'project_id' => 'finance-project-id',
        'display_name' => 'Financial Analytics',
        'allowed_roles' => ['admin', 'cfo', 'finance_analyst'],
    ],
];
```

---

## Authentication Flow

### Overview of GoodData Authentication

GoodData uses a two-token authentication system for secure API access:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    GoodData Authentication Flow                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐    1. Login Request     ┌──────────────┐                 │
│  │  Client  │ ──────────────────────► │   Gateway    │                 │
│  │          │                         │   Service    │                 │
│  └──────────┘                         └──────┬───────┘                 │
│       ▲                                      │                          │
│       │                          2. Authenticate                        │
│       │                                      ▼                          │
│       │                               ┌──────────────┐                 │
│       │                               │   GoodData   │                 │
│       │                               │     API      │                 │
│       │                               └──────┬───────┘                 │
│       │                                      │                          │
│       │                          3. Return SST Token                    │
│       │                                      ▼                          │
│       │                               ┌──────────────┐                 │
│       │                               │ Token Store  │                 │
│       │       4. Return Session       │  (DB/Redis)  │                 │
│       └────────────────────────────── └──────────────┘                 │
│                                                                         │
│  ┌──────────┐    5. API Request       ┌──────────────┐                 │
│  │  Client  │ ──────────────────────► │   Gateway    │                 │
│  │ (+ Token)│                         │   Service    │                 │
│  └──────────┘                         └──────┬───────┘                 │
│       ▲                                      │                          │
│       │                          6. Exchange SST → TT                   │
│       │                                      ▼                          │
│       │                               ┌──────────────┐                 │
│       │       7. Analytics Data       │   GoodData   │                 │
│       └────────────────────────────── │     API      │                 │
│                                       └──────────────┘                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Token Types Explained

| Token Type | Full Name | Purpose | Lifetime | Storage |
|------------|-----------|---------|----------|---------|
| SST | Super Secure Token | Long-lived session token for authentication | Hours to days | Database/Redis |
| TT | Temporary Token | Short-lived token for individual requests | Minutes | Memory/Cache |

### Step-by-Step Authentication Process

#### Step 1: Initial Login

The client initiates authentication by providing GoodData credentials:

```php
<?php
// Client request to gateway
POST /api/v1/gooddata/auth/login
Content-Type: application/json

{
    "username": "user@company.com",
    "password": "secure-password",
    "project_id": "optional-project-id"
}
```

#### Step 2: Gateway Authenticates with GoodData

The gateway service validates credentials against GoodData API:

```php
<?php
// Internal gateway process
class GoodData_auth_lib {
    
    public function authenticate($username, $password) {
        $response = $this->http_client->post(
            $this->config['api_endpoint'] . '/gdc/account/login',
            [
                'postUserLogin' => [
                    'login' => $username,
                    'password' => $password,
                    'remember' => 1,
                    'verify_level' => 2
                ]
            ]
        );
        
        return $this->extract_sst_token($response);
    }
}
```

#### Step 3: Token Storage and Session Creation

Upon successful authentication, the SST token is securely stored:

```php
<?php
// Token storage process
$token_data = [
    'user_id' => $user_id,
    'sst_token' => $this->encrypt($sst_token),
    'project_id' => $project_id,
    'issued_at' => date('Y-m-d H:i:s'),
    'expires_at' => date('Y-m-d H:i:s', time() + $this->config['token_ttl'])
];

$this->token_model->store($token_data);
```

#### Step 4: Subsequent API Requests

For subsequent requests, the gateway exchanges SST for TT:

```php
<?php
// TT token exchange
public function get_temporary_token($sst_token) {
    $response = $this->http_client->get(
        $this->config['api_endpoint'] . '/gdc/account/token',
        [],
        ['headers' => ['X-GDC-AuthSST' => $sst_token]]
    );
    
    return $response['userToken']['token'];
}
```

---

## Code Examples

### Basic Authentication Implementation

#### Authentication Library

```php
<?php
defined('BASEPATH') OR exit('No direct script access allowed');

/**
 * GoodData Authentication Library
 * 
 * Handles all GoodData authentication operations including
 * login, token management, and session handling.
 * 
 * @package     Platform Service Gateway
 * @subpackage  Libraries
 * @category    Authentication
 */
class Gooddata_auth {
    
    protected $CI;
    protected $config;
    protected $http_client;
    protected $cache;
    
    /**
     * Constructor
     */
    public function __construct($params = []) {
        $this->CI =& get_instance();
        $this->CI->load->config('gooddata');
        $this->config = $this->CI->config->item('gooddata');
        
        $this->CI->load->library('Http_client');
        $this->http_client = $this->CI->http_client;
        
        $this->CI->load->driver('cache', ['adapter' => $this->config['cache_driver']]);
        $this->cache = $this->CI->cache;
    }
    
    /**
     * Authenticate user with GoodData
     * 
     * @param string $username GoodData username/email
     * @param string $password User password
     * @param string $project_id Optional project ID
     * @return array Authentication result with tokens
     * @throws Exception On authentication failure
     */
    public function login($username, $password, $project_id = null) {
        // Validate inputs
        if (empty($username) || empty($password)) {
            throw new InvalidArgumentException('Username and password are required');
        }
        
        // Prepare login payload
        $payload = [
            'postUserLogin' => [
                'login' => $username,
                'password' => $password,
                'remember' => 1,
                'verify_level' => 2
            ]
        ];
        
        try {
            // Make authentication request
            $response = $this->http_client->request(
                'POST',
                $this->config['api_endpoint'] . '/gdc/account/login',
                [
                    'json' => $payload,
                    'timeout' => $this->config['timeout'],
                    'verify' => $this->config['verify_ssl']
                ]
            );
            
            // Extract SST token from response cookies
            $sst_token = $this->extract_sst_from_response($response);
            
            if (empty($sst_token)) {
                throw new RuntimeException('Failed to obtain SST token');
            }
            
            // Get user profile
            $profile = $this->get_user_profile($sst_token);
            
            // Store token
            $token_id = $this->store_token([
                'user_id' => $profile['accountSetting']['login'],
                'sst_token' => $sst_token,
                'project_id' => $project_id ?: $this->config['project_id'],
                'profile' => $profile
            ]);
            
            // Log successful login
            $this->log_auth_action($profile['accountSetting']['login'], 'login');
            
            return [
                'success' => true,
                'token_id' => $token_id,
                'user' => [
                    'email' => $profile['accountSetting']['login'],
                    'name' => $profile['accountSetting']['firstName'] . ' ' . 
                              $profile['accountSetting']['lastName'],
                    'timezone' => $profile['accountSetting']['timezone'] ?? 'UTC'
                ],
                'expires_at' => date('c', time() + $this->config['token_ttl'])
            ];
            
        } catch (Exception $e) {
            $this->CI->load->library('logger');
            $this->CI->logger->error('GoodData authentication failed', [
                'username' => $username,
                'error' => $e->getMessage()
            ]);
            
            throw new RuntimeException('Authentication failed: ' . $e->getMessage());
        }
    }
    
    /**
     * Get temporary token for API requests
     * 
     * @param string $token_id Stored token ID
     * @return string Temporary token
     */
    public function get_tt_token($token_id) {
        // Check cache first
        $cache_key = $this->config['cache_prefix'] . 'tt_' . $token_id;
        $cached_tt = $this->cache->get($cache_key);
        
        if ($cached_tt !== false) {
            return $cached_tt;
        }
        
        // Get SST from storage
        $token_data = $this->get_stored_token($token_id);
        
        if (empty($token_data) || $this->is_token_expired($token_data)) {
            throw new RuntimeException('Token expired or invalid');
        }
        
        // Exchange SST for TT
        $response = $this->http_client->request(
            'GET',
            $this->config['api_endpoint'] . '/gdc/account/token',
            [
                'headers' => [
                    'X-GDC-AuthSST' => $this->decrypt($token_data['sst_token'])
                ]
            ]
        );
        
        $tt_token = $response['userToken']['token'];
        
        // Cache TT token (shorter TTL)
        $this->cache->save($cache_key, $tt_token, 300); // 5 minutes
        
        return $tt_token;
    }
    
    /**
     * Logout and invalidate tokens
     * 
     * @param string $token_id Token to invalidate
     * @return bool Success status
     */
    public function logout($token_id) {
        $token_data = $this->get_stored_token($token_id);
        
        if (!empty($token_data)) {
            try {
                // Invalidate on GoodData side
                $this->http_client->request(
                    'DELETE',
                    $this->config['api_endpoint'] . '/gdc/account/login',
                    [
                        'headers' => [
                            'X-GDC-AuthSST' => $this->decrypt($token_data['sst_token'])
                        ]
                    ]
                );
            } catch (Exception $e) {
                // Log but continue with local cleanup
                log_message('warning', 'Failed to logout from GoodData: ' . $e->getMessage());
            }
            
            // Remove from local storage
            $this->delete_stored_token($token_id);
            
            // Clear cache
            $this->cache->delete($this->config['cache_prefix'] . 'tt_' . $token_id);
            
            // Log logout
            $this->log_auth_action($token_data['user_id'], 'logout');
        }
        
        return true;
    }
    
    /**
     * Refresh token before expiration
     * 
     * @param string $token_id Token to refresh
     * @return array New token data
     */
    public function refresh_token($token_id) {
        $token_data = $this->get_stored_token($token_id);
        
        if (empty($token_data)) {
            throw new RuntimeException('Token not found');
        }
        
        $sst_token = $this->decrypt($token_data['sst_token']);
        
        // Validate SST is still valid
        try {
            $response = $this->http_client->request(
                'GET',
                $this->config['api_endpoint'] . '/gdc/account/token',
                [
                    'headers' => ['X-GDC-AuthSST' => $sst_token]
                ]
            );
            
            // Update expiration
            $this->update_token_expiration($token_id);
            
            $this->log_auth_action($token_data['user_id'], 'refresh');
            
            return [
                'success' => true,
                'expires_at' => date('c', time() + $this->config['token_ttl'])
            ];
            
        } catch (Exception $e) {
            throw new RuntimeException('Token refresh failed: ' . $e->getMessage());
        }
    }
    
    /**
     * Extract SST token from response
     */
    protected function extract_sst_from_response($response) {
        // SST is typically in Set-Cookie header or response body
        if (isset($response['userLogin']['token'])) {
            return $response['userLogin']['token'];
        }
        
        // Check cookies if available
        $cookies = $this->http_client->get_response_cookies();
        if (isset($cookies['GDCAuthSST'])) {
            return $cookies['GDCAuthSST'];
        }
        
        return null;
    }
    
    /**
     * Get user profile from GoodData
     */
    protected function get_user_profile($sst_token) {
        $response = $this->http_client->request(
            'GET',
            $this->config['api_endpoint'] . '/gdc/account/profile/current',
            [
                'headers' => ['X-GDC-AuthSST' => $sst_token]
            ]
        );
        
        return $response;
    }
    
    /**
     * Encrypt token for storage
     */
    protected function encrypt($token) {
        $key = getenv('GOODDATA_TOKEN_ENCRYPTION_KEY');
        $iv = openssl_random_pseudo_bytes(16);
        $encrypted = openssl_encrypt($token, 'AES-256-CBC', $key, 0, $iv);
        return base64_encode($iv . $encrypted);
    }
    
    /**
     * Decrypt stored token
     */
    protected function decrypt($encrypted_token) {
        $key = getenv('GOODDATA_TOKEN_ENCRYPTION_KEY');
        $data = base64_decode($encrypted_token);
        $iv = substr($data, 0, 16);
        $encrypted = substr($data, 16);
        return openssl_decrypt($encrypted, 'AES-256-CBC', $key, 0, $iv);
    }
}
```

### Controller Implementation

```php
<?php
defined('BASEPATH') OR exit('No direct script access allowed');

/**
 * GoodData Authentication Controller
 * 
 * RESTful API endpoints for GoodData authentication
 */
class Gooddata_auth_controller extends REST_Controller {
    
    public function __construct() {
        parent::__construct();
        $this->load->library('gooddata_auth');
    }
    
    /**
     * POST /api/v1/gooddata/auth/login
     * 
     * Authenticate with GoodData
     */
    public function login_post() {
        // Validate request
        $username = $this->post('username');
        $password = $this->post('password');
        $project_id = $this->post('project_id');
        
        if (empty($username) || empty($password)) {
            return $this->response([
                'status' => false,
                'error' => 'Username and password are required'
            ], REST_Controller::HTTP_BAD_REQUEST);
        }
        
        try {
            $result = $this->gooddata_auth->login($username, $password, $project_id);
            
            return $this->response([
                'status' => true,
                'data' => $result
            ], REST_Controller::HTTP_OK);
            
        } catch (Exception $e) {
            return $this->response([
                'status' => false,
                'error' => $e->getMessage()
            ], REST_Controller::HTTP_UNAUTHORIZED);
        }
    }
    
    /**
     * POST /api/v1/gooddata/auth/logout
     * 
     * Logout and invalidate token
     */
    public function logout_post() {
        $token_id = $this->get_token_from_header();
        
        if (empty($token_id)) {
            return $this->response([
                'status' => false,
                'error' => 'Authorization token required'
            ], REST_Controller::HTTP_UNAUTHORIZED);
        }
        
        $this->gooddata_auth->logout($token_id);
        
        return $this->response([
            'status' => true,
            'message' => 'Successfully logged out'
        ], REST_Controller::HTTP_OK);
    }
    
    /**
     * POST /api/v1/gooddata/auth/refresh
     * 
     * Refresh authentication token
     */
    public function refresh_post() {
        $token_id = $this->get_token_from_header();
        
        try {
            $result = $this->gooddata_auth->refresh_token($token_id);
            
            return $this->response([
                'status' => true,
                'data' => $result
            ], REST_Controller::HTTP_OK);
            
        } catch (Exception $e) {
            return $this->response([
                'status' => false,
                'error' => $e->getMessage()
            ], REST_Controller::HTTP_UNAUTHORIZED);
        }
    }
    
    /**
     * GET /api/v1/gooddata/auth/validate
     * 
     * Validate current token
     */
    public function validate_get() {
        $token_id = $this->get_token_from_header();
        
        try {
            $tt_token = $this->gooddata_auth->get_tt_token($token_id);
            
            return $this->response([
                'status' => true,
                'valid' => true
            ], REST_Controller::HTTP_OK);
            
        } catch (Exception $e) {
            return $this->response([
                'status' => true,
                'valid' => false,
                'reason' => $e->getMessage()
            ], REST_Controller::HTTP_OK);
        }
    }
    
    /**
     * Extract token from Authorization header
     */
    protected function get_token_from_header() {
        $auth_header = $this->input->get_request_header('Authorization');
        
        if (preg_match('/Bearer\s+(.+)$/i', $auth_header, $matches)) {
            return $matches[1];
        }
        
        return null;
    }
}
```

### Client Usage Examples

#### JavaScript/Node.js Example

```javascript
// GoodData Authentication Client
class GoodDataAuthClient {
    constructor(gatewayUrl) {
        this.gatewayUrl = gatewayUrl;
        this.token = null;
    }
    
    async login(username, password, projectId = null) {
        const response = await fetch(`${this.gatewayUrl}/api/v1/gooddata/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                password,
                project_id: projectId
            })
        });
        
        const data = await response.json();
        
        if (data.status) {
            this.token = data.data.token_id;
            return data.data;
        }
        
        throw new Error(data.error);
    }
    
    async logout() {
        if (!this.token) return;
        
        await fetch(`${this.gatewayUrl}/api/v1/gooddata/auth/logout`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`
            }
        });
        
        this.token = null;
    }
    
    async executeReport(reportUri) {
        if (!this.token) {
            throw new Error('Not authenticated');
        }
        
        const response = await fetch(`${this.gatewayUrl}/api/v1/gooddata/reports/execute`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ report_uri: reportUri })
        });
        
        return response.json();
    }
}

// Usage
const client = new GoodDataAuthClient('https://gateway.example.com');

try {
    const auth = await client.login('user@company.com', 'password');
    console.log('Authenticated:', auth.user.name);
    
    const report = await client.executeReport('/gdc/md/project/obj/123');
    console.log('Report data:', report);
    
    await client.logout();
} catch (error) {
    console.error('Error:', error.message);
}
```

#### cURL Examples

```bash
# Login to GoodData
curl -X POST https://gateway.example.com/api/v1/gooddata/auth/login \
    -H "Content-Type: application/json" \
    -d '{
        "username": "user@company.com",
        "password": "your-password",
        "project_id": "optional-project-id"
    }'

# Response:
# {
#     "status": true,
#     "data": {
#         "success": true,
#         "token_id": "abc123xyz789",
#         "user": {
#             "email": "user@company.com",
#             "name": "John Doe",
#             "timezone": "America/New_York"
#         },
#         "expires_at": "2024-01-15T12:00:00+00:00"
#     }
# }

# Validate token
curl -X GET https://gateway.example.com/api/v1/gooddata/auth/validate \
    -H "Authorization: Bearer abc123xyz789"

# Refresh token
curl -X POST https://gateway.example.com/api/v1/gooddata/auth/refresh \
    -H "Authorization: Bearer abc123xyz789"

# Logout
curl -X POST https://gateway.example.com/api/v1/gooddata/auth/logout \
    -H "Authorization: Bearer abc123xyz789"
```

---

## Troubleshooting

### Common Issues and Solutions

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| `Authentication failed: 401` | Invalid credentials | Verify username and password are correct |
| `Token expired` | SST token has exceeded TTL | Implement automatic token refresh |
| `SSL certificate error` | Invalid or missing CA certificates | Set `verify_ssl` to false for testing, or provide valid CA bundle |
| `Connection timeout` | Network issues or firewall blocking | Check network connectivity to GoodData endpoints |
| `Project access denied` | User lacks project permissions | Verify user has access in GoodData admin panel |

### Debug Mode

Enable detailed logging for troubleshooting:

```php
// application/config/gooddata.php
$config['gooddata']['log_level'] = 'debug';
$config['gooddata']['log_requests'] = true;
```

### Health Check Endpoint

```php
// GET /api/v1/gooddata/health
public function health_get() {
    $checks = [
        'config' => $this->check_configuration(),
        'connectivity' => $this->check_gooddata_connectivity(),
        'database' => $this->check_token_storage(),
        'cache' => $this->check_cache_driver()
    ];
    
    $healthy = !in_array(false, array_column($checks, 'status'));
    
    return $this->response([
        'healthy' => $healthy,
        'checks' => $checks
    ], $healthy ? REST_Controller::HTTP_OK : REST_Controller::HTTP_SERVICE_UNAVAILABLE);
}
```

---

## Security Best Practices

1. **Always use HTTPS** for all GoodData API communications
2. **Encrypt tokens** before storing in database
3. **Implement rate limiting** on authentication endpoints
4. **Use environment variables** for sensitive configuration
5. **Enable audit logging** for all authentication events
6. **Set appropriate token TTLs** based on security requirements
7. **Implement IP whitelisting** where possible
8. **Regularly rotate encryption keys** used for token storage

---

## Related Documentation

- [OAuth Authentication Setup](./oauth-configuration.md)
- [LDAP Authentication](./ldap-authentication.md)
- [API Authentication Overview](./api-authentication.md)
- [Security Configuration](./security-configuration.md)