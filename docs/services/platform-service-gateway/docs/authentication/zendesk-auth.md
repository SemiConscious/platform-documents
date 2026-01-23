# Zendesk Authentication

## Overview

This document provides comprehensive guidance for configuring and implementing authentication with Zendesk through the Platform Service Gateway. The gateway supports multiple authentication methods for Zendesk integration, including API token-based authentication and OAuth 2.0, enabling secure access to Zendesk's ticketing, user management, and support platform APIs.

Zendesk authentication is a critical component for organizations that need to integrate their support workflows with other CRM platforms through the unified gateway interface. This documentation covers the complete setup process, from obtaining credentials to implementing authentication in your applications.

## Prerequisites

Before configuring Zendesk authentication, ensure you have the following requirements in place:

### Zendesk Account Requirements

1. **Zendesk Account Access**: You must have administrator or agent access to a Zendesk account with API access enabled.

2. **Zendesk Subdomain**: Know your Zendesk subdomain (e.g., `yourcompany` in `yourcompany.zendesk.com`).

3. **API Access Permissions**: Ensure your account has the necessary permissions to create API tokens or OAuth applications.

### Platform Service Gateway Requirements

1. **Gateway Installation**: The platform-service-gateway must be properly installed and running. Verify with:

```bash
docker ps | grep platform-service-gateway
```

2. **Configuration File Access**: Ensure you have access to modify configuration files in the gateway's `application/config/` directory.

3. **Required PHP Extensions**: Verify the following extensions are enabled:

```bash
php -m | grep -E "(curl|json|openssl)"
```

4. **Composer Dependencies**: Ensure all dependencies are installed:

```bash
composer install --no-dev
```

### Environment Variables

The following configuration variables must be set in your environment or configuration files:

| Variable | Description | Required |
|----------|-------------|----------|
| `ZENDESK_SUBDOMAIN` | Your Zendesk subdomain | Yes |
| `ZENDESK_AUTH_METHOD` | Authentication method (`token` or `oauth`) | Yes |
| `ZENDESK_API_TOKEN` | API token for token-based auth | Conditional |
| `ZENDESK_OAUTH_CLIENT_ID` | OAuth application client ID | Conditional |
| `ZENDESK_OAUTH_CLIENT_SECRET` | OAuth application client secret | Conditional |
| `ZENDESK_OAUTH_REDIRECT_URI` | OAuth callback URL | Conditional |

## API Token Setup

API token authentication is the simplest method to configure and is recommended for server-to-server integrations where user context is not required.

### Step 1: Generate an API Token in Zendesk

1. Log in to your Zendesk account as an administrator.
2. Navigate to **Admin Center** → **Apps and integrations** → **Zendesk API**.
3. Click on the **Settings** tab.
4. Enable **Token Access** if not already enabled.
5. Click **Add API token**.
6. Provide a description (e.g., "Platform Service Gateway Integration").
7. Click **Copy** to save the token securely—it will only be displayed once.

### Step 2: Configure the Gateway

Create or update the Zendesk configuration file:

```php
<?php
// application/config/zendesk.php

defined('BASEPATH') OR exit('No direct script access allowed');

$config['zendesk'] = [
    // Zendesk subdomain (without .zendesk.com)
    'subdomain' => getenv('ZENDESK_SUBDOMAIN') ?: 'your-subdomain',
    
    // Authentication method: 'token' or 'oauth'
    'auth_method' => 'token',
    
    // API Token Authentication Settings
    'token_auth' => [
        'email' => getenv('ZENDESK_EMAIL') ?: 'admin@yourcompany.com',
        'api_token' => getenv('ZENDESK_API_TOKEN') ?: '',
    ],
    
    // API Base URL (automatically constructed)
    'api_base_url' => 'https://' . (getenv('ZENDESK_SUBDOMAIN') ?: 'your-subdomain') . '.zendesk.com/api/v2',
    
    // Request timeout in seconds
    'timeout' => 30,
    
    // Enable request logging
    'debug' => getenv('ZENDESK_DEBUG') === 'true',
];
```

