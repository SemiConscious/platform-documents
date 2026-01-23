# Authentication & Authorization

## Overview

The Platform DGAPI (Disposition Gateway API) implements a robust token-based authentication system designed to secure all API endpoints handling sensitive task disposition workflows. This documentation provides comprehensive guidance on how authentication and authorization work within the platform-dgapi service, including token generation, validation, and the complete authorization flow.

### Authentication Architecture

The DGAPI authentication system consists of two primary components:

1. **DGAPIAuthToken**: A token generation and validation library responsible for creating secure, time-limited authentication tokens
2. **Authorization Library**: A middleware-style authorization layer that intercepts incoming requests and validates authentication credentials

All API endpoints in platform-dgapi require valid authentication tokens, ensuring that only authorized systems and users can access task disposition management, SMS sending, email notifications, voicemail processing, and CDR integration features.

### Security Model

The authentication system employs the following security measures:

- **Token-based authentication**: Each request must include a valid authentication token
- **Time-limited tokens**: Tokens expire after a configurable duration to minimize exposure from compromised credentials
- **Key-based signing**: Tokens are cryptographically signed using server-side keys
- **Request validation**: All incoming requests are validated against expected parameters and signatures

---

## Token Generation

### Understanding Token Structure

DGAPI authentication tokens are structured strings containing encoded information about the requesting entity, timestamp, and cryptographic signature. The token format follows this structure:

```
[base64_encoded_payload].[signature].[timestamp]
```

### Generating Tokens Programmatically

#### PHP Token Generation

```php
<?php
// Load the DGAPIAuthToken library
$this->load->library('DGAPIAuthToken');

// Configuration parameters for token generation
$tokenConfig = [
    'client_id'     => 'your_client_identifier',
    'client_secret' => 'your_client_secret_key',
    'scope'         => 'disposition:write,sms:send,email:send',
    'timestamp'     => time(),
    'expires_in'    => 3600  // Token validity in seconds
];

// Generate the authentication token
$authToken = $this->dgapiauthtoken->generate($tokenConfig);

if ($authToken === false) {
    log_message('error', 'Failed to generate DGAPI auth token');
    return false;
}

// The generated token
echo "Generated Token: " . $authToken;
```

#### Token Generation with Custom Expiry

```php
<?php
// Generate a token with extended validity for batch operations
$batchTokenConfig = [
    'client_id'     => 'batch_processor',
    'client_secret' => $this->config->item('dgapi_batch_secret'),
    'scope'         => 'cdr:process,callback:finish',
    'timestamp'     => time(),
    'expires_in'    => 7200,  // 2-hour validity for batch jobs
    'batch_mode'    => true
];

$batchToken = $this->dgapiauthtoken->generate($batchTokenConfig);
```

### Token Scopes

The DGAPI supports granular permission scopes that control access to specific functionality:

| Scope | Description | Endpoints Affected |
|-------|-------------|-------------------|
| `disposition:read` | Read task disposition data | GET endpoints |
| `disposition:write` | Create and update dispositions | POST, PUT endpoints |
| `sms:send` | Send SMS notifications | SMS-related endpoints |
| `email:send` | Send email notifications | Email-related endpoints |
| `voicemail:process` | Process voicemail notifications | Voicemail endpoints |
| `cdr:process` | Process CDR records | CDR integration endpoints |
| `callback:finish` | Handle callback finish events | Callback endpoints |
| `admin:full` | Full administrative access | All endpoints |

---

## Token Validation

### Server-Side Validation Process

When a request arrives at any DGAPI endpoint, the Authorization library performs the following validation steps:

```php
<?php
class Authorization {
    
    /**
     * Validate incoming authentication token
     * 
     * @param string $token The authentication token from request header
     * @return array|bool Decoded token data or false on failure
     */
    public function validateToken($token) {
        // Step 1: Check token format
        if (!$this->isValidTokenFormat($token)) {
            $this->setError(401, 'INVALID_TOKEN_FORMAT');
            return false;
        }
        
        // Step 2: Decode and extract components
        $tokenParts = explode('.', $token);
        if (count($tokenParts) !== 3) {
            $this->setError(401, 'MALFORMED_TOKEN');
            return false;
        }
        
        list($payload, $signature, $timestamp) = $tokenParts;
        
        // Step 3: Verify timestamp and expiration
        $decodedPayload = json_decode(base64_decode($payload), true);
        $tokenTimestamp = (int) $timestamp;
        $expiresIn = $decodedPayload['expires_in'] ?? 3600;
        
        if (time() > ($tokenTimestamp + $expiresIn)) {
            $this->setError(401, 'TOKEN_EXPIRED');
            return false;
        }
        
        // Step 4: Verify signature
        $expectedSignature = $this->generateSignature($payload, $timestamp);
        if (!hash_equals($expectedSignature, $signature)) {
            $this->setError(401, 'INVALID_SIGNATURE');
            return false;
        }
        
        // Step 5: Validate client credentials
        if (!$this->validateClientCredentials($decodedPayload)) {
            $this->setError(403, 'INVALID_CLIENT');
            return false;
        }
        
        return $decodedPayload;
    }
    
    /**
     * Generate expected signature for comparison
     */
    private function generateSignature($payload, $timestamp) {
        $secretKey = $this->CI->config->item('dgapi_signing_key');
        return hash_hmac('sha256', $payload . $timestamp, $secretKey);
    }
}
```

