# Core Libraries Reference

## Overview

The platform-dgapi service is built on a foundation of purpose-built utility libraries that handle critical functionality across the application. These core libraries provide standardized approaches to DOM-based request/response handling, error management, database operations, and task processing workflows.

This reference guide provides comprehensive documentation for each core library, including usage patterns, method signatures, practical examples, and best practices. Understanding these libraries is essential for extending the platform-dgapi service or integrating with its disposition gateway workflows.

### Library Architecture

The core libraries follow a layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│              (Controllers, Business Logic)                  │
├─────────────────────────────────────────────────────────────┤
│                    Utility Layer                            │
│    ┌──────────┐  ┌──────────────┐  ┌──────────────────┐    │
│    │ DOMMaker │  │ DOMRequest   │  │ DOMResponse      │    │
│    └──────────┘  └──────────────┘  └──────────────────┘    │
│    ┌──────────┐  ┌──────────────┐  ┌──────────────────┐    │
│    │ APIUtils │  │ TasksD       │  │ DGAPIException   │    │
│    └──────────┘  └──────────────┘  └──────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                    Data Layer                               │
│    ┌──────────────────────┐  ┌─────────────────────────┐   │
│    │      XDatabase       │  │        Codes            │   │
│    └──────────────────────┘  └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## DOMMaker

The `DOMMaker` library provides utilities for creating and manipulating DOM (Document Object Model) structures used throughout the API for request and response handling. This library forms the foundation for the XML-based communication protocol used by the disposition gateway.

### Class Definition

```php
<?php
namespace DGAPI\Libraries;

class DOMMaker
{
    /**
     * @var \DOMDocument The internal DOM document instance
     */
    protected $document;
    
    /**
     * @var \DOMElement The root element of the document
     */
    protected $root;
    
    /**
     * @var string Default encoding for documents
     */
    protected $encoding = 'UTF-8';
}
```

### Constructor and Initialization

```php
<?php
// Create a new DOMMaker instance with default settings
$maker = new DOMMaker();

// Create with custom root element
$maker = new DOMMaker('DispositionResponse');

// Create with custom root element and namespace
$maker = new DOMMaker('DispositionResponse', 'http://api.example.com/disposition');
```

### Core Methods

#### createElement()

Creates a new DOM element with optional text content and attributes.

```php
<?php
/**
 * Create a new element
 * 
 * @param string $name Element name
 * @param string|null $value Optional text content
 * @param array $attributes Optional attributes
 * @return \DOMElement
 */
public function createElement(string $name, ?string $value = null, array $attributes = []): \DOMElement

// Usage examples
$element = $maker->createElement('TaskId', '12345');
$element = $maker->createElement('Status', 'completed', ['code' => '200']);
```

#### appendChild()

Appends a child element to a parent element or the root.

```php
<?php
/**
 * Append child to parent or root
 * 
 * @param \DOMElement $child The child element to append
 * @param \DOMElement|null $parent Parent element (null for root)
 * @return \DOMElement The appended element
 */
public function appendChild(\DOMElement $child, ?\DOMElement $parent = null): \DOMElement

// Usage
$task = $maker->createElement('Task');
$maker->appendChild($maker->createElement('Id', '123'), $task);
$maker->appendChild($maker->createElement('Type', 'SMS'), $task);
$maker->appendChild($task);
```

#### addCDATA()

Adds CDATA section for content that may contain special characters.

```php
<?php
/**
 * Add CDATA section to element
 * 
 * @param \DOMElement $element Target element
 * @param string $content CDATA content
 * @return \DOMElement
 */
public function addCDATA(\DOMElement $element, string $content): \DOMElement

// Usage for message content with special characters
$message = $maker->createElement('MessageBody');
$maker->addCDATA($message, 'Hello <Customer>! Your order #123 is ready.');
```

#### toXML()

Generates the final XML string from the DOM structure.

```php
<?php
/**
 * Generate XML string
 * 
 * @param bool $formatOutput Whether to format with indentation
 * @return string XML string
 */
public function toXML(bool $formatOutput = true): string

// Generate formatted XML
$xml = $maker->toXML();

// Generate compact XML for transmission
$xml = $maker->toXML(false);
```

### Complete Example

```php
<?php
use DGAPI\Libraries\DOMMaker;

// Build a disposition response
$maker = new DOMMaker('DispositionGatewayResponse');

// Add header information
$header = $maker->createElement('Header');
$maker->appendChild($maker->createElement('Version', '1.0'), $header);
$maker->appendChild($maker->createElement('Timestamp', date('c')), $header);
$maker->appendChild($header);

// Add task result
$task = $maker->createElement('TaskResult');
$maker->appendChild($maker->createElement('TaskId', 'TSK-2024-001'), $task);
$maker->appendChild($maker->createElement('Status', 'completed'), $task);
$maker->appendChild($maker->createElement('Code', '200'), $task);

// Add message with CDATA
$message = $maker->createElement('Message');
$maker->addCDATA($message, 'Task processed successfully');
$maker->appendChild($message, $task);

$maker->appendChild($task);

// Output
echo $maker->toXML();
```

**Output:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<DispositionGatewayResponse>
  <Header>
    <Version>1.0</Version>
    <Timestamp>2024-01-15T10:30:00+00:00</Timestamp>
  </Header>
  <TaskResult>
    <TaskId>TSK-2024-001</TaskId>
    <Status>completed</Status>
    <Code>200</Code>
    <Message><![CDATA[Task processed successfully]]></Message>
  </TaskResult>
</DispositionGatewayResponse>
```

---

## DOMRequest

The `DOMRequest` library handles parsing and validation of incoming XML requests to the disposition gateway API. It provides structured access to request data with built-in validation and error handling.

### Class Definition

```php
<?php
namespace DGAPI\Libraries;

class DOMRequest
{
    /**
     * @var \DOMDocument Parsed request document
     */
    protected $document;
    
    /**
     * @var \DOMXPath XPath query interface
     */
    protected $xpath;
    
    /**
     * @var array Parsed request parameters
     */
    protected $params = [];
    
    /**
     * @var array Validation errors
     */
    protected $errors = [];
}
```

### Initialization Methods

```php
<?php
/**
 * Parse XML request from string
 * 
 * @param string $xmlString Raw XML string
 * @throws DGAPIException On parse failure
 * @return self
 */
public static function fromString(string $xmlString): self

/**
 * Parse XML request from file
 * 
 * @param string $filePath Path to XML file
 * @throws DGAPIException On file not found or parse failure
 * @return self
 */
public static function fromFile(string $filePath): self

/**
 * Parse XML from PHP input stream
 * 
 * @return self
 */
public static function fromInput(): self
```

### Data Access Methods

#### getValue()

Retrieves a single value from the request using XPath.

```php
<?php
/**
 * Get single value by XPath
 * 
 * @param string $xpath XPath expression
 * @param mixed $default Default value if not found
 * @return mixed
 */
public function getValue(string $xpath, $default = null)

// Usage
$taskId = $request->getValue('//TaskId');
$phone = $request->getValue('//Recipient/Phone', 'N/A');
```

#### getValues()

Retrieves multiple values matching an XPath expression.

```php
<?php
/**
 * Get multiple values by XPath
 * 
 * @param string $xpath XPath expression
 * @return array
 */
public function getValues(string $xpath): array

// Get all recipient phone numbers
$phones = $request->getValues('//Recipients/Recipient/Phone');
```

#### getNode()

Retrieves a DOM node for complex data extraction.

```php
<?php
/**
 * Get DOM node by XPath
 * 
 * @param string $xpath XPath expression
 * @return \DOMNode|null
 */
public function getNode(string $xpath): ?\DOMNode

// Get task node for further processing
$taskNode = $request->getNode('//Task');
if ($taskNode) {
    foreach ($taskNode->childNodes as $child) {
        // Process child nodes
    }
}
```

#### toArray()

Converts the entire request to an associative array.

```php
<?php
/**
 * Convert request to array
 * 
 * @param string|null $rootPath Optional root XPath
 * @return array
 */
public function toArray(?string $rootPath = null): array

// Get entire request as array
$data = $request->toArray();