### Step 3: Set Environment Variables

For Docker deployments, add to your `docker-compose.yml`:

```yaml
services:
  platform-service-gateway:
    environment:
      - ZENDESK_SUBDOMAIN=yourcompany
      - ZENDESK_AUTH_METHOD=token
      - ZENDESK_EMAIL=admin@yourcompany.com
      - ZENDESK_API_TOKEN=your_api_token_here
      - ZENDESK_DEBUG=false
```

For non-Docker deployments, create a `.env` file:

```bash
ZENDESK_SUBDOMAIN=yourcompany
ZENDESK_AUTH_METHOD=token
ZENDESK_EMAIL=admin@yourcompany.com
ZENDESK_API_TOKEN=your_api_token_here
ZENDESK_DEBUG=false
```

### Step 4: Verify Token Authentication

Test the configuration using the gateway's health check endpoint:

```bash
curl -X GET "http://localhost:8080/api/zendesk/health" \
  -H "Content-Type: application/json" \
  -H "X-Gateway-Auth: your_gateway_api_key"
```

Expected successful response:

```json
{
  "status": "success",
  "provider": "zendesk",
  "auth_method": "token",
  "connected": true,
  "subdomain": "yourcompany",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## OAuth Configuration

OAuth 2.0 authentication is recommended when you need to access Zendesk on behalf of specific users or when building applications that require user authorization flows.

### Step 1: Register an OAuth Application in Zendesk

1. Log in to your Zendesk account as an administrator.
2. Navigate to **Admin Center** → **Apps and integrations** → **Zendesk API** → **OAuth Clients**.
3. Click **Add OAuth client**.
4. Fill in the application details:
   - **Client Name**: Platform Service Gateway
   - **Description**: Integration gateway for CRM platforms
   - **Company**: Your company name
   - **Logo**: Upload your application logo (optional)
   - **Unique Identifier**: `platform-service-gateway` (auto-generated if left blank)
   - **Redirect URLs**: Add your callback URL(s):
     ```
     https://your-gateway-domain.com/api/zendesk/oauth/callback
     http://localhost:8080/api/zendesk/oauth/callback (for development)
     ```
5. Click **Save**.
6. Note the **Client ID** and **Client Secret** displayed.

### Step 2: Configure OAuth in the Gateway

Update the configuration file:

```php
<?php
// application/config/zendesk.php

defined('BASEPATH') OR exit('No direct script access allowed');

$config['zendesk'] = [
    'subdomain' => getenv('ZENDESK_SUBDOMAIN') ?: 'your-subdomain',
    'auth_method' => 'oauth',
    
    // OAuth 2.0 Settings
    'oauth' => [
        'client_id' => getenv('ZENDESK_OAUTH_CLIENT_ID') ?: '',
        'client_secret' => getenv('ZENDESK_OAUTH_CLIENT_SECRET') ?: '',
        'redirect_uri' => getenv('ZENDESK_OAUTH_REDIRECT_URI') ?: 'https://your-gateway-domain.com/api/zendesk/oauth/callback',
        'scope' => 'read write',
        'authorization_url' => 'https://' . (getenv('ZENDESK_SUBDOMAIN') ?: 'your-subdomain') . '.zendesk.com/oauth/authorizations/new',
        'token_url' => 'https://' . (getenv('ZENDESK_SUBDOMAIN') ?: 'your-subdomain') . '.zendesk.com/oauth/tokens',
    ],
    
    // Token storage configuration
    'token_storage' => [
        'driver' => 'database', // Options: 'database', 'redis', 'file'
        'table' => 'oauth_tokens',
        'encryption' => true,
    ],
    
    'api_base_url' => 'https://' . (getenv('ZENDESK_SUBDOMAIN') ?: 'your-subdomain') . '.zendesk.com/api/v2',
    'timeout' => 30,
    'debug' => getenv('ZENDESK_DEBUG') === 'true',
];
```

### Step 3: Database Schema for Token Storage

If using database token storage, create the required table:

```sql
CREATE TABLE oauth_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    provider VARCHAR(50) NOT NULL DEFAULT 'zendesk',
    user_identifier VARCHAR(255) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at DATETIME,
    scope VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_provider_user (provider, user_identifier),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Step 4: OAuth Flow Implementation

