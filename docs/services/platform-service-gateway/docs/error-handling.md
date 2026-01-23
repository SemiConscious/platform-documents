# Error Handling Guide

## Overview

This comprehensive guide documents the error handling architecture and exception types used throughout the Platform Service Gateway (platform-service-gateway). Understanding how errors are structured, thrown, and handled is essential for developers integrating with CRM systems and operators deploying and maintaining the gateway.

The Platform Service Gateway implements a layered error handling system designed to provide consistent, informative error responses across all 59 API endpoints while supporting integrations with multiple CRM platforms including Salesforce, Microsoft Dynamics, Zendesk, SugarCRM, Oracle Fusion, and custom data sources.

## Error Response Format

### Standard Error Response Structure

All errors returned by the Platform Service Gateway follow a consistent JSON structure, enabling predictable error handling in client applications:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": {
      "field": "Additional context about the error",
      "timestamp": "2024-01-15T10:30:00Z",
      "request_id": "req_abc123xyz"
    },
    "http_status": 400
  }
}
```

### Response Fields Explained

| Field | Type | Description |
|-------|------|-------------|
| `code` | string | Unique error identifier for programmatic handling |
| `message` | string | Human-readable description suitable for logging or display |
| `details` | object | Optional additional context (varies by error type) |
| `http_status` | integer | HTTP status code associated with the error |

### HTTP Status Code Mapping

The gateway maps errors to appropriate HTTP status codes:

| Status Code | Category | Description |
|-------------|----------|-------------|
| 400 | Bad Request | Invalid input, malformed requests |
| 401 | Unauthorized | Authentication required or failed |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource does not exist |
| 405 | Method Not Allowed | HTTP method not supported for endpoint |
| 409 | Conflict | Resource state conflict |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limiting triggered |
| 500 | Internal Server Error | Unexpected server errors |
| 502 | Bad Gateway | Upstream CRM service errors |
| 503 | Service Unavailable | Temporary service issues |

---

## Exception Types

The Platform Service Gateway implements a hierarchical exception system built on CodeIgniter's PHP framework. Understanding this hierarchy is crucial for both implementing custom error handling and debugging integration issues.

### Exception Hierarchy

```
Exception (PHP Base)
└── SgException (Base Gateway Exception)
    ├── RestApiErrorException
    │   └── SgCannedRestApiErrorException
    ├── SgMethodNotAllowedException
    ├── SgBadRequestException
    └── MgwError
```

---

## SgException

### Description

`SgException` serves as the base exception class for all Platform Service Gateway specific errors. It extends PHP's native `Exception` class and provides additional context relevant to gateway operations.

### Class Definition

```php
<?php
namespace App\Exceptions;

class SgException extends \Exception
{
    protected $errorCode;
    protected $details;
    protected $httpStatus;
    protected $requestId;

    public function __construct(
        string $message,
        string $errorCode = 'SG_GENERIC_ERROR',
        int $httpStatus = 500,
        array $details = [],
        \Throwable $previous = null
    ) {
        parent::__construct($message, 0, $previous);
        $this->errorCode = $errorCode;
        $this->httpStatus = $httpStatus;
        $this->details = $details;
        $this->requestId = $this->generateRequestId();
    }

    public function getErrorCode(): string
    {
        return $this->errorCode;
    }

    public function getHttpStatus(): int
    {
        return $this->httpStatus;
    }

    public function getDetails(): array
    {
        return $this->details;
    }

    public function getRequestId(): string
    {
        return $this->requestId;
    }

    public function toArray(): array
    {
        return [
            'error' => [
                'code' => $this->errorCode,
                'message' => $this->getMessage(),
                'details' => array_merge($this->details, [
                    'request_id' => $this->requestId,
                    'timestamp' => date('c')
                ]),
                'http_status' => $this->httpStatus
            ]
        ];
    }