// Get specific section as array
$taskData = $request->toArray('//Task');
```

### Validation Methods

```php
<?php
/**
 * Validate required fields exist
 * 
 * @param array $fields Array of required XPath expressions
 * @return bool
 */
public function validateRequired(array $fields): bool

/**
 * Get validation errors
 * 
 * @return array
 */
public function getErrors(): array

// Usage
$required = [
    '//TaskId',
    '//TaskType',
    '//Recipient/Phone'
];

if (!$request->validateRequired($required)) {
    $errors = $request->getErrors();
    throw new DGAPIException('Validation failed: ' . implode(', ', $errors));
}
```

### Complete Example

```php
<?php
use DGAPI\Libraries\DOMRequest;
use DGAPI\Libraries\DGAPIException;

try {
    // Parse incoming request
    $request = DOMRequest::fromInput();
    
    // Validate required fields
    $required = [
        '//DispositionRequest/TaskId',
        '//DispositionRequest/TaskType',
        '//DispositionRequest/Action'
    ];
    
    if (!$request->validateRequired($required)) {
        throw new DGAPIException(
            'Missing required fields: ' . implode(', ', $request->getErrors()),
            Codes::ERR_VALIDATION_FAILED
        );
    }
    
    // Extract task data
    $taskId = $request->getValue('//DispositionRequest/TaskId');
    $taskType = $request->getValue('//DispositionRequest/TaskType');
    $action = $request->getValue('//DispositionRequest/Action');
    
    // Extract optional parameters with defaults
    $priority = $request->getValue('//DispositionRequest/Priority', 'normal');
    $retryCount = (int) $request->getValue('//DispositionRequest/RetryCount', '3');
    
    // Get all recipients
    $recipients = $request->getValues('//DispositionRequest/Recipients/Recipient/Address');
    
    // Process the request...
    
} catch (DGAPIException $e) {
    // Handle parsing or validation errors
    log_message('error', 'Request processing failed: ' . $e->getMessage());
}
```

---

## DOMResponse

The `DOMResponse` library provides a fluent interface for building and sending XML responses from the disposition gateway API. It extends DOMMaker with response-specific functionality.

### Class Definition

```php
<?php
namespace DGAPI\Libraries;

class DOMResponse extends DOMMaker
{
    /**
     * @var int HTTP status code
     */
    protected $statusCode = 200;
    
    /**
     * @var array Response headers
     */
    protected $headers = [];
    
    /**
     * @var string Response status (success/error)
     */
    protected $status = 'success';
    
    /**
     * @var string|null Error message if applicable
     */
    protected $errorMessage = null;
    
    /**
     * @var int|null Error code if applicable
     */
    protected $errorCode = null;
}
```

### Builder Methods

#### setStatus()

Sets the response status and optional message.

```php
<?php
/**
 * Set response status
 * 
 * @param string $status Status string (success/error/pending)
 * @param string|null $message Optional status message
 * @return self
 */
public function setStatus(string $status, ?string $message = null): self

// Usage
$response->setStatus('success', 'Task processed successfully');
$response->setStatus('error', 'Invalid task type specified');
```

#### setError()

Configures an error response.

```php
<?php
/**
 * Set error response
 * 
 * @param int $code Error code
 * @param string $message Error message
 * @param array $details Additional error details
 * @return self
 */
public function setError(int $code, string $message, array $details = []): self

// Usage
$response->setError(
    Codes::ERR_TASK_NOT_FOUND,
    'Task not found',
    ['taskId' => 'TSK-123', 'searchTime' => '2024-01-15T10:30:00Z']
);
```

#### addData()

Adds data elements to the response.

```php
<?php
/**
 * Add data to response
 * 
 * @param string $key Data key/element name
 * @param mixed $value Data value (scalar or array)
 * @return self
 */
public function addData(string $key, $value): self

// Add simple values
$response->addData('TaskId', 'TSK-2024-001');
$response->addData('ProcessedAt', date('c'));

// Add complex data structures
$response->addData('TaskResult', [
    'Status' => 'completed',
    'Duration' => '1.5s',
    'Retries' => 0
]);
```

#### addDataArray()

Adds an array of items as repeated elements.

```php
<?php
/**
 * Add array of items
 * 
 * @param string $containerName Container element name
 * @param string $itemName Individual item element name
 * @param array $items Array of items
 * @return self
 */
public function addDataArray(string $containerName, string $itemName, array $items): self

// Add multiple results
$results = [
    ['Id' => '1', 'Status' => 'sent'],
    ['Id' => '2', 'Status' => 'failed'],
    ['Id' => '3', 'Status' => 'pending']
];
$response->addDataArray('NotificationResults', 'Result', $results);
```

### Output Methods

```php
<?php
/**
 * Send response to client
 * 
 * @param bool $exit Whether to exit after sending
 * @return void
 */
public function send(bool $exit = true): void

/**
 * Get response as string without sending
 * 
 * @return string
 */
public function toString(): string

/**
 * Set HTTP status code
 * 
 * @param int $code HTTP status code
 * @return self
 */
public function setHttpStatus(int $code): self

/**
 * Add response header
 * 
 * @param string $name Header name
 * @param string $value Header value
 * @return self
 */
public function addHeader(string $name, string $value): self
```

### Response Templates

The library provides pre-built templates for common response types:

```php
<?php
/**
 * Create success response
 * 
 * @param string $message Success message
 * @param array $data Additional data
 * @return self
 */
public static function success(string $message, array $data = []): self

/**
 * Create error response
 * 
 * @param int $code Error code
 * @param string $message Error message
 * @return self
 */
public static function error(int $code, string $message): self

/**
 * Create task result response
 * 
 * @param string $taskId Task identifier
 * @param string $status Task status
 * @param array $details Additional details
 * @return self
 */
public static function taskResult(string $taskId, string $status, array $details = []): self
```

### Complete Example

```php
<?php
use DGAPI\Libraries\DOMResponse;
use DGAPI\Libraries\Codes;

// Build a comprehensive response
$response = new DOMResponse('DispositionGatewayResponse');

// Set success status
$response->setStatus('success', 'Disposition processed successfully');

// Add task information
$response->addData('Task', [
    'Id' => 'TSK-2024-001',
    'Type' => 'SMS',
    'Status' => 'completed',
    'ProcessedAt' => date('c')
]);

// Add notification results
$notifications = [
    [
        'Recipient' => '+1234567890',
        'Status' => 'delivered',
        'MessageId' => 'MSG-001',
        'DeliveredAt' => date('c')
    ],
    [
        'Recipient' => '+0987654321',
        'Status' => 'pending',
        'MessageId' => 'MSG-002',
        'ScheduledFor' => date('c', strtotime('+5 minutes'))
    ]
];
$response->addDataArray('Notifications', 'Notification', $notifications);

// Add metadata
$response->addData('Metadata', [
    'ProcessingTime' => '0.245s',
    'ServerNode' => 'dgapi-node-01',
    'RequestId' => uniqid('REQ-')
]);

// Send response
$response->setHttpStatus(200)
         ->addHeader('X-Request-Id', 'REQ-12345')
         ->send();
```

**Output:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<DispositionGatewayResponse>
  <Status>success</Status>
  <Message>Disposition processed successfully</Message>
  <Task>
    <Id>TSK-2024-001</Id>
    <Type>SMS</Type>
    <Status>completed</Status>
    <ProcessedAt>2024-01-15T10:30:00+00:00</ProcessedAt>
  </Task>
  <Notifications>
    <Notification>
      <Recipient>+1234567890</Recipient>
      <Status>delivered</Status>
      <MessageId>MSG-001</MessageId>
      <DeliveredAt>2024-01-15T10:30:00+00:00</DeliveredAt>
    </Notification>
    <Notification>
      <Recipient>+0987654321</Recipient>
      <Status>pending</Status>
      <MessageId>MSG-002</MessageId>
      <ScheduledFor>2024-01-15T10:35:00+00:00</ScheduledFor>
    </Notification>
  </Notifications>
  <Metadata>
    <ProcessingTime>0.245s</ProcessingTime>
    <ServerNode>dgapi-node-01</ServerNode>
    <RequestId>REQ-65a12345abcde</RequestId>
  </Metadata>
</DispositionGatewayResponse>
```

---

## DGAPIException