The gateway handles the OAuth flow through dedicated endpoints. Here's the complete flow:

#### Initiating Authorization

```bash
# Redirect users to this endpoint to start OAuth flow
curl -X GET "http://localhost:8080/api/zendesk/oauth/authorize?state=unique_state_token"
```

This redirects to Zendesk's authorization page where users grant access.

#### Handling the Callback

The gateway automatically handles the callback at `/api/zendesk/oauth/callback`. The callback controller:

```php
<?php
// application/controllers/api/zendesk/Oauth.php

defined('BASEPATH') OR exit('No direct script access allowed');

class Oauth extends CI_Controller {
    
    public function __construct() {
        parent::__construct();
        $this->load->config('zendesk');
        $this->load->library('zendesk_oauth');
    }
    
    public function authorize() {
        $state = $this->input->get('state') ?: bin2hex(random_bytes(16));
        
        $params = [
            'response_type' => 'code',
            'client_id' => $this->config->item('zendesk')['oauth']['client_id'],
            'redirect_uri' => $this->config->item('zendesk')['oauth']['redirect_uri'],
            'scope' => $this->config->item('zendesk')['oauth']['scope'],
            'state' => $state,
        ];
        
        // Store state for validation
        $this->session->set_userdata('oauth_state', $state);
        
        $auth_url = $this->config->item('zendesk')['oauth']['authorization_url'] . '?' . http_build_query($params);
        redirect($auth_url);
    }
    
    public function callback() {
        $code = $this->input->get('code');
        $state = $this->input->get('state');
        
        // Validate state
        if ($state !== $this->session->userdata('oauth_state')) {
            $this->output
                ->set_status_header(400)
                ->set_content_type('application/json')
                ->set_output(json_encode(['error' => 'Invalid state parameter']));
            return;
        }
        
        try {
            $tokens = $this->zendesk_oauth->exchange_code($code);
            
            // Store tokens securely
            $this->zendesk_oauth->store_tokens($tokens);
            
            $this->output
                ->set_content_type('application/json')
                ->set_output(json_encode([
                    'status' => 'success',
                    'message' => 'Authorization successful',
                    'expires_in' => $tokens['expires_in'] ?? null,
                ]));
                
        } catch (Exception $e) {
            log_message('error', 'Zendesk OAuth callback error: ' . $e->getMessage());
            
            $this->output
                ->set_status_header(500)
                ->set_content_type('application/json')
                ->set_output(json_encode(['error' => 'Token exchange failed']));
        }
    }
}
```

## Code Examples

### Basic API Token Authentication