### Implementing Validation in Controllers

```php
<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Disposition extends CI_Controller {
    
    public function __construct() {
        parent::__construct();
        $this->load->library('Authorization');
        
        // Validate authentication on every request
        $this->authenticateRequest();
    }
    
    private function authenticateRequest() {
        // Extract token from Authorization header
        $authHeader = $this->input->get_request_header('Authorization');
        
        if (empty($authHeader)) {
            $this->sendErrorResponse(401, 'MISSING_AUTH_HEADER', 
                'Authorization header is required');
            exit;
        }
        
        // Parse Bearer token
        if (!preg_match('/^Bearer\s+(.+)$/i', $authHeader, $matches)) {
            $this->sendErrorResponse(401, 'INVALID_AUTH_FORMAT', 
                'Authorization header must use Bearer scheme');
            exit;
        }
        
        $token = $matches[1];
        $validationResult = $this->authorization->validateToken($token);
        
        if ($validationResult === false) {
            $error = $this->authorization->getLastError();
            $this->sendErrorResponse($error['code'], $error['type'], $error['message']);
            exit;
        }
        
        // Store validated token data for use in controller methods
        $this->tokenData = $validationResult;
    }
    
    /**
     * Check if current token has required scope
     */
    protected function requireScope($requiredScope) {
        $tokenScopes = explode(',', $this->tokenData['scope'] ?? '');
        
        if (!in_array($requiredScope, $tokenScopes) && 
            !in_array('admin:full', $tokenScopes)) {
            $this->sendErrorResponse(403, 'INSUFFICIENT_SCOPE', 
                "This operation requires the '{$requiredScope}' scope");
            exit;
        }
    }
}
```

---

## Authorization Flow

### Complete Request Lifecycle

The following diagram illustrates the complete authentication and authorization flow for DGAPI requests:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Client System  │     │   DGAPI Server  │     │   Auth Service  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │ 1. Request Token      │                       │
         │ (client_id, secret)   │                       │
         ├──────────────────────►│                       │
         │                       │                       │
         │                       │ 2. Validate Client    │
         │                       ├──────────────────────►│
         │                       │                       │
         │                       │ 3. Client Valid       │
         │                       │◄──────────────────────┤
         │                       │                       │
         │ 4. Return Token       │                       │
         │◄──────────────────────┤                       │
         │                       │                       │
         │ 5. API Request        │                       │
         │ (Bearer Token)        │                       │
         ├──────────────────────►│                       │
         │                       │                       │
         │                       │ 6. Validate Token     │
         │                       │ (internal)            │
         │                       │                       │
         │                       │ 7. Check Scopes       │
         │                       │ (internal)            │
         │                       │                       │
         │ 8. API Response       │                       │
         │◄──────────────────────┤                       │
         │                       │                       │
```

### Step-by-Step Authorization Process

#### Step 1: Client Authentication Request

```bash
# Request an authentication token
curl -X POST https://dgapi.example.com/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "scope": "disposition:write,sms:send"
  }'
```

#### Step 2-4: Token Generation Response

```json
{
  "status": "success",
  "data": {
    "access_token": "eyJjbGllbnRfaWQiOiJ5b3VyX2NsaWVudF9pZCIsInNjb3BlIjoiZGlzcG9zaXRpb246d3JpdGUsc21zOnNlbmQiLCJleHBpcmVzX2luIjozNjAwfQ==.a1b2c3d4e5f6g7h8i9j0.1699123456",
    "token_type": "Bearer",
    "expires_in": 3600,
    "scope": "disposition:write,sms:send"
  }
}
```

#### Step 5: Making Authenticated API Requests

```bash
# Use the token to make an authenticated request
curl -X POST https://dgapi.example.com/api/disposition/create \
  -H "Authorization: Bearer eyJjbGllbnRfaWQiOiJ5b3VyX2NsaWVudF9pZCIsInNjb3BlIjoiZGlzcG9zaXRpb246d3JpdGUsc21zOnNlbmQiLCJleHBpcmVzX2luIjozNjAwfQ==.a1b2c3d4e5f6g7h8i9j0.1699123456" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "TASK-12345",
    "disposition_code": "COMPLETED",
    "notes": "Task completed successfully"
  }'