    protected function generateRequestId(): string
    {
        return 'req_' . bin2hex(random_bytes(12));
    }
}
```

### Usage Example

```php
<?php
// Throwing a basic SgException
throw new SgException(
    'Unable to process the integration request',
    'SG_INTEGRATION_ERROR',
    500,
    ['platform' => 'salesforce', 'operation' => 'sync']
);

// Catching and handling SgException
try {
    $gateway->processRequest($request);
} catch (SgException $e) {
    log_message('error', sprintf(
        '[%s] %s - Details: %s',
        $e->getRequestId(),
        $e->getMessage(),
        json_encode($e->getDetails())
    ));
    
    return $this->response
        ->setStatusCode($e->getHttpStatus())
        ->setJSON($e->toArray());
}
```

---

## RestApiErrorException

### Description

`RestApiErrorException` handles errors that occur during REST API operations, particularly when communicating with external CRM platforms. This exception captures upstream error information and transforms it into the gateway's standard format.

### Class Definition

```php
<?php
namespace App\Exceptions;

class RestApiErrorException extends SgException
{
    protected $upstreamStatusCode;
    protected $upstreamResponse;
    protected $platform;
    protected $endpoint;

    public function __construct(
        string $message,
        string $platform,
        string $endpoint,
        int $upstreamStatusCode = 0,
        $upstreamResponse = null,
        string $errorCode = 'REST_API_ERROR',
        int $httpStatus = 502
    ) {
        $this->upstreamStatusCode = $upstreamStatusCode;
        $this->upstreamResponse = $upstreamResponse;
        $this->platform = $platform;
        $this->endpoint = $endpoint;

        $details = [
            'platform' => $platform,
            'endpoint' => $endpoint,
            'upstream_status' => $upstreamStatusCode
        ];

        parent::__construct($message, $errorCode, $httpStatus, $details);
    }

    public function getUpstreamStatusCode(): int
    {
        return $this->upstreamStatusCode;
    }

    public function getUpstreamResponse()
    {
        return $this->upstreamResponse;
    }

    public function getPlatform(): string
    {
        return $this->platform;
    }

    public function getEndpoint(): string
    {
        return $this->endpoint;
    }

    public function isRetryable(): bool
    {
        return in_array($this->upstreamStatusCode, [408, 429, 500, 502, 503, 504]);
    }
}
```

### Usage Example

```php
<?php
// When Salesforce API returns an error
try {
    $response = $salesforceClient->query($soqlQuery);
} catch (\GuzzleHttp\Exception\ClientException $e) {
    throw new RestApiErrorException(
        'Salesforce query failed: ' . $e->getMessage(),
        'salesforce',
        '/services/data/v58.0/query',
        $e->getResponse()->getStatusCode(),
        json_decode($e->getResponse()->getBody()->getContents(), true),
        'SALESFORCE_QUERY_ERROR',
        502
    );
}

// Implementing retry logic
try {
    $result = $gateway->fetchFromCRM($request);
} catch (RestApiErrorException $e) {
    if ($e->isRetryable()) {
        // Queue for retry with exponential backoff
        $this->retryQueue->add($request, [
            'max_attempts' => 3,
            'backoff_multiplier' => 2
        ]);
    }
    throw $e;
}
```

---

## SgCannedRestApiErrorException

### Description

`SgCannedRestApiErrorException` provides pre-defined, standardized error responses for common REST API failure scenarios. This ensures consistent error messaging across all platform integrations.

### Class Definition

```php
<?php
namespace App\Exceptions;

