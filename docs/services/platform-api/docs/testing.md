# Testing Guide

## Overview

This comprehensive testing guide provides developers and operators with the knowledge and tools necessary to effectively test the platform-api service. As the core hub for telecommunications and VoIP platform management, the platform-api handles critical operations including user management, billing, dialplan configuration, and SIP/VoIP resource management. Rigorous testing is essential to ensure reliability, security, and performance across all 150 API endpoints and 100 data models.

This guide covers the complete testing lifecycle using Codeception, from initial setup through CI/CD integration, enabling you to maintain high code quality and catch issues before they reach production.

## Test Setup

### Prerequisites

Before setting up the testing environment, ensure you have the following installed:

- PHP 8.1 or higher
- Composer (dependency manager)
- MySQL 8.0+ or PostgreSQL 13+ (for integration tests)
- Redis (for caching tests)
- Docker and Docker Compose (recommended for isolated test environments)

### Installing Codeception

The platform-api uses Codeception as its primary testing framework. Install it via Composer:

```bash
# Install Codeception and required modules
composer require --dev codeception/codeception
composer require --dev codeception/module-phpbrowser
composer require --dev codeception/module-rest
composer require --dev codeception/module-db
composer require --dev codeception/module-asserts

# Bootstrap Codeception (if not already initialized)
vendor/bin/codecept bootstrap
```

### Configuration Files

#### codeception.yml

Create or update the main Codeception configuration file:

```yaml
# codeception.yml
namespace: Tests
support_namespace: Support
paths:
    tests: tests
    output: tests/_output
    data: tests/_data
    support: tests/_support
    envs: tests/_envs

actor_suffix: Tester

extensions:
    enabled:
        - Codeception\Extension\RunFailed

params:
    - .env.testing

settings:
    shuffle: true
    lint: true
```

#### Environment Configuration

Create a dedicated testing environment file:

```bash
# .env.testing
APP_ENV=testing
APP_DEBUG=true

# Database Configuration
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=platform_api_test
DB_USERNAME=test_user
DB_PASSWORD=test_password

# Redis Configuration
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DATABASE=1

# External API Mocking
EXTERNAL_API_MOCK=true
SIP_GATEWAY_MOCK=true

# OAuth Testing
OAUTH_TEST_CLIENT_ID=test-client-id
OAUTH_TEST_CLIENT_SECRET=test-client-secret
```

### Database Setup for Testing

Set up a dedicated test database with proper isolation:

```sql
-- Create test database
CREATE DATABASE platform_api_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create test user with limited permissions
CREATE USER 'test_user'@'localhost' IDENTIFIED BY 'test_password';
GRANT ALL PRIVILEGES ON platform_api_test.* TO 'test_user'@'localhost';
FLUSH PRIVILEGES;
```

### Docker-Based Test Environment

For consistent and isolated testing, use Docker Compose:

```yaml
# docker-compose.testing.yml
version: '3.8'

services:
  platform-api-test:
    build:
      context: .
      dockerfile: Dockerfile.test
    environment:
      - APP_ENV=testing
      - DB_HOST=mysql-test
      - REDIS_HOST=redis-test
    depends_on:
      - mysql-test
      - redis-test
    volumes:
      - ./tests:/app/tests
      - ./tests/_output:/app/tests/_output

  mysql-test:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: platform_api_test
      MYSQL_USER: test_user
      MYSQL_PASSWORD: test_password
    tmpfs:
      - /var/lib/mysql

  redis-test:
    image: redis:7-alpine
    command: redis-server --appendonly no
```

## Running Tests

### Basic Test Execution

Run all tests using the Codeception command:

```bash
# Run all test suites
vendor/bin/codecept run

# Run with verbose output
vendor/bin/codecept run -v

# Run with detailed step-by-step output
vendor/bin/codecept run --steps

# Run with debug information
vendor/bin/codecept run --debug
```

### Running Specific Test Suites

The platform-api organizes tests into multiple suites:

```bash
# Run unit tests only
vendor/bin/codecept run unit

# Run API/functional tests
vendor/bin/codecept run api

# Run integration tests
vendor/bin/codecept run integration

# Run acceptance tests
vendor/bin/codecept run acceptance
```

