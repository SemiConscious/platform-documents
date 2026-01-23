# Microsoft Dynamics Authentication

## Overview

Microsoft Dynamics authentication in the platform-service-gateway service provides secure integration with Microsoft Dynamics CRM and Dynamics 365 platforms through OAuth 2.0 and Live ID (Microsoft Account) authentication mechanisms. This documentation covers the complete authentication setup process, including Live ID configuration, OAuth flow implementation, token management, and practical code examples for developers integrating with Microsoft Dynamics environments.

The platform-service-gateway implements a unified authentication layer that abstracts the complexity of Microsoft's authentication ecosystem while providing robust token lifecycle management, automatic refresh capabilities, and comprehensive error handling.

## Prerequisites

### System Requirements

Before configuring Microsoft Dynamics authentication, ensure your environment meets the following requirements:

| Requirement | Minimum Version | Recommended |
|-------------|-----------------|-------------|
| PHP | 7.4+ | 8.1+ |
| OpenSSL Extension | Enabled | Enabled |
| cURL Extension | Enabled | Enabled |
| JSON Extension | Enabled | Enabled |
| Composer | 2.0+ | Latest |

### Microsoft Azure Prerequisites

1. **Azure Active Directory Tenant**: You must have access to an Azure AD tenant associated with your Dynamics instance.

2. **Azure App Registration**: Register an application in Azure Portal with the following permissions:
   - `Dynamics CRM > user_impersonation`
   - `Microsoft Graph > User.Read` (optional, for user profile data)

3. **Dynamics 365 Instance**: Active Dynamics 365 or Dynamics CRM Online instance with API access enabled.

### Required Configuration Variables

The following configuration variables must be set in your environment or configuration files:

```php
// config/dynamics_auth.php

$config['dynamics'] = [
    'client_id'         => getenv('DYNAMICS_CLIENT_ID'),
    'client_secret'     => getenv('DYNAMICS_CLIENT_SECRET'),
    'tenant_id'         => getenv('DYNAMICS_TENANT_ID'),
    'resource_url'      => getenv('DYNAMICS_RESOURCE_URL'),      // e.g., https://yourorg.crm.dynamics.com
    'redirect_uri'      => getenv('DYNAMICS_REDIRECT_URI'),
    'authority_url'     => 'https://login.microsoftonline.com',
    'token_endpoint'    => '/oauth2/v2.0/token',
    'authorize_endpoint'=> '/oauth2/v2.0/authorize',
];
```

### Environment Variables

Set the following environment variables in your `.env` file or Docker configuration:

```bash
# Microsoft Dynamics Authentication
DYNAMICS_CLIENT_ID=your-azure-app-client-id
DYNAMICS_CLIENT_SECRET=your-azure-app-client-secret
DYNAMICS_TENANT_ID=your-azure-tenant-id
DYNAMICS_RESOURCE_URL=https://yourorg.crm.dynamics.com
DYNAMICS_REDIRECT_URI=https://your-gateway-url/auth/dynamics/callback
DYNAMICS_AUTH_SCOPE=https://yourorg.crm.dynamics.com/.default
```

## Live ID Configuration

### Understanding Live ID Integration

Live ID (now Microsoft Account) authentication allows users to authenticate with their personal or organizational Microsoft accounts. The platform-service-gateway supports both:

- **Organizational Accounts (Azure AD)**: Business accounts tied to an Azure AD tenant
- **Personal Microsoft Accounts**: Consumer Microsoft accounts (outlook.com, hotmail.com, etc.)

### Azure Portal App Registration

#### Step 1: Create App Registration