class SgCannedRestApiErrorException extends RestApiErrorException
{
    const ERRORS = [
        'AUTH_TOKEN_EXPIRED' => [
            'message' => 'Authentication token has expired. Please re-authenticate.',
            'http_status' => 401,
            'error_code' => 'AUTH_TOKEN_EXPIRED'
        ],
        'AUTH_TOKEN_INVALID' => [
            'message' => 'Invalid authentication token provided.',
            'http_status' => 401,
            'error_code' => 'AUTH_TOKEN_INVALID'
        ],
        'RATE_LIMIT_EXCEEDED' => [
            'message' => 'API rate limit exceeded. Please retry after the specified interval.',
            'http_status' => 429,
            'error_code' => 'RATE_LIMIT_EXCEEDED'
        ],
        'RESOURCE_NOT_FOUND' => [
            'message' => 'The requested resource was not found on the upstream platform.',
            'http_status' => 404,
            'error_code' => 'UPSTREAM_RESOURCE_NOT_FOUND'
        ],
        'PLATFORM_UNAVAILABLE' => [
            'message' => 'The target platform is temporarily unavailable.',
            'http_status' => 503,
            'error_code' => 'PLATFORM_UNAVAILABLE'
        ],
        'INVALID_QUERY' => [
            'message' => 'The query syntax is invalid for the target platform.',
            'http_status' => 400,
            'error_code' => 'INVALID_QUERY_SYNTAX'
        ],
        'INSUFFICIENT_PERMISSIONS' => [
            'message' => 'Insufficient permissions to access the requested resource.',
            'http_status' => 403,
            'error_code' => 'INSUFFICIENT_PERMISSIONS'
        ],
        'CONNECTION_TIMEOUT' => [
            'message' => 'Connection to the upstream platform timed out.',
            'http_status' => 504,
            'error_code' => 'CONNECTION_TIMEOUT'
        ]
    ];

    public function __construct(
        string $errorKey,
        string $platform,
        string $endpoint,
        array $additionalDetails = []
    ) {
        if (!isset(self::ERRORS[$errorKey])) {
            throw new \InvalidArgumentException("Unknown canned error key: {$errorKey}");
        }

        $error = self::ERRORS[$errorKey];

        parent::__construct(
            $error['message'],
            $platform,
            $endpoint,
            0,
            null,
            $error['error_code'],
            $error['http_status']
        );

        $this->details = array_merge($this->details, $additionalDetails);
    }

    public static function authTokenExpired(string $platform, string $endpoint): self
    {
        return new self('AUTH_TOKEN_EXPIRED', $platform, $endpoint);
    }

    public static function rateLimitExceeded(string $platform, string $endpoint, int $retryAfter): self
    {
        return new self('RATE_LIMIT_EXCEEDED', $platform, $endpoint, [
            'retry_after' => $retryAfter
        ]);
    }

    public static function platformUnavailable(string $platform): self
    {
        return new self('PLATFORM_UNAVAILABLE', $platform, '*');
    }
}
```

### Usage Example

```php
<?php
// Using static factory methods
if ($token->isExpired()) {
    throw SgCannedRestApiErrorException::authTokenExpired(
        'dynamics365',
        '/api/data/v9.2/contacts'
    );
}

// Rate limiting with retry information
if ($response->getStatusCode() === 429) {
    $retryAfter = (int) $response->getHeader('Retry-After')[0] ?? 60;
    throw SgCannedRestApiErrorException::rateLimitExceeded(
        'zendesk',
        '/api/v2/tickets',
        $retryAfter
    );
}

// Direct instantiation with additional details
throw new SgCannedRestApiErrorException(
    'INSUFFICIENT_PERMISSIONS',
    'salesforce',
    '/services/data/v58.0/sobjects/Account',
    ['required_permission' => 'Account.Read', 'user_permissions' => ['Contact.Read']]
);
```

---

## SgMethodNotAllowedException

### Description

`SgMethodNotAllowedException` is thrown when a client attempts to use an HTTP method that is not supported by a particular endpoint. This exception includes information about which methods are allowed.

### Class Definition

```php
<?php
namespace App\Exceptions;

class SgMethodNotAllowedException extends SgException
{
    protected $allowedMethods;
    protected $attemptedMethod;
    protected $endpoint;