```

### DOM-Based Request Handling

DGAPI uses DOM-based request and response handling for structured data processing:

```php
<?php
// DOM-based request parsing
$requestDom = new DOMDocument();
$requestDom->loadXML($this->input->raw_input_stream);

// Extract authentication element
$authElement = $requestDom->getElementsByTagName('authentication')->item(0);
$token = $authElement->getAttribute('token');

// Validate token
$tokenData = $this->authorization->validateToken($token);

// Process request with validated context
$taskElement = $requestDom->getElementsByTagName('task')->item(0);
$taskId = $taskElement->getAttribute('id');
```

---

## Key Generation (dgapi-keygen)

### Overview

The `dgapi-keygen` utility is a command-line tool for generating secure API keys and secrets used in the DGAPI authentication system. This tool ensures cryptographically secure key generation following security best practices.

### Installation and Usage

#### Basic Key Generation

```bash
# Navigate to the DGAPI tools directory
cd /path/to/platform-dgapi/tools

# Generate a new client key pair
php dgapi-keygen.php --type=client --output=keys/

# Output:
# Client ID: dgapi_client_a1b2c3d4e5f6
# Client Secret: sk_test_EXAMPLE_KEY_REPLACE_WITH_REAL_KEY
# Keys saved to: keys/dgapi_client_a1b2c3d4e5f6.json
```

#### Advanced Key Generation Options

```bash
# Generate keys with specific parameters
php dgapi-keygen.php \
  --type=client \
  --name="Production SMS Service" \
  --scopes="sms:send,disposition:write" \
  --expires=365 \
  --output=keys/production/

# Generate signing key for token signatures
php dgapi-keygen.php \
  --type=signing \
  --algorithm=sha256 \
  --length=64 \
  --output=config/
```

### Key Configuration

```php
<?php
// config/dgapi_auth.php

$config['dgapi_signing_key'] = getenv('DGAPI_SIGNING_KEY') 
    ?: 'your_default_signing_key_min_32_chars';

$config['dgapi_token_expiry'] = 3600; // 1 hour default

$config['dgapi_allowed_scopes'] = [
    'disposition:read',
    'disposition:write',
    'sms:send',
    'email:send',
    'voicemail:process',
    'cdr:process',
    'callback:finish',
    'admin:full'
];

$config['dgapi_clients'] = [
    'dgapi_client_a1b2c3d4e5f6' => [
        'secret' => 'sk_test_EXAMPLE_KEY_REPLACE_WITH_REAL_KEY',
        'name' => 'Production SMS Service',
        'allowed_scopes' => ['sms:send', 'disposition:write'],
        'rate_limit' => 1000, // requests per hour
        'active' => true
    ],
    // Additional clients...
];
```

### Programmatic Key Generation

```php
<?php
require_once APPPATH . 'libraries/DGAPIKeyGenerator.php';

$keyGen = new DGAPIKeyGenerator();

// Generate a new client
$newClient = $keyGen->generateClient([
    'name' => 'New Integration Partner',
    'scopes' => ['disposition:read', 'cdr:process'],
    'rate_limit' => 500
]);

// Store in database
$this->db->insert('dgapi_clients', [
    'client_id' => $newClient['client_id'],
    'client_secret_hash' => password_hash($newClient['client_secret'], PASSWORD_ARGON2ID),
    'name' => $newClient['name'],
    'scopes' => json_encode($newClient['scopes']),
    'rate_limit' => $newClient['rate_limit'],
    'created_at' => date('Y-m-d H:i:s'),
    'active' => 1
]);