1. Navigate to [Azure Portal](https://portal.azure.com)
2. Go to **Azure Active Directory** > **App registrations** > **New registration**
3. Configure the application:

```
Name: Platform Service Gateway - Dynamics Integration
Supported account types: Accounts in any organizational directory and personal Microsoft accounts
Redirect URI: Web - https://your-gateway-url/auth/dynamics/callback
```

#### Step 2: Configure API Permissions

Add the following API permissions:

```
Microsoft APIs:
├── Dynamics CRM
│   └── Delegated: user_impersonation
├── Microsoft Graph
│   └── Delegated: User.Read
│   └── Delegated: offline_access
```

#### Step 3: Create Client Secret

1. Go to **Certificates & secrets** > **New client secret**
2. Set description and expiration period
3. Copy the secret value immediately (it won't be shown again)

#### Step 4: Configure Authentication Settings

In the **Authentication** section, configure:

```json
{
  "accessTokenAcceptedVersion": 2,
  "allowPublicClient": false,
  "oauth2AllowImplicitFlow": false,
  "oauth2AllowIdTokenImplicitFlow": true
}
```

### Gateway Configuration for Live ID

Configure the gateway to support Live ID authentication:

```php
// application/config/auth_providers.php

$config['auth_providers']['dynamics_liveid'] = [
    'enabled'           => TRUE,
    'provider_type'     => 'oauth2',
    'display_name'      => 'Microsoft Dynamics (Live ID)',
    'icon'              => 'dynamics-icon.svg',
    
    // OAuth Endpoints
    'authorization_url' => 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
    'token_url'         => 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
    
    // Scopes
    'scopes'            => [
        'https://yourorg.crm.dynamics.com/user_impersonation',
        'offline_access',
        'openid',
        'profile'
    ],
    
    // Response handling
    'response_type'     => 'code',
    'response_mode'     => 'query',
    
    // Token settings
    'token_storage'     => 'database',  // Options: database, redis, session
    'encrypt_tokens'    => TRUE,
];
```

## OAuth Flow

### Authorization Code Flow Overview

The platform-service-gateway implements the OAuth 2.0 Authorization Code flow for Microsoft Dynamics authentication:

```
┌──────────┐                               ┌───────────────┐
│  Client  │                               │    Gateway    │
└────┬─────┘                               └───────┬───────┘
     │                                             │
     │  1. Request Auth URL                        │
     │ ─────────────────────────────────────────> │
     │                                             │
     │  2. Redirect to Microsoft Login             │
     │ <───────────────────────────────────────── │
     │                                             │
     │           ┌─────────────────────┐           │
     │           │   Microsoft Azure   │           │
     │           │   Login Portal      │           │
     │           └──────────┬──────────┘           │
     │                      │                      │
     │  3. User Authenticates                      │
     │ ────────────────────>│                      │
     │                      │                      │
     │  4. Auth Code Redirect                      │
     │ <────────────────────│                      │
     │                      │                      │
     │  5. Exchange Code    │                      │
     │ ─────────────────────┼─────────────────────>│
     │                      │                      │
     │                      │  6. Token Request    │
     │                      │<─────────────────────│
     │                      │                      │
     │                      │  7. Access Token     │
     │                      │─────────────────────>│
     │                      │                      │
     │  8. Token Response                          │
     │ <───────────────────────────────────────── │
     │                                             │
```

### Step 1: Initiating Authentication

To start the OAuth flow, redirect users to the authorization endpoint:

```php
// application/controllers/Auth.php

class Auth extends CI_Controller {
    
    public function dynamics_login() {
        $this->load->library('dynamics_auth');
        
        // Generate state parameter for CSRF protection
        $state = bin2hex(random_bytes(32));
        $this->session->set_userdata('oauth_state', $state);
        
        // Build authorization URL
        $auth_url = $this->dynamics_auth->get_authorization_url([
            'state'         => $state,
            'prompt'        => 'consent',  // Options: login, consent, select_account
            'login_hint'    => $this->input->get('email'),  // Pre-fill email if known
        ]);
        
        redirect($auth_url);
    }
}
```

### Step 2: Handling the Callback

Process the authorization code returned by Microsoft:

```php
// application/controllers/Auth.php

public function dynamics_callback() {
    $this->load->library('dynamics_auth');
    
    // Validate state parameter
    $state = $this->input->get('state');
    $stored_state = $this->session->userdata('oauth_state');
    
    if (!$state || $state !== $stored_state) {
        log_message('error', 'OAuth state mismatch - possible CSRF attack');
        show_error('Authentication failed: Invalid state parameter', 403);
        return;
    }
    
    // Check for errors
    if ($error = $this->input->get('error')) {
        $error_description = $this->input->get('error_description');
        log_message('error', "Dynamics OAuth error: {$error} - {$error_description}");
        show_error("Authentication failed: {$error_description}", 401);
        return;
    }
    
    // Exchange authorization code for tokens
    $code = $this->input->get('code');
    
    try {
        $token_response = $this->dynamics_auth->exchange_code($code);
        
        // Store tokens securely
        $this->store_tokens($token_response);
        
        // Redirect to success page
        redirect('dashboard');
        
    } catch (DynamicsAuthException $e) {
        log_message('error', 'Token exchange failed: ' . $e->getMessage());
        show_error('Authentication failed. Please try again.', 500);
    }
}
```

### Step 3: Token Exchange Implementation

The token exchange process retrieves access and refresh tokens:

```php
// application/libraries/Dynamics_auth.php

class Dynamics_auth {
    
    protected $CI;
    protected $config;
    
    public function __construct() {
        $this->CI =& get_instance();
        $this->CI->config->load('dynamics_auth');
        $this->config = $this->CI->config->item('dynamics');
    }
    
    public function exchange_code($authorization_code) {
        $token_url = $this->config['authority_url'] . '/' . 
                     $this->config['tenant_id'] . 
                     $this->config['token_endpoint'];
        
        $params = [
            'grant_type'    => 'authorization_code',
            'client_id'     => $this->config['client_id'],
            'client_secret' => $this->config['client_secret'],
            'code'          => $authorization_code,
            'redirect_uri'  => $this->config['redirect_uri'],
            'scope'         => $this->config['resource_url'] . '/.default offline_access',
        ];
        
        $response = $this->http_post($token_url, $params);
        
        if (isset($response['error'])) {
            throw new DynamicsAuthException(
                $response['error_description'] ?? $response['error'],
                $response['error_codes'][0] ?? 0
            );
        }
        
        return [
            'access_token'  => $response['access_token'],
            'refresh_token' => $response['refresh_token'] ?? null,
            'expires_in'    => $response['expires_in'],
            'token_type'    => $response['token_type'],
            'scope'         => $response['scope'],
            'id_token'      => $response['id_token'] ?? null,
        ];
    }
    
    protected function http_post($url, $params) {
        $ch = curl_init($url);
        
        curl_setopt_array($ch, [
            CURLOPT_POST           => true,
            CURLOPT_POSTFIELDS     => http_build_query($params),
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER     => [
                'Content-Type: application/x-www-form-urlencoded',
                'Accept: application/json',
            ],
            CURLOPT_SSL_VERIFYPEER => true,
            CURLOPT_TIMEOUT        => 30,
        ]);
        
        $response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        
        if (curl_errno($ch)) {
            throw new DynamicsAuthException('HTTP request failed: ' . curl_error($ch));
        }
        
        curl_close($ch);
        
        return json_decode($response, true);
    }
}
```

## Token Refresh

### Automatic Token Refresh

The gateway implements automatic token refresh to maintain seamless API access:

```php
// application/libraries/Dynamics_token_manager.php

class Dynamics_token_manager {
    
    protected $CI;
    protected $dynamics_auth;
    protected $token_model;
    
    // Buffer time before expiration to trigger refresh (in seconds)
    const REFRESH_BUFFER = 300;  // 5 minutes
    
    public function __construct() {
        $this->CI =& get_instance();
        $this->CI->load->library('dynamics_auth');
        $this->CI->load->model('dynamics_token_model');
        
        $this->dynamics_auth = $this->CI->dynamics_auth;
        $this->token_model = $this->CI->dynamics_token_model;
    }
    
    /**
     * Get a valid access token, refreshing if necessary
     *
     * @param int $user_id The user ID to get token for
     * @return string Valid access token
     * @throws DynamicsAuthException If token cannot be obtained
     */
    public function get_valid_token($user_id) {
        $token_data = $this->token_model->get_token($user_id, 'dynamics');
        
        if (!$token_data) {
            throw new DynamicsAuthException('No token found for user', 401);
        }
        
        // Check if token needs refresh
        $expires_at = strtotime($token_data['expires_at']);
        $refresh_threshold = time() + self::REFRESH_BUFFER;
        
        if ($expires_at <= $refresh_threshold) {
            // Token is expired or about to expire
            if (empty($token_data['refresh_token'])) {
                throw new DynamicsAuthException('Token expired and no refresh token available', 401);
            }
            
            $token_data = $this->refresh_token($user_id, $token_data['refresh_token']);
        }
        
        return $token_data['access_token'];
    }
    
    /**
     * Refresh an expired access token
     *
     * @param int $user_id The user ID
     * @param string $refresh_token The refresh token
     * @return array New token data
     */
    public function refresh_token($user_id, $refresh_token) {
        try {
            $new_tokens = $this->dynamics_auth->refresh_access_token($refresh_token);
            
            // Calculate expiration time
            $expires_at = date('Y-m-d H:i:s', time() + $new_tokens['expires_in']);
            
            // Update stored tokens
            $this->token_model->update_token($user_id, 'dynamics', [
                'access_token'  => $new_tokens['access_token'],
                'refresh_token' => $new_tokens['refresh_token'] ?? $refresh_token,
                'expires_at'    => $expires_at,
                'updated_at'    => date('Y-m-d H:i:s'),
            ]);
            
            log_message('info', "Dynamics token refreshed for user {$user_id}");
            
            return [
                'access_token'  => $new_tokens['access_token'],
                'refresh_token' => $new_tokens['refresh_token'] ?? $refresh_token,
                'expires_at'    => $expires_at,
            ];
            
        } catch (DynamicsAuthException $e) {
            log_message('error', "Token refresh failed for user {$user_id}: " . $e->getMessage());
            
            // Mark token as invalid
            $this->token_model->invalidate_token($user_id, 'dynamics');
            
            throw $e;
        }
    }
}
```

### Refresh Token Implementation in Auth Library

```php
// application/libraries/Dynamics_auth.php (additional method)

public function refresh_access_token($refresh_token) {
    $token_url = $this->config['authority_url'] . '/' . 
                 $this->config['tenant_id'] . 
                 $this->config['token_endpoint'];
    
    $params = [
        'grant_type'    => 'refresh_token',
        'client_id'     => $this->config['client_id'],
        'client_secret' => $this->config['client_secret'],
        'refresh_token' => $refresh_token,
        'scope'         => $this->config['resource_url'] . '/.default offline_access',
    ];
    
    $response = $this->http_post($token_url, $params);
    
    if (isset($response['error'])) {
        // Handle specific error codes
        $error_code = $response['error_codes'][0] ?? 0;
        
        switch ($error_code) {
            case 70000:
            case 70001:
                throw new DynamicsAuthException(
                    'Refresh token has expired. User must re-authenticate.',
                    $error_code
                );
            case 65001:
                throw new DynamicsAuthException(
                    'Consent required. User must re-authorize the application.',
                    $error_code
                );
            default:
                throw new DynamicsAuthException(
                    $response['error_description'] ?? 'Token refresh failed',
                    $error_code
                );
        }
    }
    
    return $response;
}
```

### Token Storage Model

```php
// application/models/Dynamics_token_model.php

class Dynamics_token_model extends CI_Model {
    
    protected $table = 'oauth_tokens';
    protected $encryption_key;
    
    public function __construct() {
        parent::__construct();
        $this->encryption_key = $this->config->item('encryption_key');
    }
    
    /**
     * Store tokens securely in database
     */
    public function store_token($user_id, $provider, $token_data) {
        // Encrypt sensitive data
        $encrypted_access = $this->encrypt($token_data['access_token']);
        $encrypted_refresh = isset($token_data['refresh_token']) 
            ? $this->encrypt($token_data['refresh_token']) 
            : null;
        
        $data = [
            'user_id'       => $user_id,
            'provider'      => $provider,
            'access_token'  => $encrypted_access,
            'refresh_token' => $encrypted_refresh,
            'expires_at'    => $token_data['expires_at'],
            'scope'         => $token_data['scope'] ?? null,
            'created_at'    => date('Y-m-d H:i:s'),
            'updated_at'    => date('Y-m-d H:i:s'),
        ];
        
        // Use upsert logic
        $existing = $this->get_token($user_id, $provider);
        
        if ($existing) {
            $this->db->where('user_id', $user_id)
                     ->where('provider', $provider)
                     ->update($this->table, $data);
        } else {
            $this->db->insert($this->table, $data);
        }
    }
    
    /**
     * Retrieve and decrypt tokens
     */
    public function get_token($user_id, $provider) {
        $result = $this->db->where('user_id', $user_id)
                           ->where('provider', $provider)
                           ->where('is_valid', 1)
                           ->get($this->table)
                           ->row_array();
        
        if (!$result) {
            return null;
        }
        
        // Decrypt tokens
        $result['access_token'] = $this->decrypt($result['access_token']);
        if ($result['refresh_token']) {
            $result['refresh_token'] = $this->decrypt($result['refresh_token']);
        }
        
        return $result;
    }
    
    protected function encrypt($data) {
        return openssl_encrypt($data, 'AES-256-CBC', $this->encryption_key, 0, 
            substr(hash('sha256', $this->encryption_key), 0, 16));
    }
    
    protected function decrypt($data) {
        return openssl_decrypt($data, 'AES-256-CBC', $this->encryption_key, 0,
            substr(hash('sha256', $this->encryption_key), 0, 16));
    }
}
```

## Code Examples

### Complete API Request Example

```php
// application/libraries/Dynamics_api.php

class Dynamics_api {
    
    protected $CI;
    protected $token_manager;
    protected $base_url;
    
    public function __construct() {
        $this->CI =& get_instance();
        $this->CI->load->library('dynamics_token_manager');
        $this->CI->config->load('dynamics_auth');
        
        $this->token_manager = $this->CI->dynamics_token_manager;
        $this->base_url = $this->CI->config->item('dynamics')['resource_url'] . '/api/data/v9.2';
    }
    
    /**
     * Make authenticated request to Dynamics API
     */
    public function request($method, $endpoint, $data = null, $user_id = null) {
        // Get current user if not specified
        if (!$user_id) {
            $user_id = $this->CI->session->userdata('user_id');
        }
        
        // Get valid access token
        $access_token = $this->token_manager->get_valid_token($user_id);
        
        $url = $this->base_url . $endpoint;
        
        $headers = [
            'Authorization: Bearer ' . $access_token,
            'Accept: application/json',
            'OData-MaxVersion: 4.0',
            'OData-Version: 4.0',
            'Prefer: odata.include-annotations="*"',
        ];
        
        if ($data && in_array($method, ['POST', 'PATCH', 'PUT'])) {
            $headers[] = 'Content-Type: application/json';
        }
        
        $ch = curl_init($url);
        
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER     => $headers,
            CURLOPT_SSL_VERIFYPEER => true,
            CURLOPT_TIMEOUT        => 60,
        ]);
        
        switch ($method) {
            case 'POST':
                curl_setopt($ch, CURLOPT_POST, true);
                curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
                break;
            case 'PATCH':
                curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'PATCH');
                curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
                break;
            case 'PUT':
                curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'PUT');
                curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
                break;
            case 'DELETE':
                curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'DELETE');
                break;
        }
        
        $response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        
        curl_close($ch);
        
        return [
            'status_code' => $http_code,
            'body'        => json_decode($response, true),
        ];
    }
    
    /**
     * Get accounts from Dynamics
     */
    public function get_accounts($select = [], $filter = null, $top = 50) {
        $endpoint = '/accounts';
        $query_params = [];
        
        if (!empty($select)) {
            $query_params['$select'] = implode(',', $select);
        }
        
        if ($filter) {
            $query_params['$filter'] = $filter;
        }
        
        $query_params['$top'] = $top;
        
        if (!empty($query_params)) {
            $endpoint .= '?' . http_build_query($query_params);
        }
        
        return $this->request('GET', $endpoint);
    }
    
    /**
     * Create a new contact
     */
    public function create_contact($contact_data) {
        return $this->request('POST', '/contacts', $contact_data);
    }
    
    /**
     * Update an existing record
     */
    public function update_record($entity, $id, $data) {
        return $this->request('PATCH', "/{$entity}({$id})", $data);
    }
}
```

### Controller Usage Example

```php
// application/controllers/api/Dynamics.php

class Dynamics extends REST_Controller {
    
    public function __construct() {
        parent::__construct();
        $this->load->library('dynamics_api');
    }
    
    /**
     * GET /api/dynamics/accounts
     */
    public function accounts_get() {
        try {
            $select = ['name', 'accountnumber', 'telephone1', 'emailaddress1'];
            $filter = $this->get('filter');
            $top = $this->get('limit') ?? 50;
            
            $result = $this->dynamics_api->get_accounts($select, $filter, $top);
            
            if ($result['status_code'] == 200) {
                $this->response([
                    'success' => true,
                    'data'    => $result['body']['value'],
                    'count'   => count($result['body']['value']),
                ], REST_Controller::HTTP_OK);
            } else {
                $this->response([
                    'success' => false,
                    'error'   => $result['body']['error'] ?? 'Unknown error',
                ], $result['status_code']);
            }
            
        } catch (DynamicsAuthException $e) {
            if ($e->getCode() == 401) {
                $this->response([
                    'success' => false,
                    'error'   => 'Authentication required',
                    'action'  => 'reauthenticate',
                ], REST_Controller::HTTP_UNAUTHORIZED);
            } else {
                $this->response([
                    'success' => false,
                    'error'   => $e->getMessage(),
                ], REST_Controller::HTTP_INTERNAL_ERROR);
            }
        }
    }
    
    /**
     * POST /api/dynamics/contacts
     */
    public function contacts_post() {
        $contact_data = [
            'firstname'     => $this->post('first_name'),
            'lastname'      => $this->post('last_name'),
            'emailaddress1' => $this->post('email'),
            'telephone1'    => $this->post('phone'),
        ];
        
        // Validate required fields
        if (empty($contact_data['lastname'])) {
            $this->response([
                'success' => false,
                'error'   => 'Last name is required',
            ], REST_Controller::HTTP_BAD_REQUEST);
            return;
        }
        
        try {
            $result = $this->dynamics_api->create_contact($contact_data);
            
            if ($result['status_code'] == 204) {
                $this->response([
                    'success' => true,
                    'message' => 'Contact created successfully',
                ], REST_Controller::HTTP_CREATED);
            } else {
                $this->response([
                    'success' => false,
                    'error'   => $result['body']['error'] ?? 'Failed to create contact',
                ], $result['status_code']);
            }
            
        } catch (Exception $e) {
            $this->response([
                'success' => false,
                'error'   => $e->getMessage(),
            ], REST_Controller::HTTP_INTERNAL_ERROR);
        }
    }
}
```

### JavaScript Frontend Integration

```javascript
// assets/js/dynamics-auth.js

class DynamicsAuth {
    constructor(options) {
        this.gatewayUrl = options.gatewayUrl || '/api';
        this.loginEndpoint = '/auth/dynamics/login';
        this.callbackEndpoint = '/auth/dynamics/callback';
        this.tokenCheckEndpoint = '/auth/dynamics/status';
    }
    
    /**
     * Initiate OAuth login flow
     */
    login(options = {}) {
        const params = new URLSearchParams({
            redirect: options.redirect || window.location.pathname,
            prompt: options.prompt || 'select_account'
        });
        
        window.location.href = `${this.gatewayUrl}${this.loginEndpoint}?${params}`;
    }
    
    /**
     * Check authentication status
     */
    async checkAuthStatus() {
        try {
            const response = await fetch(`${this.gatewayUrl}${this.tokenCheckEndpoint}`, {
                credentials: 'include'
            });
            
            const data = await response.json();
            return data.authenticated === true;
        } catch (error) {
            console.error('Auth status check failed:', error);
            return false;
        }
    }
    
    /**
     * Make authenticated API call
     */
    async apiCall(endpoint, options = {}) {
        const response = await fetch(`${this.gatewayUrl}/dynamics${endpoint}`, {
            method: options.method || 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            body: options.body ? JSON.stringify(options.body) : undefined,
            credentials: 'include'
        });
        
        if (response.status === 401) {
            // Token expired or invalid - redirect to login
            this.login({ redirect: window.location.pathname });
            throw new Error('Authentication required');
        }
        
        return response.json();
    }
    
    /**
     * Get Dynamics accounts
     */
    async getAccounts(options = {}) {
        const params = new URLSearchParams();
        if (options.filter) params.append('filter', options.filter);
        if (options.limit) params.append('limit', options.limit);
        
        const queryString = params.toString();
        const endpoint = `/accounts${queryString ? '?' + queryString : ''}`;
        
        return this.apiCall(endpoint);
    }
}

// Usage example
const dynamicsAuth = new DynamicsAuth({
    gatewayUrl: 'https://your-gateway-url/api'
});

// Check if user is authenticated
dynamicsAuth.checkAuthStatus().then(isAuthenticated => {
    if (!isAuthenticated) {
        document.getElementById('login-btn').style.display = 'block';
    } else {
        // Load Dynamics data
        dynamicsAuth.getAccounts({ limit: 10 })
            .then(data => {
                console.log('Accounts:', data);
            })
            .catch(error => {
                console.error('Failed to load accounts:', error);
            });
    }
});
```

## Troubleshooting

### Common Issues and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `AADSTS65001` | User hasn't consented to permissions | Re-authenticate with `prompt=consent` |
| `AADSTS70001` | Application not found | Verify client_id and tenant_id |
| `AADSTS50011` | Reply URL mismatch | Update redirect_uri in Azure Portal |
| `AADSTS700024` | Client assertion invalid | Regenerate client secret |
| `invalid_grant` | Refresh token expired | User must re-authenticate |

### Debug Logging

Enable detailed logging for troubleshooting:

```php
// application/config/config.php
$config['log_threshold'] = 4;  // Enable debug logging

// In your code
log_message('debug', 'Dynamics auth request: ' . json_encode($params));
log_message('debug', 'Dynamics auth response: ' . json_encode($response));
```

## Security Best Practices

1. **Always use HTTPS** for all OAuth endpoints and API calls
2. **Encrypt tokens at rest** using strong encryption (AES-256)
3. **Implement CSRF protection** using state parameter
4. **Validate all redirect URIs** against whitelist
5. **Monitor token usage** for anomalies
6. **Implement rate limiting** on authentication endpoints
7. **Rotate client secrets** periodically
8. **Use short-lived access tokens** with refresh token rotation