    public function __construct(
        string $attemptedMethod,
        string $endpoint,
        array $allowedMethods
    ) {
        $this->attemptedMethod = $attemptedMethod;
        $this->endpoint = $endpoint;
        $this->allowedMethods = $allowedMethods;

        $message = sprintf(
            'Method %s is not allowed for endpoint %s. Allowed methods: %s',
            $attemptedMethod,
            $endpoint,
            implode(', ', $allowedMethods)
        );

        parent::__construct(
            $message,
            'METHOD_NOT_ALLOWED',
            405,
            [
                'attempted_method' => $attemptedMethod,
                'allowed_methods' => $allowedMethods,
                'endpoint' => $endpoint
            ]
        );
    }

    public function getAllowedMethods(): array
    {
        return $this->allowedMethods;
    }

    public function getAttemptedMethod(): string
    {
        return $this->attemptedMethod;
    }

    public function getAllowHeader(): string
    {
        return implode(', ', $this->allowedMethods);
    }
}
```

### Usage Example

```php
<?php
// In a route handler or middleware
$allowedMethods = ['GET', 'POST'];
$requestMethod = $request->getMethod();

if (!in_array($requestMethod, $allowedMethods)) {
    throw new SgMethodNotAllowedException(
        $requestMethod,
        $request->getUri()->getPath(),
        $allowedMethods
    );
}

// In error handler - set Allow header
try {
    $response = $router->dispatch($request);
} catch (SgMethodNotAllowedException $e) {
    return $this->response
        ->setStatusCode(405)
        ->setHeader('Allow', $e->getAllowHeader())
        ->setJSON($e->toArray());
}
```

---

## SgBadRequestException

### Description

`SgBadRequestException` handles invalid client requests including malformed JSON, missing required parameters, invalid parameter values, and validation failures.

### Class Definition

```php
<?php
namespace App\Exceptions;

class SgBadRequestException extends SgException
{
    protected $validationErrors;
    protected $invalidFields;

    public function __construct(
        string $message,
        array $validationErrors = [],
        string $errorCode = 'BAD_REQUEST'
    ) {
        $this->validationErrors = $validationErrors;
        $this->invalidFields = array_keys($validationErrors);

        parent::__construct(
            $message,
            $errorCode,
            400,
            [
                'validation_errors' => $validationErrors,
                'invalid_fields' => $this->invalidFields
            ]
        );
    }

    public function getValidationErrors(): array
    {
        return $this->validationErrors;
    }

    public function getInvalidFields(): array
    {
        return $this->invalidFields;
    }

    public static function missingRequiredField(string $field): self
    {
        return new self(
            "Missing required field: {$field}",
            [$field => 'This field is required'],
            'MISSING_REQUIRED_FIELD'
        );
    }

    public static function invalidFieldValue(string $field, string $reason): self
    {
        return new self(
            "Invalid value for field: {$field}",
            [$field => $reason],
            'INVALID_FIELD_VALUE'
        );
    }

    public static function malformedJson(string $jsonError): self
    {
        return new self(
            "Malformed JSON in request body: {$jsonError}",
            ['body' => $jsonError],
            'MALFORMED_JSON'
        );
    }

    public static function fromValidationResult(array $errors): self
    {
        return new self(
            'Request validation failed',
            $errors,
            'VALIDATION_FAILED'
        );
    }
}
```

### Usage Example

```php
<?php
// Validating incoming request
$rules = [
    'platform' => 'required|in_list[salesforce,dynamics,zendesk,sugarcrm,oracle]',
    'query' => 'required|min_length[1]',
    'limit' => 'permit_empty|integer|greater_than[0]|less_than[1001]'
];

$validation = \Config\Services::validation();
if (!$validation->setRules($rules)->run($request->getJSON(true))) {
    throw SgBadRequestException::fromValidationResult($validation->getErrors());
}

// Checking for required field
$data = $request->getJSON(true);
if (empty($data['platform'])) {
    throw SgBadRequestException::missingRequiredField('platform');
}

// Validating field value
$validPlatforms = ['salesforce', 'dynamics', 'zendesk', 'sugarcrm', 'oracle'];
if (!in_array($data['platform'], $validPlatforms)) {
    throw SgBadRequestException::invalidFieldValue(
        'platform',
        'Must be one of: ' . implode(', ', $validPlatforms)
    );
}