### Running Individual Tests

Target specific test files or methods:

```bash
# Run a specific test file
vendor/bin/codecept run api tests/api/UserManagementCest.php

# Run a specific test method
vendor/bin/codecept run api UserManagementCest:testCreateUser

# Run tests matching a pattern
vendor/bin/codecept run api -g billing
```

### Parallel Test Execution

For faster feedback on large test suites:

```bash
# Run tests in parallel (requires roave/better-reflection)
vendor/bin/codecept run --shard 1/4  # Run first quarter
vendor/bin/codecept run --shard 2/4  # Run second quarter

# Using paratest for true parallel execution
vendor/bin/paratest -p 4 --runner=WrapperRunner
```

### Code Coverage Reports

Generate coverage reports to identify untested code:

```bash
# Generate HTML coverage report
vendor/bin/codecept run --coverage --coverage-html

# Generate XML coverage for CI tools
vendor/bin/codecept run --coverage --coverage-xml

# Generate Clover format for code quality tools
vendor/bin/codecept run --coverage --coverage-clover coverage.xml
```

### Handling Failed Tests

Re-run only failed tests for faster iteration:

```bash
# Re-run failed tests
vendor/bin/codecept run -g failed

# Clean failed tests list
vendor/bin/codecept clean
```

## Writing Tests

### Test Suite Structure

Organize tests following the platform-api domain structure:

```
tests/
├── _data/
│   ├── fixtures/
│   │   ├── users.php
│   │   ├── organizations.php
│   │   ├── billing_plans.php
│   │   └── dialplans.php
│   └── seeds/
│       └── test_data.sql
├── _support/
│   ├── ApiTester.php
│   ├── UnitTester.php
│   ├── Helper/
│   │   ├── Api.php
│   │   ├── Auth.php
│   │   └── Database.php
│   └── Page/
│       ├── UserEndpoint.php
│       └── BillingEndpoint.php
├── api/
│   ├── UserManagementCest.php
│   ├── OrganizationCest.php
│   ├── BillingCest.php
│   └── DialplanCest.php
├── unit/
│   ├── Models/
│   ├── Services/
│   └── Validators/
└── integration/
    ├── SipGatewayCest.php
    └── CdrProcessingCest.php
```

### Writing Unit Tests

Unit tests focus on individual components in isolation:

```php
<?php
// tests/unit/Services/BillingCalculatorTest.php

namespace Tests\Unit\Services;

use Codeception\Test\Unit;
use App\Services\BillingCalculator;
use App\Models\Rate;
use App\Models\CallRecord;

class BillingCalculatorTest extends Unit
{
    protected BillingCalculator $calculator;

    protected function _before()
    {
        $this->calculator = new BillingCalculator();
    }

    public function testCalculateCallCostWithStandardRate()
    {
        // Arrange
        $rate = new Rate([
            'rate_per_minute' => 0.05,
            'connection_fee' => 0.01,
            'billing_increment' => 6,
            'minimum_duration' => 0
        ]);
        
        $callRecord = new CallRecord([
            'duration_seconds' => 125,  // 2 minutes 5 seconds
            'destination' => '+1234567890'
        ]);

        // Act
        $cost = $this->calculator->calculateCost($callRecord, $rate);

        // Assert
        // 126 seconds (rounded to next 6-second increment) = 2.1 minutes
        // Cost: 0.01 (connection) + (2.1 * 0.05) = 0.115
        $this->assertEquals(0.115, $cost, '', 0.001);
    }

    public function testCalculateCallCostWithMinimumDuration()
    {
        $rate = new Rate([
            'rate_per_minute' => 0.10,
            'connection_fee' => 0.00,
            'billing_increment' => 60,
            'minimum_duration' => 60
        ]);
        
        $callRecord = new CallRecord([
            'duration_seconds' => 15,
            'destination' => '+1234567890'
        ]);

        $cost = $this->calculator->calculateCost($callRecord, $rate);

        // Minimum 60 seconds charged
        $this->assertEquals(0.10, $cost);
    }

    /**
     * @dataProvider invalidDurationProvider
     */
    public function testRejectsInvalidDurations($duration)
    {
        $this->expectException(\InvalidArgumentException::class);
        
        $callRecord = new CallRecord(['duration_seconds' => $duration]);
        $rate = new Rate(['rate_per_minute' => 0.05]);
        
        $this->calculator->calculateCost($callRecord, $rate);
    }

    public function invalidDurationProvider(): array
    {
        return [
            'negative duration' => [-1],
            'null duration' => [null],
            'string duration' => ['invalid'],
        ];
    }
}
```