The `DGAPIException` class provides a standardized exception handling mechanism for the disposition gateway API. It extends PHP's base Exception class with additional context for error codes, HTTP status mapping, and structured error data.

### Class Definition

```php
<?php
namespace DGAPI\Libraries;

class DGAPIException extends \Exception
{
    /**
     * @var int Application-specific error code
     */
    protected $errorCode;
    
    /**
     * @var int HTTP status code
     */
    protected $httpStatus;
    
    /**
     * @var array Additional error context
     */
    protected $context = [];
    
    /**
     * @var bool Whether this error is recoverable
     */
    protected $recoverable = false;
}
```

### Constructor

```php
<?php
/**
 * Create new DGAPI exception
 * 
 * @param string $message Error message
 * @param int $errorCode Application error code (from Codes class)
 * @param int $httpStatus HTTP status code (default: 500)
 * @param array $context Additional context data
 * @param \Throwable|null $previous Previous exception
 */
public function __construct(
    string $message,
    int $errorCode = Codes::ERR_UNKNOWN,
    int $httpStatus = 500,
    array $context = [],
    ?\Throwable $previous = null
)
```

### Usage Examples

```php
<?php
use DGAPI\Libraries\DGAPIException;
use DGAPI\Libraries\Codes;

// Basic exception
throw new DGAPIException(
    'Task not found',
    Codes::ERR_TASK_NOT_FOUND,
    404
);

// Exception with context
throw new DGAPIException(
    'SMS delivery failed',
    Codes::ERR_SMS_DELIVERY_FAILED,
    502,
    [
        'taskId' => 'TSK-001',
        'recipient' => '+1234567890',
        'provider' => 'twilio',
        'providerError' => 'Invalid phone number format'
    ]
);

// Validation exception
throw new DGAPIException(
    'Invalid request parameters',
    Codes::ERR_VALIDATION_FAILED,
    400,
    [
        'fields' => [
            'phone' => 'Required field missing',
            'message' => 'Exceeds maximum length of 160 characters'
        ]
    ]
);
```

### Exception Methods

```php
<?php
/**
 * Get application error code
 * @return int
 */
public function getErrorCode(): int

/**
 * Get HTTP status code
 * @return int
 */
public function getHttpStatus(): int

/**
 * Get error context
 * @return array
 */
public function getContext(): array

/**
 * Check if error is recoverable
 * @return bool
 */
public function isRecoverable(): bool

/**
 * Convert to array for response
 * @return array
 */
public function toArray(): array

/**
 * Convert to DOMResponse
 * @return DOMResponse
 */
public function toResponse(): DOMResponse
```

### Exception Handling Pattern

```php
<?php
use DGAPI\Libraries\DGAPIException;
use DGAPI\Libraries\DOMResponse;
use DGAPI\Libraries\Codes;

class DispositionController extends CI_Controller
{
    public function processTask()
    {
        try {
            // Parse request
            $request = DOMRequest::fromInput();
            
            // Validate
            $this->validateRequest($request);
            
            // Process
            $result = $this->taskService->process($request);
            
            // Respond
            DOMResponse::success('Task processed', $result)->send();
            
        } catch (DGAPIException $e) {
            // Handle known application errors
            log_message('error', sprintf(
                'DGAPI Error [%d]: %s | Context: %s',
                $e->getErrorCode(),
                $e->getMessage(),
                json_encode($e->getContext())
            ));
            
            $e->toResponse()->send();
            
        } catch (\Exception $e) {
            // Handle unexpected errors
            log_message('critical', 'Unexpected error: ' . $e->getMessage());
            
            $error = new DGAPIException(
                'Internal server error',
                Codes::ERR_INTERNAL,
                500,
                ['originalError' => $e->getMessage()]
            );
            
            $error->toResponse()->send();
        }
    }
}
```

### Pre-defined Exception Factories

```php
<?php
class DGAPIException extends \Exception
{
    /**
     * Create validation exception
     */
    public static function validationFailed(array $errors): self
    {
        return new self(
            'Validation failed',
            Codes::ERR_VALIDATION_FAILED,
            400,
            ['validationErrors' => $errors]
        );
    }
    
    /**
     * Create not found exception
     */
    public static function notFound(string $resource, string $identifier): self
    {
        return new self(
            sprintf('%s not found: %s', $resource, $identifier),
            Codes::ERR_NOT_FOUND,
            404,
            ['resource' => $resource, 'identifier' => $identifier]
        );
    }
    
    /**
     * Create authentication exception
     */
    public static function unauthorized(string $reason = 'Invalid credentials'): self
    {
        return new self(
            $reason,
            Codes::ERR_UNAUTHORIZED,
            401
        );
    }
    
    /**
     * Create rate limit exception
     */
    public static function rateLimitExceeded(int $retryAfter = 60): self
    {
        return new self(
            'Rate limit exceeded',
            Codes::ERR_RATE_LIMITED,
            429,
            ['retryAfter' => $retryAfter]
        );
    }
}
```

---

## Codes (Error/Status Codes)

The `Codes` class defines all error codes, status codes, and message templates used throughout the disposition gateway API. This centralized approach ensures consistency in error handling and response formatting.

### Error Code Ranges

| Range | Category | Description |
|-------|----------|-------------|
| 1000-1099 | Authentication | Token and credential errors |
| 1100-1199 | Validation | Request validation errors |
| 1200-1299 | Task Processing | Task execution errors |
| 1300-1399 | SMS | SMS-specific errors |
| 1400-1499 | Email | Email-specific errors |
| 1500-1599 | Voicemail | Voicemail-specific errors |
| 1600-1699 | CDR | CDR processing errors |
| 1700-1799 | Callback | Callback-specific errors |
| 1800-1899 | Database | Database operation errors |
| 1900-1999 | External Service | Third-party service errors |
| 9000-9999 | System | Internal system errors |

### Error Code Definitions

```php
<?php
namespace DGAPI\Libraries;

class Codes
{
    // =========================================
    // Authentication Errors (1000-1099)
    // =========================================
    
    /** @var int Missing authentication token */
    const ERR_TOKEN_MISSING = 1000;
    
    /** @var int Invalid or malformed token */
    const ERR_TOKEN_INVALID = 1001;
    
    /** @var int Token has expired */
    const ERR_TOKEN_EXPIRED = 1002;
    
    /** @var int Token lacks required permissions */
    const ERR_TOKEN_INSUFFICIENT_PERMISSIONS = 1003;
    
    /** @var int Account is suspended */
    const ERR_ACCOUNT_SUSPENDED = 1010;
    
    /** @var int IP address not allowed */
    const ERR_IP_NOT_ALLOWED = 1011;
    
    // =========================================
    // Validation Errors (1100-1199)
    // =========================================
    
    /** @var int Generic validation failure */
    const ERR_VALIDATION_FAILED = 1100;
    
    /** @var int Required field missing */
    const ERR_REQUIRED_FIELD_MISSING = 1101;
    
    /** @var int Invalid field format */
    const ERR_INVALID_FORMAT = 1102;
    
    /** @var int Value out of allowed range */
    const ERR_VALUE_OUT_OF_RANGE = 1103;
    
    /** @var int Invalid XML structure */
    const ERR_INVALID_XML = 1110;
    
    /** @var int XML schema validation failed */
    const ERR_XML_SCHEMA_FAILED = 1111;
    
    // =========================================
    // Task Processing Errors (1200-1299)
    // =========================================
    
    /** @var int Task not found */
    const ERR_TASK_NOT_FOUND = 1200;
    
    /** @var int Invalid task type */
    const ERR_INVALID_TASK_TYPE = 1201;
    
    /** @var int Task already processed */
    const ERR_TASK_ALREADY_PROCESSED = 1202;
    
    /** @var int Task processing timeout */
    const ERR_TASK_TIMEOUT = 1203;
    
    /** @var int Task queue full */
    const ERR_TASK_QUEUE_FULL = 1204;
    
    /** @var int Task cancelled */
    const ERR_TASK_CANCELLED = 1205;
    
    // =========================================
    // SMS Errors (1300-1399)
    // =========================================
    
    /** @var int SMS delivery failed */
    const ERR_SMS_DELIVERY_FAILED = 1300;
    
    /** @var int Invalid phone number */
    const ERR_SMS_INVALID_PHONE = 1301;
    
    /** @var int Message too long */
    const ERR_SMS_MESSAGE_TOO_LONG = 1302;
    
    /** @var int SMS provider error */
    const ERR_SMS_PROVIDER_ERROR = 1310;
    
    /** @var int SMS rate limit exceeded */
    const ERR_SMS_RATE_LIMITED = 1311;
    
    // =========================================
    // Email Errors (1400-1499)
    // =========================================
    
    /** @var int Email delivery failed */
    const ERR_EMAIL_DELIVERY_FAILED = 1400;
    
    /** @var int Invalid email address */
    const ERR_EMAIL_INVALID_ADDRESS = 1401;
    
    /** @var int Email content too large */
    const ERR_EMAIL_CONTENT_TOO_LARGE = 1402;
    
    /** @var int Email template not found */
    const ERR_EMAIL_TEMPLATE_NOT_FOUND = 1410;
    
    // =========================================
    // Database Errors (1800-1899)
    // =========================================
    
    /** @var int Database connection failed */
    const ERR_DB_CONNECTION_FAILED = 1800;
    
    /** @var int Database query failed */
    const ERR_DB_QUERY_FAILED = 1801;
    
    /** @var int Record not found */
    const ERR_DB_RECORD_NOT_FOUND = 1802;
    
    /** @var int Duplicate record */
    const ERR_DB_DUPLICATE = 1803;
    
    // =========================================
    // System Errors (9000-9999)
    // =========================================
    
    /** @var int Unknown error */
    const ERR_UNKNOWN = 9000;
    
    /** @var int Internal server error */
    const ERR_INTERNAL = 9001;
    
    /** @var int Service unavailable */
    const ERR_SERVICE_UNAVAILABLE = 9002;
    
    /** @var int Rate limit exceeded */
    const ERR_RATE_LIMITED = 9003;
}
```