// Handling malformed JSON
$json = $request->getBody();
$data = json_decode($json, true);
if (json_last_error() !== JSON_ERROR_NONE) {
    throw SgBadRequestException::malformedJson(json_last_error_msg());
}
```

---

## MgwError

### Description

`MgwError` (Multi-Gateway Error) handles errors that span multiple platform integrations or occur during multi-source query operations. This exception aggregates errors from multiple upstream sources.

### Class Definition

```php
<?php
namespace App\Exceptions;

class MgwError extends SgException
{
    protected $platformErrors;
    protected $successfulPlatforms;
    protected $failedPlatforms;
    protected $partialSuccess;

    public function __construct(
        string $message,
        array $platformErrors,
        array $successfulPlatforms = []
    ) {
        $this->platformErrors = $platformErrors;
        $this->failedPlatforms = array_keys($platformErrors);
        $this->successfulPlatforms = $successfulPlatforms;
        $this->partialSuccess = !empty($successfulPlatforms);

        $httpStatus = $this->partialSuccess ? 207 : 502;

        parent::__construct(
            $message,
            'MULTI_GATEWAY_ERROR',
            $httpStatus,
            [
                'failed_platforms' => $this->failedPlatforms,
                'successful_platforms' => $this->successfulPlatforms,
                'partial_success' => $this->partialSuccess,
                'platform_errors' => $this->formatPlatformErrors()
            ]
        );
    }

    protected function formatPlatformErrors(): array
    {
        $formatted = [];
        foreach ($this->platformErrors as $platform => $error) {
            if ($error instanceof \Throwable) {
                $formatted[$platform] = [
                    'message' => $error->getMessage(),
                    'code' => $error instanceof SgException 
                        ? $error->getErrorCode() 
                        : 'UNKNOWN_ERROR'
                ];
            } else {
                $formatted[$platform] = [
                    'message' => (string) $error,
                    'code' => 'UNKNOWN_ERROR'
                ];
            }
        }
        return $formatted;
    }

    public function getPlatformErrors(): array
    {
        return $this->platformErrors;
    }

    public function getFailedPlatforms(): array
    {
        return $this->failedPlatforms;
    }

    public function getSuccessfulPlatforms(): array
    {
        return $this->successfulPlatforms;
    }

    public function isPartialSuccess(): bool
    {
        return $this->partialSuccess;
    }

    public function getPlatformError(string $platform): ?\Throwable
    {
        return $this->platformErrors[$platform] ?? null;
    }
}
```

### Usage Example

```php
<?php
// Multi-platform query execution
$platforms = ['salesforce', 'dynamics', 'zendesk'];
$results = [];
$errors = [];
$successful = [];

foreach ($platforms as $platform) {
    try {
        $results[$platform] = $this->queryPlatform($platform, $query);
        $successful[] = $platform;
    } catch (\Throwable $e) {
        $errors[$platform] = $e;
        log_message('error', "Query failed for {$platform}: " . $e->getMessage());
    }
}