### Writing API Tests

API tests validate endpoint behavior and responses:

```php
<?php
// tests/api/UserManagementCest.php

namespace Tests\Api;

use Tests\Support\ApiTester;
use Codeception\Util\HttpCode;

class UserManagementCest
{
    private string $authToken;
    private int $testUserId;

    public function _before(ApiTester $I)
    {
        // Authenticate before each test
        $I->haveHttpHeader('Content-Type', 'application/json');
        $I->sendPost('/oauth/token', [
            'grant_type' => 'client_credentials',
            'client_id' => getenv('OAUTH_TEST_CLIENT_ID'),
            'client_secret' => getenv('OAUTH_TEST_CLIENT_SECRET'),
            'scope' => 'users:read users:write'
        ]);
        
        $this->authToken = $I->grabDataFromResponseByJsonPath('$.access_token')[0];
        $I->amBearerAuthenticated($this->authToken);
    }

    /**
     * @group users
     * @group crud
     */
    public function testCreateUserWithValidData(ApiTester $I)
    {
        $I->wantTo('create a new user with valid data');
        
        $userData = [
            'email' => 'test.user.' . time() . '@example.com',
            'username' => 'testuser_' . time(),
            'password' => 'SecureP@ssw0rd123',
            'first_name' => 'Test',
            'last_name' => 'User',
            'organization_id' => 1,
            'role' => 'user'
        ];

        $I->sendPost('/api/v1/users', $userData);
        
        $I->seeResponseCodeIs(HttpCode::CREATED);
        $I->seeResponseIsJson();
        $I->seeResponseMatchesJsonType([
            'id' => 'integer',
            'email' => 'string:email',
            'username' => 'string',
            'created_at' => 'string:date',
            'organization' => [
                'id' => 'integer',
                'name' => 'string'
            ]
        ]);
        
        $I->seeResponseContainsJson([
            'email' => $userData['email'],
            'username' => $userData['username'],
            'first_name' => $userData['first_name']
        ]);
        
        // Store for cleanup
        $this->testUserId = $I->grabDataFromResponseByJsonPath('$.id')[0];
    }

    /**
     * @group users
     * @group validation
     */
    public function testCreateUserWithDuplicateEmailFails(ApiTester $I)
    {
        $I->wantTo('ensure duplicate emails are rejected');
        
        // Create first user
        $email = 'duplicate.' . time() . '@example.com';
        $I->sendPost('/api/v1/users', [
            'email' => $email,
            'username' => 'user1_' . time(),
            'password' => 'SecureP@ssw0rd123',
            'organization_id' => 1
        ]);
        $I->seeResponseCodeIs(HttpCode::CREATED);
        
        // Attempt to create second user with same email
        $I->sendPost('/api/v1/users', [
            'email' => $email,
            'username' => 'user2_' . time(),
            'password' => 'SecureP@ssw0rd123',
            'organization_id' => 1
        ]);
        
        $I->seeResponseCodeIs(HttpCode::UNPROCESSABLE_ENTITY);
        $I->seeResponseContainsJson([
            'errors' => [
                'email' => ['The email has already been taken.']
            ]
        ]);
    }

    /**
     * @group users
     * @group pagination
     */
    public function testListUsersWithPagination(ApiTester $I)
    {
        $I->wantTo('retrieve paginated list of users');
        
        $I->sendGet('/api/v1/users', [
            'page' => 1,
            'per_page' => 10,
            'sort' => 'created_at',
            'order' => 'desc'
        ]);
        
        $I->seeResponseCodeIs(HttpCode::OK);
        $I->seeResponseMatchesJsonType([
            'data' => 'array',
            'meta' => [
                'current_page' => 'integer',
                'per_page' => 'integer',
                'total' => 'integer',
                'last_page' => 'integer'
            ],
            'links' => [
                'first' => 'string:url',
                'last' => 'string:url'
            ]
        ]);
    }

    /**
     * @group users
     * @group security
     */
    public function testUnauthorizedAccessIsDenied(ApiTester $I)
    {
        $I->wantTo('verify unauthorized requests are rejected');
        
        // Remove authentication
        $I->deleteHeader('Authorization');
        
        $I->sendGet('/api/v1/users');
        
        $I->seeResponseCodeIs(HttpCode::UNAUTHORIZED);
        $I->seeResponseContainsJson([
            'error' => 'Unauthenticated.'
        ]);
    }
}
```