### Status Codes

```php
<?php
class Codes
{
    // =========================================
    // Task Status Codes
    // =========================================
    
    /** @var string Task is pending processing */
    const STATUS_PENDING = 'pending';
    
    /** @var string Task is currently processing */
    const STATUS_PROCESSING = 'processing';
    
    /** @var string Task completed successfully */
    const STATUS_COMPLETED = 'completed';
    
    /** @var string Task failed */
    const STATUS_FAILED = 'failed';
    
    /** @var string Task was cancelled */
    const STATUS_CANCELLED = 'cancelled';
    
    /** @var string Task is scheduled for future */
    const STATUS_SCHEDULED = 'scheduled';
    
    /** @var string Task is waiting for retry */
    const STATUS_RETRY_PENDING = 'retry_pending';
    
    // =========================================
    // Disposition Status Codes
    // =========================================
    
    /** @var string Disposition successful */
    const DISP_SUCCESS = 'success';
    
    /** @var string Disposition failed */
    const DISP_FAILURE = 'failure';
    
    /** @var string No answer */
    const DISP_NO_ANSWER = 'no_answer';
    
    /** @var string Busy */
    const DISP_BUSY = 'busy';
    
    /** @var string Voicemail reached */
    const DISP_VOICEMAIL = 'voicemail';
    
    /** @var string Callback requested */
    const DISP_CALLBACK = 'callback';
}
```

### Error Message Templates

```php
<?php
class Codes
{
    /**
     * Error message templates
     * @var array
     */
    protected static $messages = [
        self::ERR_TOKEN_MISSING => 'Authentication token is required',
        self::ERR_TOKEN_INVALID => 'The provided authentication token is invalid',
        self::ERR_TOKEN_EXPIRED => 'The authentication token has expired',
        self::ERR_VALIDATION_FAILED => 'Request validation failed',
        self::ERR_TASK_NOT_FOUND => 'The requested task was not found',
        self::ERR_SMS_DELIVERY_FAILED => 'SMS delivery failed',
        self::ERR_DB_CONNECTION_FAILED => 'Database connection failed',
        self::ERR_UNKNOWN => 'An unknown error occurred',
        // ... more messages
    ];
    
    /**
     * Get error message for code
     * 
     * @param int $code Error code
     * @param array $replacements Placeholder replacements
     * @return string
     */
    public static function getMessage(int $code, array $replacements = []): string
    {
        $message = self::$messages[$code] ?? self::$messages[self::ERR_UNKNOWN];
        
        foreach ($replacements as $key => $value) {
            $message = str_replace("{{$key}}", $value, $message);
        }
        
        return $message;
    }
    
    /**
     * Get HTTP status code for error code
     * 
     * @param int $code Error code
     * @return int HTTP status code
     */
    public static function getHttpStatus(int $code): int
    {
        $mapping = [
            self::ERR_TOKEN_MISSING => 401,
            self::ERR_TOKEN_INVALID => 401,
            self::ERR_TOKEN_EXPIRED => 401,
            self::ERR_VALIDATION_FAILED => 400,
            self::ERR_TASK_NOT_FOUND => 404,
            self::ERR_DB_RECORD_NOT_FOUND => 404,
            self::ERR_RATE_LIMITED => 429,
            self::ERR_SERVICE_UNAVAILABLE => 503,
        ];
        
        return $mapping[$code] ?? 500;
    }
}
```

### Usage Examples

```php
<?php
use DGAPI\Libraries\Codes;
use DGAPI\Libraries\DGAPIException;

// Get error message
$message = Codes::getMessage(Codes::ERR_TASK_NOT_FOUND);
// Returns: "The requested task was not found"

// Get message with replacements
$message = Codes::getMessage(Codes::ERR_SMS_INVALID_PHONE, [
    'phone' => '+invalid123'
]);

// Get HTTP status for error
$httpStatus = Codes::getHttpStatus(Codes::ERR_VALIDATION_FAILED);
// Returns: 400

// Use in exception
throw new DGAPIException(
    Codes::getMessage(Codes::ERR_TASK_NOT_FOUND),
    Codes::ERR_TASK_NOT_FOUND,
    Codes::getHttpStatus(Codes::ERR_TASK_NOT_FOUND)
);

// Check task status
if ($task->status === Codes::STATUS_COMPLETED) {
    // Task is done
}
```

---

## APIUtils

The `APIUtils` class provides a collection of utility functions commonly needed across the disposition gateway API, including string manipulation, date handling, phone number formatting, and request/response helpers.

### String Utilities

```php
<?php
namespace DGAPI\Libraries;

class APIUtils
{
    /**
     * Generate unique identifier
     * 
     * @param string $prefix Optional prefix
     * @return string
     */
    public static function generateId(string $prefix = ''): string
    {
        $id = sprintf(
            '%s%s-%s',
            $prefix ? $prefix . '-' : '',
            date('Ymd'),
            bin2hex(random_bytes(8))
        );
        return strtoupper($id);
    }
    
    /**
     * Sanitize string for XML
     * 
     * @param string $string Input string
     * @return string
     */
    public static function sanitizeForXml(string $string): string
    {
        // Remove invalid XML characters
        $string = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/', '', $string);
        return htmlspecialchars($string, ENT_XML1 | ENT_QUOTES, 'UTF-8');
    }
    
    /**
     * Truncate string to length
     * 
     * @param string $string Input string
     * @param int $length Maximum length
     * @param string $suffix Suffix for truncated strings
     * @return string
     */
    public static function truncate(string $string, int $length, string $suffix = '...'): string
    {
        if (mb_strlen($string) <= $length) {
            return $string;
        }
        return mb_substr($string, 0, $length - mb_strlen($suffix)) . $suffix;
    }
    
    /**
     * Generate slug from string
     * 
     * @param string $string Input string
     * @return string
     */
    public static function slugify(string $string): string
    {
        $string = transliterator_transliterate('Any-Latin; Latin-ASCII', $string);
        $string = preg_replace('/[^a-zA-Z0-9\s-]/', '', $string);
        $string = preg_replace('/[\s-]+/', '-', $string);
        return strtolower(trim($string, '-'));
    }
}
```

### Phone Number Utilities