```php
<?php
// Example: Making authenticated requests to Zendesk

class Zendesk_client {
    
    private $config;
    private $ci;
    
    public function __construct() {
        $this->ci =& get_instance();
        $this->ci->load->config('zendesk');
        $this->config = $this->ci->config->item('zendesk');
    }
    
    /**
     * Make an authenticated request to Zendesk API
     */
    public function request($endpoint, $method = 'GET', $data = null) {
        $url = $this->config['api_base_url'] . '/' . ltrim($endpoint, '/');
        
        $headers = [
            'Content-Type: application/json',
            'Accept: application/json',
        ];
        
        // Build authentication header based on method
        if ($this->config['auth_method'] === 'token') {
            $auth = base64_encode(
                $this->config['token_auth']['email'] . '/token:' . 
                $this->config['token_auth']['api_token']
            );
            $headers[] = 'Authorization: Basic ' . $auth;
        } else {
            $access_token = $this->get_oauth_token();
            $headers[] = 'Authorization: Bearer ' . $access_token;
        }
        
        $ch = curl_init();
        curl_setopt_array($ch, [
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER => $headers,
            CURLOPT_TIMEOUT => $this->config['timeout'],
            CURLOPT_CUSTOMREQUEST => $method,
        ]);
        
        if ($data && in_array($method, ['POST', 'PUT', 'PATCH'])) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }
        
        $response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);
        
        if ($error) {
            throw new Exception("Zendesk API request failed: $error");
        }
        
        return [
            'status_code' => $http_code,
            'data' => json_decode($response, true),
        ];
    }
    
    /**
     * Get tickets with pagination
     */
    public function get_tickets($page = 1, $per_page = 100) {
        return $this->request("tickets.json?page=$page&per_page=$per_page");
    }
    
    /**
     * Create a new ticket
     */
    public function create_ticket($subject, $description, $requester_email, $priority = 'normal') {
        $ticket_data = [
            'ticket' => [
                'subject' => $subject,
                'comment' => ['body' => $description],
                'requester' => ['email' => $requester_email],
                'priority' => $priority,
            ]
        ];
        
        return $this->request('tickets.json', 'POST', $ticket_data);
    }
    
    /**
     * Get user information
     */
    public function get_user($user_id) {
        return $this->request("users/$user_id.json");
    }
    
    private function get_oauth_token() {
        // Retrieve stored OAuth token
        $this->ci->load->model('oauth_token_model');
        $token = $this->ci->oauth_token_model->get_token('zendesk');
        
        if (!$token || strtotime($token['expires_at']) < time()) {
            // Token expired, attempt refresh
            $token = $this->refresh_oauth_token($token['refresh_token']);
        }
        
        return $token['access_token'];
    }
    
    private function refresh_oauth_token($refresh_token) {
        // Implementation for token refresh
        $this->ci->load->library('zendesk_oauth');
        return $this->ci->zendesk_oauth->refresh_token($refresh_token);
    }
}
```

### Using the Gateway's Unified API

```php
<?php
// Example: Using the gateway's unified interface

// Controller endpoint for Zendesk operations
class Zendesk extends CI_Controller {
    
    public function __construct() {
        parent::__construct();
        $this->load->library('zendesk_client');
        $this->load->helper('gateway_response');
    }
    
    /**
     * GET /api/zendesk/tickets
     * List tickets with optional filtering
     */
    public function tickets() {
        try {
            $page = $this->input->get('page') ?: 1;
            $status = $this->input->get('status');
            
            $result = $this->zendesk_client->get_tickets($page);
            
            // Apply status filter if provided
            if ($status && isset($result['data']['tickets'])) {
                $result['data']['tickets'] = array_filter(
                    $result['data']['tickets'],
                    fn($ticket) => $ticket['status'] === $status
                );
            }
            
            gateway_response_success($result['data']);
            
        } catch (Exception $e) {
            gateway_response_error($e->getMessage(), 500);
        }
    }
    
    /**
     * POST /api/zendesk/tickets
     * Create a new ticket
     */
    public function create_ticket() {
        try {
            $input = json_decode(file_get_contents('php://input'), true);
            
            // Validate required fields
            $required = ['subject', 'description', 'requester_email'];
            foreach ($required as $field) {
                if (empty($input[$field])) {
                    gateway_response_error("Missing required field: $field", 400);
                    return;
                }
            }
            
            $result = $this->zendesk_client->create_ticket(
                $input['subject'],
                $input['description'],
                $input['requester_email'],
                $input['priority'] ?? 'normal'
            );
            
            if ($result['status_code'] === 201) {
                gateway_response_success($result['data'], 201);
            } else {
                gateway_response_error('Failed to create ticket', $result['status_code']);
            }
            
        } catch (Exception $e) {
            gateway_response_error($e->getMessage(), 500);
        }
    }
}
```

### JavaScript/Frontend Integration