// Handle mixed results
if (!empty($errors)) {
    if (empty($successful)) {
        // Complete failure
        throw new MgwError(
            'Query failed on all requested platforms',
            $errors
        );
    } else {
        // Partial success - might want to return partial results
        $mgwError = new MgwError(
            'Query succeeded on some platforms but failed on others',
            $errors,
            $successful
        );
        
        // Return partial results with warning
        return $this->response
            ->setStatusCode(207) // Multi-Status
            ->setJSON([
                'results' => $results,
                'warnings' => $mgwError->toArray()
            ]);
    }
}
```

---

## Error Codes Reference

### Complete Error Code Catalog

| Error Code | HTTP Status | Category | Description |
|------------|-------------|----------|-------------|
| `SG_GENERIC_ERROR` | 500 | System | Unspecified internal error |
| `SG_INTEGRATION_ERROR` | 500 | System | Platform integration failure |
| `REST_API_ERROR` | 502 | API | Generic REST API error |
| `AUTH_TOKEN_EXPIRED` | 401 | Authentication | OAuth/token expired |
| `AUTH_TOKEN_INVALID` | 401 | Authentication | Invalid credentials/token |
| `AUTH_LDAP_FAILED` | 401 | Authentication | LDAP authentication failure |
| `AUTH_GOODDATA_FAILED` | 401 | Authentication | GoodData authentication failure |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate Limiting | API rate limit hit |
| `UPSTREAM_RESOURCE_NOT_FOUND` | 404 | API | Resource missing on CRM |
| `PLATFORM_UNAVAILABLE` | 503 | Availability | CRM platform down |
| `INVALID_QUERY_SYNTAX` | 400 | Validation | Malformed query |
| `INSUFFICIENT_PERMISSIONS` | 403 | Authorization | Access denied |
| `CONNECTION_TIMEOUT` | 504 | Network | Request timeout |
| `METHOD_NOT_ALLOWED` | 405 | Routing | Invalid HTTP method |
| `BAD_REQUEST` | 400 | Validation | Generic bad request |
| `MISSING_REQUIRED_FIELD` | 400 | Validation | Required field missing |
| `INVALID_FIELD_VALUE` | 400 | Validation | Field value invalid |
| `MALFORMED_JSON` | 400 | Validation | JSON parse error |
| `VALIDATION_FAILED` | 400 | Validation | Multiple validation errors |
| `MULTI_GATEWAY_ERROR` | 502/207 | Multi-Platform | Aggregated platform errors |
| `FEED_CONFIGURATION_ERROR` | 500 | Configuration | Feed/webhook config issue |
| `WEBHOOK_DELIVERY_FAILED` | 502 | Webhook | Webhook POST failed |
| `DATA_SOURCE_ERROR` | 500 | Data Source | Custom data source error |

### Platform-Specific Error Codes

#### Salesforce Errors

| Error Code | Description |
|------------|-------------|
| `SALESFORCE_QUERY_ERROR` | SOQL query execution failed |
| `SALESFORCE_AUTH_FAILED` | OAuth flow failed |
| `SALESFORCE_RECORD_LOCKED` | Record locked by another user |
| `SALESFORCE_FIELD_INTEGRITY` | Field-level security violation |

#### Microsoft Dynamics Errors

| Error Code | Description |
|------------|-------------|
| `DYNAMICS_QUERY_ERROR` | OData query failed |
| `DYNAMICS_AUTH_FAILED` | Azure AD authentication failed |
| `DYNAMICS_ENTITY_NOT_FOUND` | Entity type not found |

#### Zendesk Errors

| Error Code | Description |
|------------|-------------|
| `ZENDESK_QUERY_ERROR` | Search API error |
| `ZENDESK_AUTH_FAILED` | API token invalid |
| `ZENDESK_RATE_LIMITED` | Zendesk rate limit exceeded |

---

## Troubleshooting Common Errors

### Authentication Errors

#### Problem: `AUTH_TOKEN_EXPIRED` errors occurring frequently

**Symptoms:**
- Multiple 401 responses with `AUTH_TOKEN_EXPIRED` code
- Users experiencing frequent re-authentication prompts

**Diagnosis:**
```php
<?php
// Check token expiration configuration
$tokenLifetime = getenv('OAUTH_TOKEN_LIFETIME') ?: 3600;
$refreshWindow = getenv('TOKEN_REFRESH_WINDOW') ?: 300;

log_message('debug', "Token lifetime: {$tokenLifetime}s, Refresh window: {$refreshWindow}s");