```php
<?php
class APIUtils
{
    /**
     * Normalize phone number to E.164 format
     * 
     * @param string $phone Phone number
     * @param string $defaultCountry Default country code (e.g., 'US')
     * @return string|null Normalized number or null if invalid
     */
    public static function normalizePhone(string $phone, string $defaultCountry = 'US'): ?string
    {
        // Remove all non-digit characters except leading +
        $phone = preg_replace('/[^\d+]/', '', $phone);
        
        // Handle different formats
        if (strpos($phone, '+') === 0) {
            // Already has country code
            return $phone;
        }
        
        // Add country code based on length and country
        $countryCodes = [
            'US' => '+1',
            'UK' => '+44',
            'AU' => '+61',
            'CA' => '+1',
        ];
        
        $prefix = $countryCodes[$defaultCountry] ?? '+1';
        
        // US/CA numbers - strip leading 1 if present
        if (in_array($defaultCountry, ['US', 'CA'])) {
            if (strlen($phone) === 11 && $phone[0] === '1') {
                $phone = substr($phone, 1);
            }
            if (strlen($phone) === 10) {
                return $prefix . $phone;
            }
        }
        
        return null; // Invalid format
    }
    
    /**
     * Validate phone number format
     * 
     * @param string $phone Phone number
     * @return bool
     */
    public static function isValidPhone(string $phone): bool
    {
        // E.164 format: + followed by 7-15 digits
        return preg_match('/^\+[1-9]\d{6,14}$/', $phone) === 1;
    }
    
    /**
     * Format phone for display
     * 
     * @param string $phone E.164 phone number
     * @return string
     */
    public static function formatPhoneDisplay(string $phone): string
    {
        // US/CA format: +1 (XXX) XXX-XXXX
        if (preg_match('/^\+1(\d{3})(\d{3})(\d{4})$/', $phone, $matches)) {
            return sprintf('+1 (%s) %s-%s', $matches[1], $matches[2], $matches[3]);
        }
        
        return $phone;
    }
}
```

### Date/Time Utilities

```php
<?php
class APIUtils
{
    /**
     * Get current timestamp in ISO 8601 format
     * 
     * @return string
     */
    public static function now(): string
    {
        return date('c');
    }
    
    /**
     * Parse various date formats to timestamp
     * 
     * @param string $dateString Date string
     * @return int|null Unix timestamp or null
     */
    public static function parseDate(string $dateString): ?int
    {
        $timestamp = strtotime($dateString);
        return $timestamp !== false ? $timestamp : null;
    }
    
    /**
     * Format timestamp for database
     * 
     * @param int|null $timestamp Unix timestamp (null for now)
     * @return string
     */
    public static function formatForDb(?int $timestamp = null): string
    {
        return date('Y-m-d H:i:s', $timestamp ?? time());
    }
    
    /**
     * Calculate time difference in human-readable format
     * 
     * @param int $timestamp Target timestamp
     * @param int|null $reference Reference timestamp (null for now)
     * @return string
     */
    public static function timeAgo(int $timestamp, ?int $reference = null): string
    {
        $reference = $reference ?? time();
        $diff = $reference - $timestamp;
        
        if ($diff < 60) return $diff . ' seconds ago';
        if ($diff < 3600) return floor($diff / 60) . ' minutes ago';
        if ($diff < 86400) return floor($diff / 3600) . ' hours ago';
        if ($diff < 604800) return floor($diff / 86400) . ' days ago';
        
        return date('M j, Y', $timestamp);
    }
    
    /**
     * Check if timestamp is within business hours
     * 
     * @param int|null $timestamp Timestamp to check
     * @param string $timezone Timezone
     * @param int $startHour Business start hour (24h)
     * @param int $endHour Business end hour (24h)
     * @return bool
     */
    public static function isBusinessHours(
        ?int $timestamp = null,
        string $timezone = 'America/New_York',
        int $startHour = 9,
        int $endHour = 17
    ): bool {
        $dt = new \DateTime('@' . ($timestamp ?? time()));
        $dt->setTimezone(new \DateTimeZone($timezone));
        
        $hour = (int) $dt->format('G');
        $dayOfWeek = (int) $dt->format('N');
        
        // Monday-Friday, 9-17
        return $dayOfWeek <= 5 && $hour >= $startHour && $hour < $endHour;
    }
}
```

### Request/Response Utilities

```php
<?php
class APIUtils
{
    /**
     * Get client IP address
     * 
     * @return string
     */
    public static function getClientIp(): string
    {
        $headers = [
            'HTTP_CF_CONNECTING_IP',  // Cloudflare
            'HTTP_X_FORWARDED_FOR',
            'HTTP_X_REAL_IP',
            'REMOTE_ADDR'
        ];
        
        foreach ($headers as $header) {
            if (!empty($_SERVER[$header])) {
                $ip = $_SERVER[$header];
                // Handle comma-separated list (X-Forwarded-For)
                if (strpos($ip, ',') !== false) {
                    $ip = trim(explode(',', $ip)[0]);
                }
                if (filter_var($ip, FILTER_VALIDATE_IP)) {
                    return $ip;
                }
            }
        }
        
        return '0.0.0.0';
    }
    
    /**
     * Get request header
     * 
     * @param string $name Header name
     * @param string|null $default Default value
     * @return string|null
     */
    public static function getHeader(string $name, ?string $default = null): ?string
    {
        $key = 'HTTP_' . strtoupper(str_replace('-', '_', $name));
        return $_SERVER[$key] ?? $default;
    }
    
    /**
     * Extract bearer token from Authorization header
     * 
     * @return string|null
     */
    public static function getBearerToken(): ?string
    {
        $header = self::getHeader('Authorization');
        if ($header && preg_match('/Bearer\s+(.+)$/i', $header, $matches)) {
            return $matches[1];
        }
        return null;
    }
    
    /**
     * Generate secure random token
     * 
     * @param int $length Token length
     * @return string
     */
    public static function generateToken(int $length = 32): string
    {
        return bin2hex(random_bytes($length / 2));
    }
    
    /**
     * Calculate request signature for verification
     * 
     * @param string $payload Request payload
     * @param string $secret Signing secret
     * @param string $algorithm Hash algorithm
     * @return string
     */
    public static function signPayload(
        string $payload,
        string $secret,
        string $algorithm = 'sha256'
    ): string {
        return hash_hmac($algorithm, $payload, $secret);
    }
}
```

### Array Utilities

```php
<?php
class APIUtils
{
    /**
     * Get nested array value using dot notation
     * 
     * @param array $array Source array
     * @param string $key Dot-notation key (e.g., 'user.profile.name')
     * @param mixed $default Default value
     * @return mixed
     */
    public static function arrayGet(array $array, string $key, $default = null)
    {
        $keys = explode('.', $key);
        $value = $array;
        
        foreach ($keys as $k) {
            if (!is_array($value) || !array_key_exists($k, $value)) {
                return $default;
            }
            $value = $value[$k];
        }
        
        return $value;
    }
    
    /**
     * Set nested array value using dot notation
     * 
     * @param array $array Target array (modified by reference)
     * @param string $key Dot-notation key
     * @param mixed $value Value to set
     * @return void
     */
    public static function arraySet(array &$array, string $key, $value): void
    {
        $keys = explode('.', $key);
        $current = &$array;
        
        foreach ($keys as $k) {
            if (!isset($current[$k]) || !is_array($current[$k])) {
                $current[$k] = [];
            }
            $current = &$current[$k];
        }
        
        $current = $value;
    }
    
    /**
     * Filter array to only specified keys
     * 
     * @param array $array Source array
     * @param array $keys Keys to keep
     * @return array
     */
    public static function arrayOnly(array $array, array $keys): array
    {
        return array_intersect_key($array, array_flip($keys));
    }
    
    /**
     * Remove specified keys from array
     * 
     * @param array $array Source array
     * @param array $keys Keys to remove
     * @return array
     */
    public static function arrayExcept(array $array, array $keys): array
    {
        return array_diff_key($array, array_flip($keys));
    }
}
```

---

## XDatabase

The `XDatabase` library provides an extended database abstraction layer built on top of CodeIgniter's database class. It offers enhanced query building, connection pooling, transaction management, and query logging capabilities.

### Configuration