### Writing Integration Tests

Integration tests verify interactions with external systems:

```php
<?php
// tests/integration/SipGatewayCest.php

namespace Tests\Integration;

use Tests\Support\ApiTester;
use Codeception\Util\HttpCode;

class SipGatewayCest
{
    /**
     * @group integration
     * @group sip
     */
    public function testProvisionSipTrunk(ApiTester $I)
    {
        $I->wantTo('provision a new SIP trunk and verify gateway configuration');
        
        // Create trunk via API
        $trunkData = [
            'name' => 'test-trunk-' . time(),
            'gateway_id' => 1,
            'channels' => 30,
            'codec_priority' => ['G711A', 'G711U', 'G729'],
            'authentication' => [
                'type' => 'ip',
                'allowed_ips' => ['192.168.1.100', '192.168.1.101']
            ]
        ];
        
        $I->sendPost('/api/v1/sip/trunks', $trunkData);
        $I->seeResponseCodeIs(HttpCode::CREATED);
        
        $trunkId = $I->grabDataFromResponseByJsonPath('$.id')[0];
        
        // Verify trunk was provisioned on gateway
        $I->sendGet("/api/v1/sip/trunks/{$trunkId}/status");
        $I->seeResponseCodeIs(HttpCode::OK);
        $I->seeResponseContainsJson([
            'provisioned' => true,
            'gateway_status' => 'active'
        ]);
        
        // Verify registration status
        $I->sendGet("/api/v1/sip/trunks/{$trunkId}/registrations");
        $I->seeResponseCodeIs(HttpCode::OK);
    }

    /**
     * @group integration
     * @group cdr
     */
    public function testCdrProcessingPipeline(ApiTester $I)
    {
        $I->wantTo('verify CDR records are processed and stored correctly');
        
        // Submit raw CDR data
        $cdrData = [
            'call_id' => 'test-call-' . uniqid(),
            'caller_id' => '+15551234567',
            'callee_id' => '+15559876543',
            'start_time' => date('Y-m-d H:i:s', strtotime('-5 minutes')),
            'end_time' => date('Y-m-d H:i:s'),
            'duration' => 300,
            'disposition' => 'ANSWERED',
            'trunk_id' => 1
        ];
        
        $I->sendPost('/api/v1/cdr/ingest', $cdrData);
        $I->seeResponseCodeIs(HttpCode::ACCEPTED);
        
        // Wait for async processing
        sleep(2);
        
        // Verify CDR was processed
        $I->sendGet('/api/v1/cdr/records', [
            'call_id' => $cdrData['call_id']
        ]);
        
        $I->seeResponseCodeIs(HttpCode::OK);
        $I->seeResponseContainsJson([
            'data' => [[
                'call_id' => $cdrData['call_id'],
                'processed' => true,
                'billing_applied' => true
            ]]
        ]);
    }
}
```

### Creating Test Helpers

Build reusable helpers for common operations:

```php
<?php
// tests/_support/Helper/Api.php

namespace Tests\Support\Helper;

use Codeception\Module;

class Api extends Module
{
    public function createTestUser(array $overrides = []): array
    {
        $defaults = [
            'email' => 'test.' . uniqid() . '@example.com',
            'username' => 'testuser_' . uniqid(),
            'password' => 'TestP@ssw0rd123',
            'organization_id' => 1,
            'role' => 'user'
        ];
        
        return array_merge($defaults, $overrides);
    }

    public function createTestOrganization(array $overrides = []): array
    {
        $defaults = [
            'name' => 'Test Organization ' . uniqid(),
            'billing_email' => 'billing.' . uniqid() . '@example.com',
            'plan_id' => 1,
            'status' => 'active'
        ];
        
        return array_merge($defaults, $overrides);
    }

    public function getAdminAuthToken(): string
    {
        $rest = $this->getModule('REST');
        
        $rest->sendPost('/oauth/token', [
            'grant_type' => 'client_credentials',
            'client_id' => getenv('OAUTH_ADMIN_CLIENT_ID'),
            'client_secret' => getenv('OAUTH_ADMIN_CLIENT_SECRET'),
            'scope' => '*'
        ]);
        
        return $rest->grabDataFromResponseByJsonPath('$.access_token')[0];
    }
}
```

## Test Categories

### Unit Tests

Unit tests verify individual components in isolation without external dependencies.

| Category | Focus Area | Coverage Target |
|----------|-----------|-----------------|
| Models | Data validation, relationships, accessors | 90% |
| Services | Business logic, calculations | 95% |
| Validators | Input validation rules | 100% |
| Transformers | Data transformation | 90% |
| Helpers | Utility functions | 85% |

**When to write unit tests:**
- Testing pure business logic
- Validating calculations (billing, rates)
- Testing data transformations
- Verifying validation rules

### API/Functional Tests

API tests validate endpoint behavior and HTTP interactions.

| Category | Focus Area | Coverage Target |
|----------|-----------|-----------------|
| Authentication | OAuth flows, token validation | 100% |
| CRUD Operations | Create, read, update, delete | 95% |
| Validation | Request validation, error responses | 95% |
| Authorization | Permission checks, role-based access | 100% |
| Pagination | List endpoints, filtering, sorting | 90% |

**When to write API tests:**
- Testing endpoint responses
- Validating authentication/authorization
- Testing error handling
- Verifying API contracts

### Integration Tests

Integration tests verify interactions between the platform-api and external systems.

| Category | Focus Area | Priority |
|----------|-----------|----------|
| SIP Gateway | Trunk provisioning, registration | High |
| Database | Complex queries, transactions | High |
| CDR Processing | Call record ingestion | High |
| External APIs | Third-party integrations | Medium |
| Cache | Redis operations | Medium |

**When to write integration tests:**
- Testing database transactions
- Verifying external API calls
- Testing message queue processing
- Validating cache behavior

### Performance Tests

```php
<?php
// tests/performance/ApiLoadTest.php

namespace Tests\Performance;

use Tests\Support\ApiTester;

class ApiLoadTest
{
    /**
     * @group performance
     * @group slow
     */
    public function testUserListEndpointPerformance(ApiTester $I)
    {
        $I->wantTo('verify user list endpoint responds within SLA');
        
        $startTime = microtime(true);
        
        $I->sendGet('/api/v1/users', ['per_page' => 100]);
        
        $responseTime = microtime(true) - $startTime;
        
        $I->seeResponseCodeIs(200);
        $I->assertLessThan(0.5, $responseTime, 'Response time should be under 500ms');
    }
}
```

## CI/CD Integration

### GitHub Actions Configuration

```yaml
# .github/workflows/tests.yml
name: Platform API Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: '8.2'
          extensions: mbstring, pdo_mysql, redis
          coverage: xdebug
      
      - name: Install Dependencies
        run: composer install --prefer-dist --no-progress
      
      - name: Run Unit Tests
        run: vendor/bin/codecept run unit --coverage --coverage-xml
      
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        with:
          files: tests/_output/coverage.xml

  api-tests:
    runs-on: ubuntu-latest
    
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: platform_api_test
        ports:
          - 3306:3306
        options: --health-cmd="mysqladmin ping" --health-interval=10s --health-timeout=5s --health-retries=3
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: --health-cmd="redis-cli ping" --health-interval=10s --health-timeout=5s --health-retries=3
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: '8.2'
          extensions: mbstring, pdo_mysql, redis
      
      - name: Install Dependencies
        run: composer install --prefer-dist --no-progress
      
      - name: Setup Database
        run: |
          php artisan migrate --env=testing --force
          php artisan db:seed --class=TestDataSeeder --env=testing
      
      - name: Run API Tests
        run: vendor/bin/codecept run api --steps
        env:
          DB_HOST: 127.0.0.1
          REDIS_HOST: 127.0.0.1

  integration-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, api-tests]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Start Services
        run: docker-compose -f docker-compose.testing.yml up -d
      
      - name: Wait for Services
        run: |
          docker-compose -f docker-compose.testing.yml exec -T platform-api-test \
            php artisan wait:database --timeout=60
      
      - name: Run Integration Tests
        run: |
          docker-compose -f docker-compose.testing.yml exec -T platform-api-test \
            vendor/bin/codecept run integration
      
      - name: Cleanup
        if: always()
        run: docker-compose -f docker-compose.testing.yml down -v
```