// Return credentials to administrator (show once only)
return $newClient;
```

---

## Error Codes

### Authentication Error Reference

| HTTP Status | Error Code | Description | Resolution |
|-------------|------------|-------------|------------|
| 400 | `MISSING_CREDENTIALS` | Client ID or secret not provided | Include both client_id and client_secret in request |
| 401 | `INVALID_TOKEN_FORMAT` | Token does not match expected format | Ensure token is correctly formatted with three dot-separated parts |
| 401 | `MALFORMED_TOKEN` | Token structure is corrupted | Request a new token |
| 401 | `TOKEN_EXPIRED` | Token has exceeded its validity period | Request a new token with valid credentials |
| 401 | `INVALID_SIGNATURE` | Token signature verification failed | Ensure token hasn't been modified; request new token |
| 401 | `MISSING_AUTH_HEADER` | Authorization header not present | Include `Authorization: Bearer <token>` header |
| 401 | `INVALID_AUTH_FORMAT` | Authorization header format incorrect | Use `Bearer` scheme: `Authorization: Bearer <token>` |
| 403 | `INVALID_CLIENT` | Client credentials are invalid or revoked | Verify client_id and client_secret; contact administrator if revoked |
| 403 | `INSUFFICIENT_SCOPE` | Token lacks required permission scope | Request token with appropriate scopes |
| 403 | `CLIENT_DISABLED` | Client account has been deactivated | Contact administrator to reactivate |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests from this client | Wait before retrying; consider increasing rate limit |

### Error Response Format

```json
{
  "status": "error",
  "error": {
    "code": 401,
    "type": "TOKEN_EXPIRED",
    "message": "The provided authentication token has expired",
    "details": {
      "expired_at": "2024-01-15T10:30:00Z",
      "current_time": "2024-01-15T12:45:00Z"
    },
    "request_id": "req_abc123def456"
  }
}
```

### Handling Errors in Client Code

```php
<?php
// Client-side error handling
$response = $httpClient->post($dgapiUrl, [
    'headers' => [
        'Authorization' => 'Bearer ' . $accessToken,
        'Content-Type' => 'application/json'
    ],
    'json' => $requestData
]);

$statusCode = $response->getStatusCode();
$body = json_decode($response->getBody(), true);

if ($statusCode === 401) {
    switch ($body['error']['type']) {
        case 'TOKEN_EXPIRED':
            // Refresh the token and retry
            $newToken = $this->refreshAuthToken();
            return $this->retryRequest($requestData, $newToken);
            
        case 'INVALID_SIGNATURE':
        case 'INVALID_CLIENT':
            // Re-authenticate completely
            $newToken = $this->authenticate();
            return $this->retryRequest($requestData, $newToken);
            
        default:
            throw new AuthenticationException($body['error']['message']);
    }
}

if ($statusCode === 403) {
    if ($body['error']['type'] === 'INSUFFICIENT_SCOPE') {
        throw new InsufficientScopeException(
            "Required scope: " . $body['error']['details']['required_scope']
        );
    }
}
```

---

## Examples

### Complete Integration Example

This comprehensive example demonstrates a full integration with the DGAPI authentication system:

```php
<?php
/**
 * DGAPI Client Integration Class
 * 
 * Complete example of integrating with platform-dgapi authentication
 */
class DGAPIClient {
    
    private $baseUrl;
    private $clientId;
    private $clientSecret;
    private $accessToken;
    private $tokenExpiry;
    
    public function __construct($config) {
        $this->baseUrl = $config['base_url'];
        $this->clientId = $config['client_id'];
        $this->clientSecret = $config['client_secret'];
    }
    
    /**
     * Authenticate and obtain access token
     */
    public function authenticate($scopes = []) {
        $scopeString = implode(',', $scopes);
        
        $response = $this->httpPost('/auth/token', [
            'client_id' => $this->clientId,
            'client_secret' => $this->clientSecret,
            'scope' => $scopeString
        ], false); // Don't use auth for token request
        
        if ($response['status'] === 'success') {
            $this->accessToken = $response['data']['access_token'];
            $this->tokenExpiry = time() + $response['data']['expires_in'];
            return true;
        }
        
        throw new Exception("Authentication failed: " . $response['error']['message']);
    }
    
    /**
     * Check if current token is valid
     */
    public function isTokenValid() {
        return $this->accessToken && time() < ($this->tokenExpiry - 60);
    }
    
    /**
     * Ensure we have a valid token before making requests
     */
    private function ensureAuthenticated($requiredScopes) {
        if (!$this->isTokenValid()) {
            $this->authenticate($requiredScopes);
        }
    }
    
    /**
     * Send SMS notification via DGAPI
     */
    public function sendSMS($phoneNumber, $message, $taskId = null) {
        $this->ensureAuthenticated(['sms:send']);
        
        return $this->httpPost('/api/sms/send', [
            'phone_number' => $phoneNumber,
            'message' => $message,
            'task_id' => $taskId,
            'timestamp' => date('c')
        ]);
    }
    