```php
<?php
// Database configuration (application/config/database.php)
$db['default'] = [
    'dsn'      => '',
    'hostname' => getenv('DB_HOST') ?: 'localhost',
    'username' => getenv('DB_USER') ?: 'dgapi_user',
    'password' => getenv('DB_PASS') ?: '',
    'database' => getenv('DB_NAME') ?: 'dgapi_db',
    'dbdriver' => 'mysqli',
    'dbprefix' => 'dgapi_',
    'pconnect' => FALSE,
    'db_debug' => (ENVIRONMENT !== 'production'),
    'cache_on' => FALSE,
    'char_set' => 'utf8mb4',
    'dbcollat' => 'utf8mb4_unicode_ci',
];
```

### Class Definition

```php
<?php
namespace DGAPI\Libraries;

class XDatabase
{
    /**
     * @var \CI_DB_driver Database connection
     */
    protected $db;
    
    /**
     * @var array Query log
     */
    protected $queryLog = [];
    
    /**
     * @var bool Whether logging is enabled
     */
    protected $loggingEnabled = true;
    
    /**
     * @var int Transaction depth counter
     */
    protected $transactionDepth = 0;
}
```

### Basic Operations

```php
<?php
use DGAPI\Libraries\XDatabase;

$db = new XDatabase();

// Simple select
$task = $db->findOne('tasks', ['id' => 123]);

// Select with conditions
$tasks = $db->findAll('tasks', [
    'status' => 'pending',
    'created_at >=' => date('Y-m-d', strtotime('-1 day'))
]);

// Select with ordering and limit
$recentTasks = $db->findAll('tasks', [
    'status' => 'completed'
], [
    'orderBy' => 'completed_at DESC',
    'limit' => 10
]);

// Insert record
$id = $db->insert('tasks', [
    'type' => 'sms',
    'recipient' => '+1234567890',
    'message' => 'Hello World',
    'status' => 'pending',
    'created_at' => date('Y-m-d H:i:s')
]);

// Update record
$affected = $db->update('tasks', 
    ['status' => 'completed', 'completed_at' => date('Y-m-d H:i:s')],
    ['id' => 123]
);

// Delete record
$deleted = $db->delete('tasks', ['id' => 123]);
```

### Advanced Query Building

```php
<?php
class XDatabase
{
    /**
     * Execute complex select query
     * 
     * @param string $table Table name
     * @param array $conditions Where conditions
     * @param array $options Query options
     * @return array
     */
    public function findAll(string $table, array $conditions = [], array $options = []): array
    {
        $this->db->from($table);
        
        // Apply conditions
        foreach ($conditions as $key => $value) {
            if (is_array($value)) {
                $this->db->where_in($key, $value);
            } elseif ($value === null) {
                $this->db->where($key . ' IS NULL');
            } else {
                $this->db->where($key, $value);
            }
        }
        
        // Apply options
        if (isset($options['select'])) {
            $this->db->select($options['select']);
        }
        
        if (isset($options['orderBy'])) {
            $this->db->order_by($options['orderBy']);
        }
        
        if (isset($options['limit'])) {
            $offset = $options['offset'] ?? 0;
            $this->db->limit($options['limit'], $offset);
        }
        
        if (isset($options['groupBy'])) {
            $this->db->group_by($options['groupBy']);
        }
        
        if (isset($options['join'])) {
            foreach ($options['join'] as $join) {
                $this->db->join($join['table'], $join['condition'], $join['type'] ?? 'inner');
            }
        }
        
        $query = $this->db->get();
        $this->logQuery();
        
        return $query->result_array();
    }
    
    /**
     * Execute raw SQL query
     * 
     * @param string $sql SQL query
     * @param array $bindings Parameter bindings
     * @return array
     */
    public function query(string $sql, array $bindings = []): array
    {
        $query = $this->db->query($sql, $bindings);
        $this->logQuery();
        
        return $query->result_array();
    }
    
    /**
     * Get count of records
     * 
     * @param string $table Table name
     * @param array $conditions Where conditions
     * @return int
     */
    public function count(string $table, array $conditions = []): int
    {
        foreach ($conditions as $key => $value) {
            $this->db->where($key, $value);
        }
        
        return $this->db->count_all_results($table);
    }
}
```

### Transaction Management

```php
<?php
class XDatabase
{
    /**
     * Begin transaction (supports nesting)
     * 
     * @return bool
     */
    public function beginTransaction(): bool
    {
        if ($this->transactionDepth === 0) {
            $this->db->trans_begin();
        } else {
            $this->db->query("SAVEPOINT trans_{$this->transactionDepth}");
        }
        
        $this->transactionDepth++;
        return true;
    }
    
    /**
     * Commit transaction
     * 
     * @return bool
     */
    public function commit(): bool
    {
        if ($this->transactionDepth <= 0) {
            return false;
        }
        
        $this->transactionDepth--;
        
        if ($this->transactionDepth === 0) {
            $this->db->trans_commit();
        } else {
            $this->db->query("RELEASE SAVEPOINT trans_{$this->transactionDepth}");
        }
        
        return true;
    }
    
    /**
     * Rollback transaction
     * 
     * @return bool
     */
    public function rollback(): bool
    {
        if ($this->transactionDepth <= 0) {
            return false;
        }
        
        $this->transactionDepth--;
        
        if ($this->transactionDepth === 0) {
            $this->db->trans_rollback();
        } else {
            $this->db->query("ROLLBACK TO SAVEPOINT trans_{$this->transactionDepth}");
        }
        
        return true;
    }
    
    /**
     * Execute callback within transaction
     * 
     * @param callable $callback Function to execute
     * @return mixed
     * @throws DGAPIException
     */
    public function transaction(callable $callback)
    {
        $this->beginTransaction();
        
        try {
            $result = $callback($this);
            $this->commit();
            return $result;
        } catch (\Exception $e) {
            $this->rollback();
            throw new DGAPIException(
                'Transaction failed: ' . $e->getMessage(),
                Codes::ERR_DB_QUERY_FAILED,
                500,
                ['originalError' => $e->getMessage()]
            );
        }
    }
}
```

### Transaction Usage Example

```php
<?php
use DGAPI\Libraries\XDatabase;

$db = new XDatabase();

// Using transaction wrapper
$result = $db->transaction(function($db) use ($taskData) {
    // Insert task
    $taskId = $db->insert('tasks', [
        'type' => $taskData['type'],
        'status' => 'pending',
        'created_at' => date('Y-m-d H:i:s')
    ]);
    
    // Insert notifications
    foreach ($taskData['recipients'] as $recipient) {
        $db->insert('notifications', [
            'task_id' => $taskId,
            'recipient' => $recipient,
            'status' => 'pending'
        ]);
    }
    
    // Update campaign stats
    $db->query(
        "UPDATE campaigns SET task_count = task_count + 1 WHERE id = ?",
        [$taskData['campaign_id']]
    );
    
    return $taskId;
});

// Manual transaction management
$db->beginTransaction();
try {
    $db->insert('tasks', $task1);
    $db->insert('tasks', $task2);
    
    if ($someCondition) {
        throw new \Exception('Condition not met');
    }
    
    $db->commit();
} catch (\Exception $e) {
    $db->rollback();
    throw $e;
}
```

### Query Logging and Performance

```php
<?php
class XDatabase
{
    /**
     * Log executed query
     * 
     * @return void
     */
    protected function logQuery(): void
    {
        if (!$this->loggingEnabled) {
            return;
        }
        
        $query = $this->db->last_query();
        $time = $this->db->query_times[count($this->db->query_times) - 1] ?? 0;
        
        $this->queryLog[] = [
            'query' => $query,
            'time' => $time,
            'timestamp' => microtime(true)
        ];
        
        // Log slow queries
        if ($time > 1.0) { // > 1 second
            log_message('warning', sprintf(
                'Slow query (%.4fs): %s',
                $time,
                $query
            ));
        }
    }
    
    /**
     * Get query log
     * 
     * @return array
     */
    public function getQueryLog(): array
    {
        return $this->queryLog;
    }
    
    /**
     * Get query statistics
     * 
     * @return array
     */
    public function getStats(): array
    {
        $totalTime = array_sum(array_column($this->queryLog, 'time'));
        
        return [
            'queryCount' => count($this->queryLog),
            'totalTime' => $totalTime,
            'averageTime' => count($this->queryLog) > 0 
                ? $totalTime / count($this->queryLog) 
                : 0,
            'slowQueries' => count(array_filter(
                $this->queryLog,
                fn($q) => $q['time'] > 0.1
            ))
        ];
    }
}
```