// Verify token refresh is working
$tokenManager = service('tokenManager');
$status = $tokenManager->getRefreshStatus('salesforce', $userId);
var_dump($status);
```

**Solutions:**

1. **Enable proactive token refresh:**
```php
// config/Gateway.php
public $tokenManagement = [
    'proactive_refresh' => true,
    'refresh_threshold' => 300, // Refresh 5 minutes before expiry
    'retry_failed_refresh' => 3
];
```

2. **Implement token refresh middleware:**
```php
<?php
class TokenRefreshFilter implements FilterInterface
{
    public function before(RequestInterface $request, $arguments = null)
    {
        $tokenManager = service('tokenManager');
        $platform = $request->getGet('platform');
        
        if ($tokenManager->shouldRefresh($platform)) {
            try {
                $tokenManager->refresh($platform);
            } catch (RestApiErrorException $e) {
                log_message('warning', "Token refresh failed: " . $e->getMessage());
            }
        }
        
        return $request;
    }
}
```

### Rate Limiting Issues

#### Problem: `RATE_LIMIT_EXCEEDED` errors from upstream platforms

**Symptoms:**
- 429 status codes returned to clients
- Salesforce/Zendesk API limits being hit

**Diagnosis:**
```bash
# Check current rate limit status
curl -X GET "http://gateway/admin/rate-limits" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Solutions:**

1. **Implement request queuing with backoff:**
```php
<?php
// services/RateLimitedClient.php
class RateLimitedClient
{
    private $rateLimiter;
    
    public function request(string $platform, callable $operation)
    {
        $maxRetries = 3;
        $baseDelay = 1;
        
        for ($attempt = 1; $attempt <= $maxRetries; $attempt++) {
            if (!$this->rateLimiter->acquire($platform)) {
                $waitTime = $this->rateLimiter->getWaitTime($platform);
                sleep($waitTime);
            }
            
            try {
                return $operation();
            } catch (RestApiErrorException $e) {
                if ($e->getUpstreamStatusCode() === 429) {
                    $delay = $baseDelay * pow(2, $attempt);
                    log_message('info', "Rate limited, waiting {$delay}s before retry");
                    sleep($delay);
                    continue;
                }
                throw $e;
            }
        }
        
        throw SgCannedRestApiErrorException::rateLimitExceeded(
            $platform, 
            'multiple-endpoints',
            60
        );
    }
}
```

2. **Configure platform-specific limits:**
```php
// config/RateLimits.php
return [
    'salesforce' => [
        'requests_per_day' => 15000,
        'requests_per_hour' => 1000,
        'concurrent_requests' => 25
    ],
    'zendesk' => [
        'requests_per_minute' => 400,
        'concurrent_requests' => 10
    ],
    'dynamics' => [
        'requests_per_second' => 60,
        'concurrent_requests' => 52
    ]
];
```

### Connection Issues

#### Problem: `CONNECTION_TIMEOUT` errors intermittently

**Symptoms:**
- 504 Gateway Timeout errors
- Slow response times before failures

**Diagnosis:**
```bash
# Test connectivity to upstream platforms
./scripts/test-connectivity.sh salesforce
./scripts/test-connectivity.sh dynamics

# Check timeout configuration
grep -r "timeout" config/*.php
```

**Solutions:**

1. **Adjust timeout configuration:**
```php
// config/Gateway.php
public $httpClient = [
    'connect_timeout' => 10,
    'read_timeout' => 30,
    'total_timeout' => 45,
    'retries' => [
        'enabled' => true,
        'max_attempts' => 3,
        'retry_on' => [408, 500, 502, 503, 504]
    ]
];
```

2. **Implement circuit breaker pattern:**
```php
<?php
class CircuitBreaker
{
    const STATE_CLOSED = 'closed';
    const STATE_OPEN = 'open';
    const STATE_HALF_OPEN = 'half_open';
    
    public function execute(string $platform, callable $operation)
    {
        $state = $this->getState($platform);
        
        if ($state === self::STATE_OPEN) {
            if (!$this->shouldAttemptReset($platform)) {
                throw new SgCannedRestApiErrorException(
                    'PLATFORM_UNAVAILABLE',
                    $platform,
                    '*',
                    ['circuit_state' => 'open']
                );
            }
            $this->setState($platform, self::STATE_HALF_OPEN);
        }
        
        try {
            $result = $operation();
            $this->recordSuccess($platform);
            return $result;
        } catch (\Throwable $e) {
            $this->recordFailure($platform);
            throw $e;
        }
    }
}
```