```javascript
// Example: Frontend OAuth flow integration

class ZendeskAuthClient {
    constructor(gatewayBaseUrl) {
        this.baseUrl = gatewayBaseUrl;
    }
    
    /**
     * Initiate OAuth authorization flow
     */
    initiateAuth(state = null) {
        const authState = state || this.generateState();
        sessionStorage.setItem('zendesk_oauth_state', authState);
        
        const authUrl = `${this.baseUrl}/api/zendesk/oauth/authorize?state=${authState}`;
        window.location.href = authUrl;
    }
    
    /**
     * Handle OAuth callback
     */
    async handleCallback() {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const storedState = sessionStorage.getItem('zendesk_oauth_state');
        
        if (state !== storedState) {
            throw new Error('Invalid state parameter - possible CSRF attack');
        }
        
        // The gateway handles token exchange, just verify success
        const response = await fetch(`${this.baseUrl}/api/zendesk/oauth/status`);
        const data = await response.json();
        
        if (data.status === 'success') {
            sessionStorage.removeItem('zendesk_oauth_state');
            return data;
        }
        
        throw new Error('OAuth authentication failed');
    }
    
    /**
     * Make authenticated API request through gateway
     */
    async request(endpoint, options = {}) {
        const response = await fetch(`${this.baseUrl}/api/zendesk/${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'X-Gateway-Auth': this.getGatewayToken(),
                ...options.headers,
            },
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Request failed');
        }
        
        return response.json();
    }
    
    generateState() {
        const array = new Uint8Array(16);
        crypto.getRandomValues(array);
        return Array.from(array, b => b.toString(16).padStart(2, '0')).join('');
    }
    
    getGatewayToken() {
        return localStorage.getItem('gateway_api_token');
    }
}

// Usage example
const zendeskClient = new ZendeskAuthClient('https://your-gateway.com');

// Get tickets
zendeskClient.request('tickets')
    .then(tickets => console.log(tickets))
    .catch(error => console.error(error));
```

### Error Handling and Retry Logic

```php
<?php
// Robust error handling with automatic retry

class Zendesk_request_handler {
    
    private $max_retries = 3;
    private $retry_delay = 1000; // milliseconds
    
    public function execute_with_retry($callback, $context = []) {
        $attempts = 0;
        $last_exception = null;
        
        while ($attempts < $this->max_retries) {
            try {
                return $callback();
                
            } catch (Zendesk_rate_limit_exception $e) {
                // Handle rate limiting with exponential backoff
                $wait_time = $e->getRetryAfter() ?: ($this->retry_delay * pow(2, $attempts));
                log_message('warning', "Zendesk rate limit hit, waiting {$wait_time}ms");
                usleep($wait_time * 1000);
                $attempts++;
                $last_exception = $e;
                
            } catch (Zendesk_auth_exception $e) {
                // Authentication errors should not be retried
                log_message('error', 'Zendesk authentication failed: ' . $e->getMessage());
                throw $e;
                
            } catch (Exception $e) {
                // Generic errors with standard retry
                log_message('warning', "Zendesk request failed (attempt $attempts): " . $e->getMessage());
                usleep($this->retry_delay * 1000);
                $attempts++;
                $last_exception = $e;
            }
        }
        
        throw new Exception(
            "Zendesk request failed after {$this->max_retries} attempts: " . 
            ($last_exception ? $last_exception->getMessage() : 'Unknown error')
        );
    }
}
```

## Best Practices

1. **Token Security**: Never commit API tokens or OAuth secrets to version control. Always use environment variables or secure secret management.

2. **Rate Limiting**: Implement rate limiting awareness. Zendesk has API rate limits (varies by plan), and the gateway should handle 429 responses gracefully.

3. **Token Rotation**: Regularly rotate API tokens and implement automatic OAuth token refresh.

4. **Logging**: Enable debug logging during development but disable in production to prevent credential leakage.

5. **Scope Minimization**: When using OAuth, request only the minimum required scopes for your integration.

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid credentials | Verify API token or OAuth access token |
| `403 Forbidden` | Insufficient permissions | Check account role and API access settings |
| `429 Too Many Requests` | Rate limit exceeded | Implement backoff and retry logic |
| `Connection refused` | Network/firewall issue | Verify Zendesk subdomain and network access |

---

*Last updated: Documentation generated for platform-service-gateway v1.0*