    /**
     * Create task disposition
     */
    public function createDisposition($taskId, $dispositionCode, $notes = '') {
        $this->ensureAuthenticated(['disposition:write']);
        
        return $this->httpPost('/api/disposition/create', [
            'task_id' => $taskId,
            'disposition_code' => $dispositionCode,
            'notes' => $notes,
            'created_at' => date('c')
        ]);
    }
    
    /**
     * Process CDR record
     */
    public function processCDR($cdrData) {
        $this->ensureAuthenticated(['cdr:process']);
        
        return $this->httpPost('/api/cdr/process', $cdrData);
    }
    
    /**
     * Generic HTTP POST request
     */
    private function httpPost($endpoint, $data, $useAuth = true) {
        $headers = ['Content-Type: application/json'];
        
        if ($useAuth && $this->accessToken) {
            $headers[] = 'Authorization: Bearer ' . $this->accessToken;
        }
        
        $ch = curl_init($this->baseUrl . $endpoint);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => json_encode($data),
            CURLOPT_HTTPHEADER => $headers,
            CURLOPT_TIMEOUT => 30
        ]);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        return json_decode($response, true);
    }
}

// Usage Example
$dgapi = new DGAPIClient([
    'base_url' => 'https://dgapi.example.com',
    'client_id' => 'your_client_id',
    'client_secret' => 'your_client_secret'
]);

try {
    // Authenticate with required scopes
    $dgapi->authenticate(['sms:send', 'disposition:write']);
    
    // Send SMS notification
    $smsResult = $dgapi->sendSMS('+1234567890', 'Your task has been completed.');
    
    // Create disposition
    $dispositionResult = $dgapi->createDisposition(
        'TASK-12345',
        'COMPLETED',
        'Customer confirmed receipt'
    );
    
    echo "SMS sent: " . ($smsResult['status'] === 'success' ? 'Yes' : 'No') . "\n";
    echo "Disposition created: " . ($dispositionResult['status'] === 'success' ? 'Yes' : 'No') . "\n";
    
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
```

### cURL Examples for Testing

```bash
# 1. Obtain authentication token
curl -X POST https://dgapi.example.com/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test_client",
    "client_secret": "test_secret",
    "scope": "disposition:write,sms:send,email:send"
  }' | jq .

# 2. Create disposition with token
export DGAPI_TOKEN="your_token_here"

curl -X POST https://dgapi.example.com/api/disposition/create \
  -H "Authorization: Bearer $DGAPI_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "TASK-98765",
    "disposition_code": "CALLBACK_SCHEDULED",
    "notes": "Customer requested callback at 3 PM",
    "metadata": {
      "callback_time": "2024-01-15T15:00:00Z",
      "agent_id": "AGENT-001"
    }
  }' | jq .

# 3. Send SMS notification
curl -X POST https://dgapi.example.com/api/sms/send \
  -H "Authorization: Bearer $DGAPI_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "message": "Your appointment is confirmed for tomorrow at 10 AM.",
    "task_id": "TASK-98765"
  }' | jq .

# 4. Process voicemail notification
curl -X POST https://dgapi.example.com/api/voicemail/process \
  -H "Authorization: Bearer $DGAPI_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "voicemail_id": "VM-12345",
    "caller_number": "+1987654321",
    "duration_seconds": 45,
    "transcription": "Hi, this is John calling about my order...",
    "audio_url": "https://storage.example.com/voicemails/VM-12345.mp3"
  }' | jq .
```

---

## Best Practices

### Security Recommendations

1. **Never expose client secrets** in client-side code or version control
2. **Use environment variables** for storing sensitive credentials
3. **Implement token refresh** logic before expiration to avoid service interruptions
4. **Request minimal scopes** needed for each integration
5. **Rotate keys periodically** using the dgapi-keygen tool
6. **Monitor authentication failures** for potential security threats
7. **Use HTTPS exclusively** for all DGAPI communications

### Performance Considerations

1. **Cache tokens** until near expiration rather than requesting new tokens for each API call
2. **Implement connection pooling** for high-volume integrations
3. **Use appropriate timeouts** to prevent hanging requests
4. **Batch operations** when possible to reduce authentication overhead

---

## Troubleshooting

### Common Issues and Solutions

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| Token immediately expires | Server clock skew | Synchronize server time with NTP |
| Signature validation fails | Modified token or wrong signing key | Verify signing key matches between token generation and validation |
| Scope errors despite correct scope | Cached token with old scopes | Request new token with updated scopes |
| Rate limiting errors | Too many requests | Implement exponential backoff; request rate limit increase |

For additional support, consult the DGAPI service logs at `/var/log/dgapi/auth.log` or contact the platform administration team.