### Multi-Platform Query Failures

#### Problem: `MULTI_GATEWAY_ERROR` with partial failures

**Symptoms:**
- 207 Multi-Status responses
- Some platforms returning data, others failing

**Diagnosis:**
```php
<?php
// Enable detailed multi-platform logging
log_message('debug', 'Multi-platform query starting', [
    'platforms' => $requestedPlatforms,
    'query' => $query
]);

foreach ($results as $platform => $result) {
    if ($result instanceof \Throwable) {
        log_message('error', "Platform {$platform} failed", [
            'error_type' => get_class($result),
            'message' => $result->getMessage(),
            'trace' => $result->getTraceAsString()
        ]);
    }
}
```

**Solutions:**

1. **Configure fallback behavior:**
```php
// config/Gateway.php
public $multiPlatform = [
    'fail_fast' => false, // Continue even if some platforms fail
    'minimum_success_count' => 1, // Require at least 1 successful response
    'timeout_per_platform' => 15,
    'parallel_execution' => true
];
```

2. **Implement graceful degradation:**
```php
<?php
public function queryMultiplePlatforms(array $platforms, string $query): array
{
    $results = $this->executeParallel($platforms, $query);
    
    $mgwError = null;
    if (!empty($results['errors'])) {
        $mgwError = new MgwError(
            'Some platforms experienced issues',
            $results['errors'],
            $results['successful_platforms']
        );
    }
    
    return [
        'data' => $results['data'],
        'metadata' => [
            'queried_platforms' => $platforms,
            'successful_platforms' => $results['successful_platforms'],
            'failed_platforms' => array_keys($results['errors']),
            'partial_success' => !empty($results['errors']) && !empty($results['data'])
        ],
        'warnings' => $mgwError ? $mgwError->toArray() : null
    ];
}
```

---

## Best Practices

### Error Handling in Client Applications

```javascript
// JavaScript client error handling example
async function queryGateway(platform, query) {
    try {
        const response = await fetch('/api/v1/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ platform, query })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            
            switch (errorData.error.code) {
                case 'AUTH_TOKEN_EXPIRED':
                    await refreshToken();
                    return queryGateway(platform, query); // Retry
                    
                case 'RATE_LIMIT_EXCEEDED':
                    const retryAfter = errorData.error.details.retry_after;
                    await sleep(retryAfter * 1000);
                    return queryGateway(platform, query); // Retry
                    
                case 'VALIDATION_FAILED':
                    throw new ValidationError(errorData.error.details.validation_errors);
                    
                default:
                    throw new GatewayError(errorData.error);
            }
        }
        
        return response.json();
    } catch (error) {
        if (error instanceof GatewayError) throw error;
        throw new NetworkError('Failed to connect to gateway');
    }
}
```

### Logging and Monitoring

```php
<?php
// Centralized error logging configuration
// config/Logger.php
public $errorHandlers = [
    'log_channel' => 'gateway_errors',
    'include_stack_trace' => true,
    'include_request_context' => true,
    'alert_thresholds' => [
        'AUTH_TOKEN_EXPIRED' => 100, // Alert if 100+ in 1 hour
        'PLATFORM_UNAVAILABLE' => 10, // Alert if 10+ in 5 minutes
        'RATE_LIMIT_EXCEEDED' => 50 // Alert if 50+ in 15 minutes
    ]
];
```

---

## Related Documentation

- [API Reference](/docs/api-reference.md) - Complete endpoint documentation
- [Authentication Guide](/docs/authentication.md) - OAuth and token management
- [Configuration Reference](/docs/configuration.md) - All 50 configuration variables
- [Platform Integration Guides](/docs/integrations/) - Platform-specific documentation