---

## TasksD

The `TasksD` library (Task Disposition) provides the core business logic for managing disposition tasks including creation, processing, status updates, and workflow management. It serves as the primary interface for all task-related operations.

### Class Definition

```php
<?php
namespace DGAPI\Libraries;

class TasksD
{
    /**
     * @var XDatabase Database instance
     */
    protected $db;
    
    /**
     * @var array Supported task types
     */
    protected $supportedTypes = ['sms', 'email', 'voicemail', 'callback', 'cdr', 'generic'];
    
    /**
     * @var array Status transition rules
     */
    protected $statusTransitions = [
        'pending' => ['processing', 'cancelled'],
        'processing' => ['completed', 'failed', 'retry_pending'],
        'retry_pending' => ['processing', 'cancelled'],
        'completed' => [],
        'failed' => ['retry_pending'],
        'cancelled' => []
    ];
}
```

### Task Creation

```php
<?php
class TasksD
{
    /**
     * Create new task
     * 
     * @param array $data Task data
     * @return array Created task
     * @throws DGAPIException
     */
    public function createTask(array $data): array
    {
        // Validate task type
        if (!isset($data['type']) || !in_array($data['type'], $this->supportedTypes)) {
            throw DGAPIException::validationFailed([
                'type' => 'Invalid or missing task type'
            ]);
        }
        
        // Generate task ID
        $taskId = APIUtils::generateId('TSK');
        
        // Build task record
        $task = [
            'task_id' => $taskId,
            'type' => $data['type'],
            'status' => Codes::STATUS_PENDING,
            'priority' => $data['priority'] ?? 'normal',
            'payload' => json_encode($data['payload'] ?? []),
            'metadata' => json_encode($data['metadata'] ?? []),
            'scheduled_at' => $data['scheduled_at'] ?? null,
            'max_retries' => $data['max_retries'] ?? 3,
            'retry_count' => 0,
            'created_at' => APIUtils::formatForDb(),
            'updated_at' => APIUtils::formatForDb()
        ];
        
        // Insert into database
        $this->db->transaction(function($db) use ($task, $data) {
            $db->insert('tasks', $task);
            
            // Create associated records based on type
            if ($task['type'] === 'sms' && isset($data['recipients'])) {
                foreach ($data['recipients'] as $recipient) {
                    $db->insert('task_recipients', [
                        'task_id' => $task['task_id'],
                        'recipient' => $recipient['phone'],
                        'status' => 'pending',
                        'created_at' => APIUtils::formatForDb()
                    ]);
                }
            }
        });
        
        return $this->getTask($taskId);
    }
    
    /**
     * Create SMS task
     * 
     * @param string $recipient Phone number
     * @param string $message Message content
     * @param array $options Additional options
     * @return array
     */
    public function createSmsTask(string $recipient, string $message, array $options = []): array
    {
        // Validate phone number
        $normalizedPhone = APIUtils::normalizePhone($recipient);
        if (!$normalizedPhone) {
            throw new DGAPIException(
                'Invalid phone number format',
                Codes::ERR_SMS_INVALID_PHONE,
                400
            );
        }
        
        // Validate message length
        if (strlen($message) > 1600) {
            throw new DGAPIException(
                'Message exceeds maximum length',
                Codes::ERR_SMS_MESSAGE_TOO_LONG,
                400
            );
        }
        
        return $this->createTask([
            'type' => 'sms',
            'payload' => [
                'message' => $message,
                'encoding' => $options['encoding'] ?? 'auto'
            ],
            'recipients' => [
                ['phone' => $normalizedPhone]
            ],
            'priority' => $options['priority'] ?? 'normal',
            'scheduled_at' => $options['scheduled_at'] ?? null
        ]);
    }
}
```

### Task Retrieval

```php
<?php
class TasksD
{
    /**
     * Get task by ID
     * 
     * @param string $taskId Task identifier
     * @return array|null
     */
    public function getTask(string $taskId): ?array
    {
        $task = $this->db->findOne('tasks', ['task_id' => $taskId]);
        
        if (!$task) {
            return null;
        }
        
        // Decode JSON fields
        $task['payload'] = json_decode($task['payload'], true) ?? [];
        $task['metadata'] = json_decode($task['metadata'], true) ?? [];
        
        // Get recipients if applicable
        if (in_array($task['type'], ['sms', 'email'])) {
            $task['recipients'] = $this->db->findAll('task_recipients', [
                'task_id' => $taskId
            ]);
        }
        
        return $task;
    }
    
    /**
     * Get task or throw exception
     * 
     * @param string $taskId Task identifier
     * @return array
     * @throws DGAPIException
     */
    public function getTaskOrFail(string $taskId): array
    {
        $task = $this->getTask($taskId);
        
        if (!$task) {
            throw DGAPIException::notFound('Task', $taskId);
        }
        
        return $task;
    }
    
    /**
     * Search tasks with filters
     * 
     * @param array $filters Search filters
     * @param array $pagination Pagination options
     * @return array
     */
    public function searchTasks(array $filters = [], array $pagination = []): array
    {
        $conditions = [];
        
        // Build conditions from filters
        if (isset($filters['type'])) {
            $conditions['type'] = $filters['type'];
        }
        
        if (isset($filters['status'])) {
            $conditions['status'] = $filters['status'];
        }
        
        if (isset($filters['created_from'])) {
            $conditions['created_at >='] = $filters['created_from'];
        }
        
        if (isset($filters['created_to'])) {
            $conditions['created_at <='] = $filters['created_to'];
        }
        
        // Get total count
        $total = $this->db->count('tasks', $conditions);
        
        // Get paginated results
        $page = $pagination['page'] ?? 1;
        $perPage = min($pagination['per_page'] ?? 20, 100);
        $offset = ($page - 1) * $perPage;
        
        $tasks = $this->db->findAll('tasks', $conditions, [
            'orderBy' => 'created_at DESC',
            'limit' => $perPage,
            'offset' => $offset
        ]);
        
        // Decode JSON fields
        foreach ($tasks as &$task) {
            $task['payload'] = json_decode($task['payload'], true) ?? [];
            $task['metadata'] = json_decode($task['metadata'], true) ?? [];
        }
        
        return [
            'data' => $tasks,
            'pagination' => [
                'total' => $total,
                'page' => $page,
                'per_page' => $perPage,
                'total_pages' => ceil($total / $perPage)
            ]
        ];
    }
}
```

### Task Status Management

```php
<?php
class TasksD
{
    /**
     * Update task status
     * 
     * @param string $taskId Task identifier
     * @param string $newStatus New status
     * @param array $updateData Additional update data
     * @return array Updated task
     * @throws DGAPIException
     */
    public function updateStatus(string $taskId, string $newStatus, array $updateData = []): array
    {
        $task = $this->getTaskOrFail($taskId);
        
        // Validate status transition
        $allowedTransitions = $this->statusTransitions[$task['status']] ?? [];
        if (!in_array($newStatus, $allowedTransitions)) {
            throw new DGAPIException(
                sprintf(
                    'Invalid status transition from %s to %s',
                    $task['status'],
                    $newStatus
                ),
                Codes::ERR_INVALID_TASK_TYPE,
                400
            );
        }
        
        // Build update data
        $update = array_merge($updateData, [
            'status' => $newStatus,
            'updated_at' => APIUtils::formatForDb()
        ]);
        
        // Add timestamps based on status
        switch ($newStatus) {
            case Codes::STATUS_PROCESSING:
                $update['started_at'] = APIUtils::formatForDb();
                break;
            case Codes::STATUS_COMPLETED:
                $update['completed_at'] = APIUtils::formatForDb();
                break;
            case Codes::STATUS_FAILED:
                $update['failed_at'] = APIUtils::formatForDb();
                break;
        }
        
        // Update database
        $this->db->update('tasks', $update, ['task_id' => $taskId]);
        
        // Log status change
        $this->logStatusChange($taskId, $task['status'], $newStatus);
        
        return $this->getTask($taskId);
    }
    
    /**
     * Mark task as completed
     * 
     * @param string $taskId Task identifier
     * @param array $result Result data
     * @return array
     */
    public function completeTask(string $taskId, array $result = []): array
    {
        return $this->updateStatus($taskId, Codes::STATUS_COMPLETED, [
            'result' => json_encode($result)
        ]);
    }
    
    /**
     * Mark task as failed
     * 
     * @param string $taskId Task identifier
     * @param string $reason Failure reason
     * @param bool $retry Whether to retry
     * @return array
     */
    public function failTask(string $taskId, string $reason, bool $retry = true): array
    {
        $task = $this->getTaskOrFail($taskId);
        
        $newStatus = Codes::STATUS_FAILED;
        
        // Check if should retry
        if ($retry && $task['retry_count'] < $task['max_retries']) {
            $newStatus = Codes::STATUS_RETRY_PENDING;
        }
        
        return $this->updateStatus($taskId, $newStatus, [
            'error_message' => $reason,
            'retry_count' => $task['retry_count'] + 1
        ]);
    }
    
    /**
     * Cancel task
     * 
     * @param string $taskId Task identifier
     * @param string $reason Cancellation reason
     * @return array
     */
    public function cancelTask(string $taskId, string $reason = ''): array
    {
        return $this->updateStatus($taskId, Codes::STATUS_CANCELLED, [
            'cancellation_reason' => $reason
        ]);
    }
}
```