### GitLab CI Configuration

```yaml
# .gitlab-ci.yml
stages:
  - test
  - coverage
  - report

variables:
  MYSQL_ROOT_PASSWORD: root
  MYSQL_DATABASE: platform_api_test
  MYSQL_USER: test_user
  MYSQL_PASSWORD: test_password

unit-tests:
  stage: test
  image: php:8.2-cli
  services:
    - mysql:8.0
    - redis:7-alpine
  before_script:
    - apt-get update && apt-get install -y git unzip libzip-dev
    - docker-php-ext-install pdo_mysql zip
    - curl -sS https://getcomposer.org/installer | php
    - php composer.phar install --prefer-dist --no-progress
  script:
    - vendor/bin/codecept run unit --coverage --coverage-xml --coverage-html
  artifacts:
    paths:
      - tests/_output/coverage/
    reports:
      coverage_report:
        coverage_format: cobertura
        path: tests/_output/coverage.xml

api-tests:
  stage: test
  image: php:8.2-cli
  services:
    - mysql:8.0
    - redis:7-alpine
  script:
    - vendor/bin/codecept run api --xml
  artifacts:
    reports:
      junit: tests/_output/report.xml
```

### Pre-commit Hooks

Set up Git hooks for local testing:

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running pre-commit tests..."

# Run fast unit tests
vendor/bin/codecept run unit --no-colors

if [ $? -ne 0 ]; then
    echo "Unit tests failed. Commit aborted."
    exit 1
fi

# Run linting
vendor/bin/phpcs --standard=PSR12 app/

if [ $? -ne 0 ]; then
    echo "Code style issues found. Commit aborted."
    exit 1
fi

echo "All checks passed!"
exit 0
```

### Test Reporting and Metrics

Configure test reporting for visibility:

```php
<?php
// codeception.yml additions for reporting
extensions:
    enabled:
        - Codeception\Extension\RunFailed
    config:
        Codeception\Extension\RunFailed:
            file: tests/_output/failed

coverage:
    enabled: true
    include:
        - app/*
    exclude:
        - app/Console/Kernel.php
        - app/Exceptions/Handler.php

reports:
    html: tests/_output/report.html
    xml: tests/_output/report.xml
    json: tests/_output/report.json
```

## Best Practices and Common Pitfalls

### Best Practices

1. **Test Isolation**: Each test should be independent and not rely on state from other tests
2. **Meaningful Names**: Use descriptive test names that explain the expected behavior
3. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification phases
4. **Test Data Factories**: Use factories to create test data consistently
5. **Mock External Services**: Always mock external APIs in unit and API tests
6. **Database Transactions**: Use transactions to rollback test data automatically

### Common Pitfalls

1. **Shared State**: Avoid global variables or shared state between tests
2. **Hardcoded IDs**: Don't rely on specific database IDs that may change
3. **Timing Issues**: Be careful with tests that depend on time or async operations
4. **Over-mocking**: Don't mock so much that you're not testing real behavior
5. **Ignoring Failures**: Never ignore flaky tests—fix them or remove them

## Conclusion

This testing guide provides a comprehensive framework for maintaining high code quality in the platform-api service. By following the practices outlined here and maintaining strong test coverage across all 150 endpoints and 100 data models, you can ensure reliable, secure, and performant operation of your telecommunications platform.

Regular execution of the full test suite in CI/CD pipelines, combined with pre-commit hooks for rapid feedback, creates a robust safety net that catches issues before they reach production. Remember to continuously update and expand your test coverage as new features are added and edge cases are discovered.