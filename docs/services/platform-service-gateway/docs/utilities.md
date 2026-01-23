# Utilities Reference

## Overview

The Platform Service Gateway includes a comprehensive set of utility classes and helper functions designed to streamline common operations across the multi-platform CRM integration layer. These utilities handle everything from parsing Salesforce object structures to string manipulation and data transformation tasks that are essential for maintaining consistency across different CRM backends.

This reference guide provides detailed documentation for developers integrating with CRM systems and operators deploying the gateway, covering the core utility classes, their methods, and practical usage patterns.

---

## Table of Contents

1. [SFObjectParser](#sfobjectparser)
2. [StringifyWrapper](#stringifywrapper)
3. [Common Utility Functions](#common-utility-functions)
4. [Best Practices](#best-practices)
5. [Troubleshooting](#troubleshooting)

---

## SFObjectParser

The `SFObjectParser` utility class provides robust parsing and transformation capabilities for Salesforce object structures. This class is essential for normalizing Salesforce API responses into the unified data format used by the Platform Service Gateway.

### Class Definition

```php
<?php
/**
 * SFObjectParser - Salesforce Object Parsing Utility
 * 
 * Handles parsing, normalization, and transformation of Salesforce
 * object structures for unified gateway consumption.
 * 
 * @package    PlatformServiceGateway
 * @subpackage Utilities
 * @since      1.0.0
 */
class SFObjectParser
{
    /**
     * @var array Supported Salesforce object types
     */
    protected $supportedTypes = [
        'Account', 'Contact', 'Lead', 'Opportunity',
        'Case', 'Task', 'Event', 'Campaign'
    ];
    
    /**
     * @var array Field mapping configuration
     */
    protected $fieldMappings = [];
    
    /**
     * @var bool Enable strict parsing mode
     */
    protected $strictMode = false;
}
```

### Core Methods

#### `parse($rawObject, $objectType = null)`

Parses a raw Salesforce object response into a normalized structure.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `$rawObject` | array\|object | Yes | Raw Salesforce API response object |
| `$objectType` | string | No | Explicit object type override |

**Returns:** `array` - Normalized object structure

**Example:**

```php
<?php
// Initialize the parser
$parser = new SFObjectParser();

// Raw Salesforce response
$sfResponse = [
    'attributes' => [
        'type' => 'Contact',
        'url' => '/services/data/v52.0/sobjects/Contact/003xx000004TxyZAAZ'
    ],
    'Id' => '003xx000004TxyZAAZ',
    'FirstName' => 'John',
    'LastName' => 'Doe',
    'Email' => 'john.doe@example.com',
    'Account' => [
        'attributes' => [
            'type' => 'Account',
            'url' => '/services/data/v52.0/sobjects/Account/001xx000003DGbZAAW'
        ],
        'Id' => '001xx000003DGbZAAW',
        'Name' => 'Acme Corporation'
    ]
];

// Parse the object
$normalized = $parser->parse($sfResponse);

// Result structure
/*
[
    'id' => '003xx000004TxyZAAZ',
    'type' => 'Contact',
    'source' => 'salesforce',
    'attributes' => [
        'first_name' => 'John',
        'last_name' => 'Doe',
        'email' => 'john.doe@example.com'
    ],
    'relationships' => [
        'account' => [
            'id' => '001xx000003DGbZAAW',
            'type' => 'Account',
            'name' => 'Acme Corporation'
        ]
    ],
    'meta' => [
        'api_url' => '/services/data/v52.0/sobjects/Contact/003xx000004TxyZAAZ',
        'parsed_at' => '2024-01-15T10:30:00Z'
    ]
]
*/
```

#### `parseCollection($records, $options = [])`

Parses a collection of Salesforce records from a query response.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `$records` | array | Yes | Array of Salesforce records |
| `$options` | array | No | Parsing options |

**Options Array:**

```php
$options = [
    'preserve_nulls' => false,      // Keep null values in output
    'flatten_relationships' => true, // Flatten nested relationships
    'include_meta' => true,          // Include metadata in output
    'date_format' => 'Y-m-d H:i:s', // Output date format
    'max_depth' => 3                 // Maximum relationship nesting depth
];
```

**Example:**

```php
<?php
// Salesforce SOQL query response
$queryResponse = [
    'totalSize' => 2,
    'done' => true,
    'records' => [
        [
            'attributes' => ['type' => 'Lead', 'url' => '...'],
            'Id' => '00Qxx000001ABCD',
            'FirstName' => 'Jane',
            'LastName' => 'Smith',
            'Company' => 'Tech Corp',
            'Status' => 'Open - Not Contacted'
        ],
        [
            'attributes' => ['type' => 'Lead', 'url' => '...'],
            'Id' => '00Qxx000001EFGH',
            'FirstName' => 'Bob',
            'LastName' => 'Wilson',
            'Company' => 'Data Inc',
            'Status' => 'Working - Contacted'
        ]
    ]
];

$parser = new SFObjectParser();
$normalizedCollection = $parser->parseCollection(
    $queryResponse['records'],
    [
        'preserve_nulls' => false,
        'include_meta' => true
    ]
);

// Returns array of normalized objects
foreach ($normalizedCollection as $record) {
    echo "Lead: {$record['attributes']['first_name']} {$record['attributes']['last_name']}\n";
}
```

#### `extractFields($object, $fieldList)`

Extracts specific fields from a parsed Salesforce object.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `$object` | array | Yes | Parsed Salesforce object |
| `$fieldList` | array | Yes | List of field names to extract |

**Example:**

```php
<?php
$parser = new SFObjectParser();

$fullObject = $parser->parse($sfResponse);

// Extract only specific fields
$subset = $parser->extractFields($fullObject, [
    'id',
    'attributes.email',
    'attributes.first_name',
    'relationships.account.name'
]);

// Result:
/*
[
    'id' => '003xx000004TxyZAAZ',
    'email' => 'john.doe@example.com',
    'first_name' => 'John',
    'account_name' => 'Acme Corporation'
]
*/
```

#### `setFieldMapping($mappings)`

Configures custom field mappings for Salesforce to gateway field translation.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `$mappings` | array | Yes | Field mapping configuration |

**Example:**

```php
<?php
$parser = new SFObjectParser();

// Configure custom field mappings
$parser->setFieldMapping([
    'Contact' => [
        'FirstName' => 'first_name',
        'LastName' => 'last_name',
        'Email' => 'email_address',
        'Phone' => 'phone_number',
        'MailingStreet' => 'address.street',
        'MailingCity' => 'address.city',
        'MailingState' => 'address.state',
        'MailingPostalCode' => 'address.postal_code',
        'MailingCountry' => 'address.country'
    ],
    'Account' => [
        'Name' => 'company_name',
        'Industry' => 'industry_sector',
        'AnnualRevenue' => 'annual_revenue',
        'NumberOfEmployees' => 'employee_count'
    ]
]);

// Now parsing will use custom field names
$parsed = $parser->parse($sfContact);
// $parsed['attributes']['email_address'] instead of $parsed['attributes']['email']
```

#### `validateObject($object, $schema)`

Validates a Salesforce object against a defined schema.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `$object` | array | Yes | Object to validate |
| `$schema` | array | Yes | Validation schema |

**Example:**

```php
<?php
$parser = new SFObjectParser();

$schema = [
    'required' => ['Id', 'Email'],
    'types' => [
        'Id' => 'string',
        'Email' => 'email',
        'CreatedDate' => 'datetime',
        'IsActive' => 'boolean'
    ],
    'constraints' => [
        'Email' => ['max_length' => 255],
        'Id' => ['pattern' => '/^[a-zA-Z0-9]{15,18}$/']
    ]
];

$validation = $parser->validateObject($sfObject, $schema);

if (!$validation['valid']) {
    foreach ($validation['errors'] as $error) {
        echo "Validation error: {$error['field']} - {$error['message']}\n";
    }
}
```

### Static Helper Methods

```php
<?php
// Check if string is a valid Salesforce ID
$isValid = SFObjectParser::isValidSalesforceId('003xx000004TxyZAAZ'); // true
$isValid = SFObjectParser::isValidSalesforceId('invalid'); // false

// Convert 15-char ID to 18-char ID
$id18 = SFObjectParser::convertTo18CharId('003xx000004TxyZ'); // '003xx000004TxyZAAZ'

// Get object type from ID prefix
$type = SFObjectParser::getObjectTypeFromId('003xx000004TxyZAAZ'); // 'Contact'

// Parse Salesforce datetime to PHP DateTime
$datetime = SFObjectParser::parseSalesforceDateTime('2024-01-15T10:30:00.000+0000');
```

---

## StringifyWrapper

The `StringifyWrapper` utility provides consistent serialization and deserialization capabilities across different data formats. It handles JSON, XML, and custom serialization formats used by various CRM platforms.

### Class Definition

```php
<?php
/**
 * StringifyWrapper - Universal Serialization Utility
 * 
 * Provides consistent data serialization across multiple formats
 * with support for CRM-specific encoding requirements.
 * 
 * @package    PlatformServiceGateway
 * @subpackage Utilities
 */
class StringifyWrapper
{
    const FORMAT_JSON = 'json';
    const FORMAT_XML = 'xml';
    const FORMAT_QUERY_STRING = 'query';
    const FORMAT_CSV = 'csv';
    
    /**
     * @var array Default encoding options
     */
    protected $defaultOptions = [
        'json' => [
            'flags' => JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES,
            'depth' => 512
        ],
        'xml' => [
            'root_element' => 'data',
            'encoding' => 'UTF-8',
            'version' => '1.0'
        ]
    ];
}
```

### Core Methods

#### `encode($data, $format = 'json', $options = [])`

Encodes data into the specified format.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `$data` | mixed | Yes | Data to encode |
| `$format` | string | No | Output format (json, xml, query, csv) |
| `$options` | array | No | Format-specific options |

**Example:**

```php
<?php
$wrapper = new StringifyWrapper();

$data = [
    'contact' => [
        'id' => '12345',
        'name' => 'John Doe',
        'email' => 'john@example.com',
        'tags' => ['customer', 'premium', 'active']
    ]
];

// JSON encoding
$json = $wrapper->encode($data, 'json');
// {"contact":{"id":"12345","name":"John Doe","email":"john@example.com","tags":["customer","premium","active"]}}

// Pretty-printed JSON
$jsonPretty = $wrapper->encode($data, 'json', ['pretty' => true]);

// XML encoding
$xml = $wrapper->encode($data, 'xml', [
    'root_element' => 'response',
    'item_element' => 'item'
]);
/*
<?xml version="1.0" encoding="UTF-8"?>
<response>
    <contact>
        <id>12345</id>
        <name>John Doe</name>
        <email>john@example.com</email>
        <tags>
            <item>customer</item>
            <item>premium</item>
            <item>active</item>
        </tags>
    </contact>
</response>
*/

// Query string encoding
$query = $wrapper->encode($data['contact'], 'query');
// id=12345&name=John+Doe&email=john%40example.com&tags%5B0%5D=customer&tags%5B1%5D=premium&tags%5B2%5D=active
```

#### `decode($string, $format = 'json', $options = [])`

Decodes a string from the specified format.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `$string` | string | Yes | String to decode |
| `$format` | string | No | Input format |
| `$options` | array | No | Format-specific options |

**Example:**

```php
<?php
$wrapper = new StringifyWrapper();

// JSON decoding
$jsonString = '{"name":"Jane","active":true,"score":95.5}';
$data = $wrapper->decode($jsonString, 'json');
// ['name' => 'Jane', 'active' => true, 'score' => 95.5]

// Decode as object instead of array
$object = $wrapper->decode($jsonString, 'json', ['assoc' => false]);
// stdClass object

// XML decoding
$xmlString = '<?xml version="1.0"?><contact><name>Jane</name><email>jane@example.com</email></contact>';
$data = $wrapper->decode($xmlString, 'xml');
// ['name' => 'Jane', 'email' => 'jane@example.com']

// Handle CDATA sections
$xmlWithCdata = '<note><content><![CDATA[Special <characters> & symbols]]></content></note>';
$data = $wrapper->decode($xmlWithCdata, 'xml', ['cdata_as_text' => true]);
```

#### `transform($data, $fromFormat, $toFormat, $options = [])`

Transforms data between formats in a single operation.

**Example:**

```php
<?php
$wrapper = new StringifyWrapper();

// Convert JSON to XML
$jsonInput = '{"user":{"id":1,"name":"Alice","roles":["admin","editor"]}}';
$xmlOutput = $wrapper->transform($jsonInput, 'json', 'xml', [
    'root_element' => 'response'
]);

// Convert XML to JSON
$xmlInput = '<contacts><contact><name>Bob</name></contact></contacts>';
$jsonOutput = $wrapper->transform($xmlInput, 'xml', 'json', [
    'pretty' => true
]);
```

#### `stringify($value, $options = [])`

Converts any value to a string representation with intelligent type handling.

**Example:**

```php
<?php
$wrapper = new StringifyWrapper();

// Boolean handling
echo $wrapper->stringify(true);  // 'true'
echo $wrapper->stringify(false); // 'false'

// Null handling
echo $wrapper->stringify(null);  // 'null' or '' depending on options

// Array handling
echo $wrapper->stringify(['a', 'b', 'c']); // 'a,b,c'

// Object handling
$obj = new stdClass();
$obj->name = 'Test';
echo $wrapper->stringify($obj); // '{"name":"Test"}'

// DateTime handling
$date = new DateTime('2024-01-15 10:30:00');
echo $wrapper->stringify($date, ['date_format' => 'Y-m-d']); // '2024-01-15'

// Custom stringify options
echo $wrapper->stringify(['key' => 'value'], [
    'array_separator' => '|',
    'key_value_separator' => ':',
    'include_keys' => true
]); // 'key:value'
```

#### `sanitize($string, $type = 'general')`

Sanitizes a string for safe use in different contexts.

**Example:**

```php
<?php
$wrapper = new StringifyWrapper();

// General sanitization
$clean = $wrapper->sanitize('<script>alert("xss")</script>Hello', 'general');
// 'Hello'

// HTML context
$htmlSafe = $wrapper->sanitize('5 > 3 && 2 < 4', 'html');
// '5 &gt; 3 &amp;&amp; 2 &lt; 4'

// SQL identifier context
$sqlSafe = $wrapper->sanitize('user; DROP TABLE users;--', 'sql_identifier');
// 'user_DROP_TABLE_users'

// URL context
$urlSafe = $wrapper->sanitize('hello world & more', 'url');
// 'hello%20world%20%26%20more'

// Filename context
$fileSafe = $wrapper->sanitize('../../../etc/passwd', 'filename');
// 'etc_passwd'
```

### CRM-Specific Methods

```php
<?php
$wrapper = new StringifyWrapper();

// Salesforce SOQL-safe string
$soqlValue = $wrapper->forSalesforce("O'Brien & Associates");
// "O\'Brien & Associates"

// Microsoft Dynamics OData filter value
$odataValue = $wrapper->forDynamics("Search 'term'");
// "Search ''term''"

// Zendesk API query parameter
$zendeskValue = $wrapper->forZendesk("tag:support status:open");
// Properly encoded for Zendesk search API
```

---

## Common Utility Functions

The Platform Service Gateway includes a set of standalone utility functions available globally throughout the application.

### Array Utilities

#### `array_get($array, $key, $default = null)`

Retrieves a value from a nested array using dot notation.

```php
<?php
$config = [
    'database' => [
        'connections' => [
            'mysql' => [
                'host' => 'localhost',
                'port' => 3306
            ]
        ]
    ]
];

$host = array_get($config, 'database.connections.mysql.host');
// 'localhost'

$missing = array_get($config, 'database.connections.postgres.host', 'default-host');
// 'default-host'
```

#### `array_set(&$array, $key, $value)`

Sets a value in a nested array using dot notation.

```php
<?php
$config = [];

array_set($config, 'app.name', 'Platform Gateway');
array_set($config, 'app.version', '2.0.0');
array_set($config, 'features.oauth.enabled', true);

/*
$config = [
    'app' => [
        'name' => 'Platform Gateway',
        'version' => '2.0.0'
    ],
    'features' => [
        'oauth' => [
            'enabled' => true
        ]
    ]
]
*/
```

#### `array_flatten($array, $prefix = '')`

Flattens a multi-dimensional array with dot notation keys.

```php
<?php
$nested = [
    'contact' => [
        'name' => [
            'first' => 'John',
            'last' => 'Doe'
        ],
        'email' => 'john@example.com'
    ]
];

$flat = array_flatten($nested);
/*
[
    'contact.name.first' => 'John',
    'contact.name.last' => 'Doe',
    'contact.email' => 'john@example.com'
]
*/
```

#### `array_only($array, $keys)`

Returns only the specified keys from an array.

```php
<?php
$user = [
    'id' => 1,
    'name' => 'John',
    'email' => 'john@example.com',
    'password' => 'hashed_secret',
    'api_token' => 'token123'
];

$safe = array_only($user, ['id', 'name', 'email']);
// ['id' => 1, 'name' => 'John', 'email' => 'john@example.com']
```

#### `array_except($array, $keys)`

Returns all keys except the specified ones.

```php
<?php
$user = [
    'id' => 1,
    'name' => 'John',
    'email' => 'john@example.com',
    'password' => 'hashed_secret'
];

$safe = array_except($user, ['password']);
// ['id' => 1, 'name' => 'John', 'email' => 'john@example.com']
```

### String Utilities

#### `str_contains($haystack, $needle)`

Checks if a string contains a substring (polyfill for PHP < 8.0).

```php
<?php
if (str_contains($email, '@example.com')) {
    echo 'Internal email detected';
}
```

#### `str_starts_with($haystack, $needle)`

Checks if a string starts with a substring.

```php
<?php
$id = '003xx000004TxyZAAZ';

if (str_starts_with($id, '003')) {
    echo 'This is a Contact ID';
} elseif (str_starts_with($id, '001')) {
    echo 'This is an Account ID';
}
```

#### `str_ends_with($haystack, $needle)`

Checks if a string ends with a substring.

```php
<?php
$filename = 'export_2024-01-15.csv';

if (str_ends_with($filename, '.csv')) {
    $handler = new CsvHandler();
} elseif (str_ends_with($filename, '.json')) {
    $handler = new JsonHandler();
}
```

#### `str_slug($string, $separator = '-')`

Generates a URL-friendly slug from a string.

```php
<?php
$title = "Platform Service Gateway: User's Guide!";
$slug = str_slug($title);
// 'platform-service-gateway-users-guide'

$slug = str_slug($title, '_');
// 'platform_service_gateway_users_guide'
```

#### `str_limit($string, $limit = 100, $end = '...')`

Truncates a string to a specified length.

```php
<?php
$description = 'This is a very long description that needs to be truncated for display purposes.';

$short = str_limit($description, 30);
// 'This is a very long descrip...'

$short = str_limit($description, 30, ' [more]');
// 'This is a very long descrip [more]'
```

### Date/Time Utilities

#### `parse_datetime($value, $format = null)`

Parses various datetime formats into a PHP DateTime object.

```php
<?php
// ISO 8601 format
$dt = parse_datetime('2024-01-15T10:30:00Z');

// Salesforce datetime format
$dt = parse_datetime('2024-01-15T10:30:00.000+0000');

// Microsoft Dynamics format
$dt = parse_datetime('/Date(1705312200000)/');

// Unix timestamp
$dt = parse_datetime(1705312200);

// Custom format
$dt = parse_datetime('15/01/2024 10:30', 'd/m/Y H:i');
```

#### `format_datetime($datetime, $format = 'Y-m-d H:i:s', $timezone = null)`

Formats a datetime value consistently.

```php
<?php
$dt = new DateTime('2024-01-15 10:30:00', new DateTimeZone('UTC'));

// Standard format
echo format_datetime($dt);
// '2024-01-15 10:30:00'

// ISO 8601
echo format_datetime($dt, 'c');
// '2024-01-15T10:30:00+00:00'

// With timezone conversion
echo format_datetime($dt, 'Y-m-d H:i:s', 'America/New_York');
// '2024-01-15 05:30:00'

// Salesforce format
echo format_datetime($dt, 'Y-m-d\TH:i:s.000O');
// '2024-01-15T10:30:00.000+0000'
```

### HTTP Utilities

#### `http_build_url($parts)`

Builds a URL from component parts.

```php
<?php
$url = http_build_url([
    'scheme' => 'https',
    'host' => 'api.salesforce.com',
    'path' => '/services/data/v52.0/sobjects/Contact',
    'query' => ['q' => 'SELECT Id FROM Contact']
]);
// 'https://api.salesforce.com/services/data/v52.0/sobjects/Contact?q=SELECT+Id+FROM+Contact'
```

#### `parse_response_headers($headerString)`

Parses HTTP response headers into an associative array.

```php
<?php
$rawHeaders = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nX-Request-Id: abc123\r\n";

$headers = parse_response_headers($rawHeaders);
/*
[
    'status_code' => 200,
    'status_text' => 'OK',
    'Content-Type' => 'application/json',
    'X-Request-Id' => 'abc123'
]
*/
```

### Validation Utilities

#### `is_valid_email($email)`

Validates an email address.

```php
<?php
is_valid_email('user@example.com');     // true
is_valid_email('invalid-email');         // false
is_valid_email('user@subdomain.example.com'); // true
```

#### `is_valid_url($url, $protocols = ['http', 'https'])`

Validates a URL.

```php
<?php
is_valid_url('https://example.com/path'); // true
is_valid_url('ftp://files.example.com');  // false (ftp not in default protocols)
is_valid_url('ftp://files.example.com', ['http', 'https', 'ftp']); // true
```

#### `is_valid_json($string)`

Checks if a string is valid JSON.

```php
<?php
is_valid_json('{"name":"John"}');  // true
is_valid_json('{invalid json}');   // false
is_valid_json('null');             // true
is_valid_json('');                 // false
```

### Encryption Utilities

#### `encrypt_value($value, $key = null)`

Encrypts a value using the application encryption key.

```php
<?php
$apiToken = 'sf_token_12345';
$encrypted = encrypt_value($apiToken);
// 'eyJpdiI6Ik...' (base64 encoded encrypted string)

// Store encrypted value in database
$db->insert('credentials', [
    'service' => 'salesforce',
    'token' => $encrypted
]);
```

#### `decrypt_value($encrypted, $key = null)`

Decrypts an encrypted value.

```php
<?php
$stored = $db->get('credentials', ['service' => 'salesforce']);
$apiToken = decrypt_value($stored['token']);
// 'sf_token_12345'
```

---

## Best Practices

### 1. Parser Configuration

Always configure the `SFObjectParser` with appropriate field mappings before processing large datasets:

```php
<?php
// Configure once at application bootstrap
$parser = new SFObjectParser();
$parser->setFieldMapping($mappingConfig);
$parser->setStrictMode(true);

// Register as singleton for reuse
$container->singleton('sf_parser', $parser);
```

### 2. Error Handling with StringifyWrapper

Always wrap encode/decode operations in try-catch blocks:

```php
<?php
$wrapper = new StringifyWrapper();

try {
    $data = $wrapper->decode($responseBody, 'json');
} catch (InvalidFormatException $e) {
    log_error('Failed to parse JSON response', [
        'error' => $e->getMessage(),
        'body' => substr($responseBody, 0, 500)
    ]);
    throw new ApiException('Invalid response format from CRM');
}
```

### 3. Memory Efficiency for Large Collections

When parsing large collections, use generators or chunk processing:

```php
<?php
// For large result sets
$parser = new SFObjectParser();

function parseInChunks($records, $chunkSize = 100) {
    global $parser;
    
    foreach (array_chunk($records, $chunkSize) as $chunk) {
        foreach ($parser->parseCollection($chunk) as $record) {
            yield $record;
        }
        
        // Allow garbage collection
        gc_collect_cycles();
    }
}

// Process without loading all into memory
foreach (parseInChunks($largeRecordSet) as $record) {
    processRecord($record);
}
```

### 4. Consistent Date Handling

Always use the date utilities for cross-platform consistency:

```php
<?php
// Convert incoming date from any CRM format
$internalDate = parse_datetime($crmDateValue);

// Format for specific CRM when sending
$salesforceDate = format_datetime($internalDate, 'Y-m-d\TH:i:s.000O');
$dynamicsDate = format_datetime($internalDate, 'Y-m-d\TH:i:s\Z');
```

---

## Troubleshooting

### Common Issues

#### SFObjectParser: "Unknown object type" Error

**Problem:** Parser fails with unknown object type error.

**Solution:** Ensure the Salesforce response includes the `attributes.type` field, or pass the type explicitly:

```php
<?php
// Option 1: Ensure attributes are present in API call
$sfClient->query("SELECT Id, Name, attributes FROM Account");

// Option 2: Pass type explicitly
$parsed = $parser->parse($object, 'Account');
```

#### StringifyWrapper: XML Encoding Issues with Special Characters

**Problem:** Special characters cause XML encoding failures.

**Solution:** Enable CDATA wrapping for problematic fields:

```php
<?php
$xml = $wrapper->encode($data, 'xml', [
    'cdata_fields' => ['description', 'notes', 'content']
]);
```

#### Array Utilities: Deep Nesting Performance

**Problem:** `array_get` is slow on deeply nested arrays.

**Solution:** Cache frequently accessed paths or use direct array access for known structures:

```php
<?php
// Instead of repeated calls
$value = array_get($config, 'very.deep.nested.value');

// Cache the intermediate reference
$nested = $config['very']['deep'] ?? [];
$value = $nested['nested']['value'] ?? $default;
```

### Debug Mode

Enable debug mode for detailed utility logging:

```php
<?php
// In config/utilities.php
return [
    'debug' => env('UTILITY_DEBUG', false),
    'log_level' => 'debug',
    'performance_tracking' => true
];
```

This will log detailed information about parsing operations, serialization timing, and memory usage to help identify performance bottlenecks.

---

## Related Documentation

- [API Reference Guide](./api-reference.md)
- [Data Models Reference](./data-models.md)
- [Configuration Guide](./configuration.md)
- [Authentication Setup](./authentication.md)