### Task Processing

```php
<?php
class TasksD
{
    /**
     * Get next pending task for processing
     * 
     * @param string|null $type Optional type filter
     * @return array|null
     */
    public function getNextPendingTask(?string $type = null): ?array
    {
        $conditions = [
            'status' => Codes::STATUS_PENDING
        ];
        
        if ($type) {
            $conditions['type'] = $type;
        }
        
        // Include scheduled tasks that are due
        $tasks = $this->db->query(
            "SELECT * FROM tasks 
             WHERE status = ? 
             AND (scheduled_at IS NULL OR scheduled_at <= NOW())
             " . ($type ? "AND type = ?" : "") . "
             ORDER BY priority DESC, created_at ASC
             LIMIT 1
             FOR UPDATE SKIP LOCKED",
            $type ? [Codes::STATUS_PENDING, $type] : [Codes::STATUS_PENDING]
        );
        
        if (empty($tasks)) {
            return null;
        }
        
        $task = $tasks[0];
        $task['payload'] = json_decode($task['payload'], true) ?? [];
        $task['metadata'] = json_decode($task['metadata'], true) ?? [];
        
        return $task;
    }
    
    /**
     * Process a task
     * 
     * @param string $taskId Task identifier
     * @param callable $processor Processing function
     * @return array Processing result
     */
    public function processTask(string $taskId, callable $processor): array
    {
        // Mark as processing
        $task = $this->updateStatus($taskId, Codes::STATUS_PROCESSING);
        
        try {
            // Execute processor
            $result = $processor($task);
            
            // Mark as completed
            return $this->completeTask($taskId, $result);
            
        } catch (\Exception $e) {
            // Mark as failed
            return $this->failTask($taskId, $e->getMessage());
        }
    }
    
    /**
     * Retry pending tasks
     * 
     * @return int Number of tasks queued for retry
     */
    public function retryPendingTasks(): int
    {
        $tasks = $this->db->findAll('tasks', [
            'status' => Codes::STATUS_RETRY_PENDING
        ], [
            'limit' => 100
        ]);
        
        $retried = 0;
        
        foreach ($tasks as $task) {
            // Check retry delay (exponential backoff)
            $delay = pow(2, $task['retry_count']) * 60; // 2^n minutes
            $failedAt = strtotime($task['failed_at']);
            
            if (time() >= $failedAt + $delay) {
                $this->updateStatus($task['task_id'], Codes::STATUS_PENDING);
                $retried++;
            }
        }
        
        return $retried;
    }
}
```

### Usage Example

```php
<?php
use DGAPI\Libraries\TasksD;
use DGAPI\Libraries\DOMRequest;
use DGAPI\Libraries\DOMResponse;

class SmsController extends CI_Controller
{
    protected $tasksD;
    
    public function __construct()
    {
        parent::__construct();
        $this->tasksD = new TasksD();
    }
    
    public function send()
    {
        try {
            $request = DOMRequest::fromInput();
            
            // Create SMS task
            $task = $this->tasksD->createSmsTask(
                $request->getValue('//Phone'),
                $request->getValue('//Message'),
                [
                    'priority' => $request->getValue('//Priority', 'normal'),
                    'scheduled_at' => $request->getValue('//ScheduledAt')
                ]
            );
            
            // Return success response
            DOMResponse::taskResult(
                $task['task_id'],
                $task['status'],
                ['message' => 'SMS task created successfully']
            )->send();
            
        } catch (DGAPIException $e) {
            $e->toResponse()->send();
        }
    }
    
    public function status($taskId)
    {
        try {
            $task = $this->tasksD->getTaskOrFail($taskId);
            
            $response = new DOMResponse('TaskStatus');
            $response->addData('Task', [
                'Id' => $task['task_id'],
                'Type' => $task['type'],
                'Status' => $task['status'],
                'CreatedAt' => $task['created_at'],
                'UpdatedAt' => $task['updated_at']
            ]);
            
            if (!empty($task['recipients'])) {
                $response->addDataArray('Recipients', 'Recipient', 
                    array_map(function($r) {
                        return [
                            'Address' => $r['recipient'],
                            'Status' => $r['status']
                        ];
                    }, $task['recipients'])
                );
            }
            
            $response->send();
            
        } catch (DGAPIException $e) {
            $e->toResponse()->send();
        }
    }
}
```

---

## Best Practices

### Error Handling

1. **Always use DGAPIException** for application errors to ensure consistent error responses
2. **Include context** in exceptions to aid debugging
3. **Log all errors** with appropriate severity levels
4. **Never expose internal errors** to API consumers

```php
<?php
// Good: Contextual exception
throw new DGAPIException(
    'Failed to process task',
    Codes::ERR_TASK_NOT_FOUND,
    404,
    ['taskId' => $taskId, 'attemptedAction' => 'process']
);

// Bad: Generic exception without context
throw new \Exception('Error');
```

### Database Operations

1. **Use transactions** for multi-table operations
2. **Enable query logging** in non-production environments
3. **Use prepared statements** to prevent SQL injection
4. **Monitor slow queries** and optimize as needed

```php
<?php
// Good: Transaction for related operations
$db->transaction(function($db) use ($data) {
    $db->insert('tasks', $taskData);
    $db->insert('task_history', $historyData);
});

// Bad: Separate operations without transaction
$db->insert('tasks', $taskData);
$db->insert('task_history', $historyData); // May fail leaving inconsistent data
```

### DOM Handling

1. **Validate XML structure** before processing
2. **Use CDATA** for content with special characters
3. **Sanitize output** to prevent XML injection
4. **Handle encoding** properly (UTF-8)

```php
<?php
// Good: Sanitize user content
$element = $maker->createElement('Message');
$maker->addCDATA($element, APIUtils::sanitizeForXml($userMessage));

// Bad: Direct inclusion of user content
$element = $maker->createElement('Message', $userMessage); // XSS risk
```

---

## Summary

The core libraries documented in this reference provide the foundation for all platform-dgapi operations:

| Library | Purpose | Key Features |
|---------|---------|--------------|
| **DOMMaker** | XML document creation | Element creation, CDATA support, formatted output |
| **DOMRequest** | XML request parsing | XPath queries, validation, array conversion |
| **DOMResponse** | XML response building | Fluent interface, templates, auto-headers |
| **DGAPIException** | Error handling | Context support, HTTP mapping, response generation |
| **Codes** | Constants and messages | Error codes, status codes, message templates |
| **APIUtils** | Utility functions | String, date, phone, and array utilities |
| **XDatabase** | Database abstraction | Query building, transactions, logging |
| **TasksD** | Task management | CRUD operations, status workflow, processing |

These libraries are designed to work together seamlessly, providing a robust foundation for building and extending disposition gateway functionality.