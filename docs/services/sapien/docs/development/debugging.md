# Debugging Guide

## Overview

This comprehensive guide covers debugging techniques and tools for the Sapien API service. Sapien is a PHP-based REST API built on Symfony, and this documentation provides detailed instructions for setting up Xdebug, configuring PhpStorm integration, utilizing the Symfony profiler, capturing network traffic, and resolving common debugging issues.

Effective debugging is essential for maintaining and extending the Sapien service, which manages entities like Person, Pet, and Toy through RESTful CRUD operations. With Docker-based development, OAuth2 authentication, ESL event systems, and rate limiting, understanding how to debug across these layers is critical for development efficiency.

---

## Xdebug Setup

### Understanding Xdebug in Sapien

Xdebug is the primary debugging extension for PHP in the Sapien service. It enables step debugging, stack traces, profiling, and code coverage analysis. The Docker-based development environment comes pre-configured with Xdebug support.

### Docker Configuration for Xdebug

The Sapien Docker environment includes Xdebug configuration in the PHP container. Verify your `docker-compose.yml` includes the following configuration:

```yaml
# docker-compose.yml
services:
  php:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - XDEBUG_MODE=debug,develop,profile
      - XDEBUG_CONFIG=client_host=host.docker.internal client_port=9003 start_with_request=trigger
      - XDEBUG_SESSION=PHPSTORM
    volumes:
      - ./:/var/www/html
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

### Xdebug PHP Configuration

Create or modify the Xdebug configuration file within your Docker container:

```ini
; /usr/local/etc/php/conf.d/xdebug.ini

[xdebug]
zend_extension=xdebug

; Debug mode settings
xdebug.mode=debug,develop,profile
xdebug.start_with_request=trigger
xdebug.discover_client_host=false
xdebug.client_host=host.docker.internal
xdebug.client_port=9003

; IDE key for PhpStorm
xdebug.idekey=PHPSTORM

; Profiler settings
xdebug.output_dir=/var/www/html/var/profiler
xdebug.profiler_output_name=cachegrind.out.%p.%t

; Log settings for troubleshooting
xdebug.log=/var/www/html/var/log/xdebug.log
xdebug.log_level=3

; Performance settings
xdebug.max_nesting_level=512
xdebug.var_display_max_depth=10
xdebug.var_display_max_data=2048
```

### Verifying Xdebug Installation

Execute the following commands to verify Xdebug is properly installed:

```bash
# Enter the PHP container
docker-compose exec php bash

# Check Xdebug is loaded
php -v
# Should show: with Xdebug v3.x.x

# Verify Xdebug configuration
php -i | grep xdebug

# Check Xdebug mode
php -r "echo xdebug_info();"
```

### Xdebug Modes Reference

| Mode | Purpose | Use Case |
|------|---------|----------|
| `debug` | Step debugging | Interactive debugging sessions |
| `develop` | Development helpers | Enhanced var_dump, error display |
| `profile` | Profiling | Performance analysis |
| `coverage` | Code coverage | Unit test coverage reports |
| `trace` | Function tracing | Execution flow analysis |

---

## PhpStorm Configuration

### Initial PhpStorm Setup

#### Step 1: Configure PHP Interpreter

1. Navigate to **File → Settings → PHP**
2. Click the **...** button next to CLI Interpreter
3. Click **+** and select **From Docker, Vagrant, VM, WSL, Remote...**
4. Choose **Docker Compose**
5. Select your `docker-compose.yml` file
6. Choose the `php` service
7. PhpStorm will automatically detect the PHP version

```
Configuration Summary:
- Server: Docker Compose
- Configuration file: ./docker-compose.yml
- Service: php
- PHP executable: php
```

#### Step 2: Configure Debug Port

1. Go to **File → Settings → PHP → Debug**
2. Set the following configuration:

```
Debug Port: 9003
□ Force break at first line when no path mapping specified
☑ Force break at first line when a script is outside the project
☑ Ignore external connections through unregistered server configurations

External Connections:
☑ Break at first line in PHP scripts
Max. simultaneous connections: 5
```

#### Step 3: Configure Server Mapping

1. Navigate to **File → Settings → PHP → Servers**
2. Click **+** to add a new server
3. Configure as follows:

```
Name: sapien-docker
Host: localhost
Port: 8080
Debugger: Xdebug

Use path mappings: ☑
Project files:
  /path/to/local/sapien → /var/www/html
```

### Setting Up Debug Configurations

#### Run/Debug Configuration for API Requests

1. Go to **Run → Edit Configurations**
2. Click **+** and select **PHP Remote Debug**
3. Configure:

```
Name: Sapien API Debug
Filter debug connection by IDE key: ☑
Server: sapien-docker
IDE key(session id): PHPSTORM
```

#### Debug Configuration for CLI Commands

```
Name: Sapien Console Debug
Configuration:
  Type: PHP Script
  File: bin/console
  Arguments: [your-command]
  Interpreter: Docker Compose (php)
```

### Browser Extension Setup

Install browser extensions for triggering debug sessions:

**Chrome/Firefox:**
- Install "Xdebug Helper" extension
- Right-click the extension icon → Options
- Set IDE key to: `PHPSTORM`

**Manual Trigger via URL:**
```
# Add to any request URL
?XDEBUG_SESSION_START=PHPSTORM

# Or use cookie
XDEBUG_SESSION=PHPSTORM
```

### Debugging Workflow Example

```php
<?php
// src/Controller/PersonController.php

namespace App\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Annotation\Route;

class PersonController extends AbstractController
{
    #[Route('/api/persons', methods: ['POST'])]
    public function create(Request $request): JsonResponse
    {
        // Set breakpoint here to inspect incoming request
        $data = json_decode($request->getContent(), true);
        
        // Validate input data
        if (!isset($data['name'])) {
            // Breakpoint: inspect validation flow
            return $this->json(['error' => 'Name is required'], 400);
        }
        
        // Process entity creation
        $person = $this->personService->create($data);
        
        // Breakpoint: verify entity before response
        return $this->json($person, 201);
    }
}
```

---

## Profiler Usage

### Symfony Profiler Configuration

Enable the Symfony profiler in your development environment:

```yaml
# config/packages/dev/web_profiler.yaml
web_profiler:
    toolbar: true
    intercept_redirects: false

framework:
    profiler:
        enabled: true
        collect: true
        only_exceptions: false
```

### Accessing the Profiler

#### Web Profiler Toolbar

The profiler toolbar appears at the bottom of HTML responses. For API responses, access the profiler directly:

```bash
# Access profiler for a specific token
http://localhost:8080/_profiler/{token}

# List recent requests
http://localhost:8080/_profiler/

# Search profiler data
http://localhost:8080/_profiler/search
```

#### Profiler for API Requests

Since Sapien returns JSON responses, the toolbar won't render. Use response headers instead:

```bash
# Make an API request and check headers
curl -v http://localhost:8080/api/persons

# Look for:
# X-Debug-Token: abc123
# X-Debug-Token-Link: http://localhost:8080/_profiler/abc123
```

### Profiler Panels Reference

| Panel | Information | Use Case |
|-------|-------------|----------|
| Request/Response | Headers, parameters, content | API debugging |
| Doctrine | Queries, query time, hydration | Database optimization |
| Security | Authentication, authorization | OAuth2 debugging |
| Events | Dispatched events, listeners | ESL event debugging |
| Logs | Monolog entries | Error tracking |
| Performance | Timeline, memory usage | Performance analysis |

### Doctrine Query Profiling

Analyze database queries for your CRUD operations:

```php
<?php
// Enable SQL logging for specific debugging

namespace App\Service;

use Doctrine\ORM\EntityManagerInterface;

class PersonService
{
    public function findWithDebug(int $id): ?Person
    {
        // Access the SQL logger
        $logger = $this->entityManager
            ->getConnection()
            ->getConfiguration()
            ->getSQLLogger();
        
        $person = $this->personRepository->find($id);
        
        // Queries are now visible in profiler
        return $person;
    }
}
```

### Custom Profiler Data Collection

Create custom data collectors for Sapien-specific debugging:

```php
<?php
// src/DataCollector/SapienCollector.php

namespace App\DataCollector;

use Symfony\Bundle\FrameworkBundle\DataCollector\AbstractDataCollector;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;

class SapienCollector extends AbstractDataCollector
{
    public function collect(Request $request, Response $response, \Throwable $exception = null): void
    {
        $this->data = [
            'organization_id' => $request->headers->get('X-Organization-ID'),
            'rate_limit_remaining' => $response->headers->get('X-RateLimit-Remaining'),
            'oauth_token_used' => $request->headers->has('Authorization'),
            'esl_events_triggered' => $this->eslEventCounter,
        ];
    }
    
    public static function getTemplate(): ?string
    {
        return 'data_collector/sapien.html.twig';
    }
    
    public function getName(): string
    {
        return 'sapien';
    }
}
```

### Xdebug Profiler Analysis

Generate and analyze profiler output:

```bash
# Trigger profiling for a specific request
curl "http://localhost:8080/api/persons?XDEBUG_PROFILE=1"

# Profiler output location
ls -la var/profiler/cachegrind.out.*

# Analyze with KCacheGrind (Linux) or QCacheGrind (Mac/Windows)
kcachegrind var/profiler/cachegrind.out.12345.1234567890
```

---

## Traffic Capture

### Using Symfony's HTTP Client Debugging

Monitor outgoing HTTP requests to external APIs:

```php
<?php
// src/Service/ExternalApiService.php

namespace App\Service;

use Symfony\Contracts\HttpClient\HttpClientInterface;
use Psr\Log\LoggerInterface;

class ExternalApiService
{
    public function __construct(
        private HttpClientInterface $httpClient,
        private LoggerInterface $logger
    ) {}
    
    public function callExternalService(array $data): array
    {
        $this->logger->debug('External API Request', [
            'url' => $url,
            'method' => 'POST',
            'body' => $data,
        ]);
        
        $response = $this->httpClient->request('POST', $url, [
            'json' => $data,
        ]);
        
        $this->logger->debug('External API Response', [
            'status' => $response->getStatusCode(),
            'headers' => $response->getHeaders(),
            'body' => $response->getContent(),
        ]);
        
        return $response->toArray();
    }
}
```

### Docker Network Traffic Monitoring

```bash
# Monitor traffic within Docker network
docker-compose exec php tcpdump -i eth0 -A -s 0 'port 80 or port 443'

# Capture specific API traffic
docker-compose exec php tcpdump -i any -w /tmp/capture.pcap 'host api.external-service.com'
```

### Using mitmproxy for HTTPS Traffic

Set up mitmproxy in your Docker environment:

```yaml
# docker-compose.override.yml
services:
  mitmproxy:
    image: mitmproxy/mitmproxy:latest
    command: mitmweb --web-host 0.0.0.0
    ports:
      - "8081:8081"  # Web interface
      - "8082:8080"  # Proxy port
    volumes:
      - ./var/mitmproxy:/home/mitmproxy/.mitmproxy

  php:
    environment:
      - HTTP_PROXY=http://mitmproxy:8080
      - HTTPS_PROXY=http://mitmproxy:8080
```

### Request/Response Logging Middleware

```php
<?php
// src/EventSubscriber/RequestLogSubscriber.php

namespace App\EventSubscriber;

use Psr\Log\LoggerInterface;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use Symfony\Component\HttpKernel\Event\RequestEvent;
use Symfony\Component\HttpKernel\Event\ResponseEvent;
use Symfony\Component\HttpKernel\KernelEvents;

class RequestLogSubscriber implements EventSubscriberInterface
{
    public function __construct(
        private LoggerInterface $logger
    ) {}
    
    public static function getSubscribedEvents(): array
    {
        return [
            KernelEvents::REQUEST => ['onRequest', 100],
            KernelEvents::RESPONSE => ['onResponse', -100],
        ];
    }
    
    public function onRequest(RequestEvent $event): void
    {
        $request = $event->getRequest();
        
        $this->logger->info('API Request', [
            'method' => $request->getMethod(),
            'uri' => $request->getRequestUri(),
            'headers' => $request->headers->all(),
            'body' => $request->getContent(),
            'client_ip' => $request->getClientIp(),
        ]);
    }
    
    public function onResponse(ResponseEvent $event): void
    {
        $response = $event->getResponse();
        
        $this->logger->info('API Response', [
            'status' => $response->getStatusCode(),
            'headers' => $response->headers->all(),
            'body' => $response->getContent(),
        ]);
    }
}
```

### cURL Verbose Mode for API Testing

```bash
# Verbose API request with full headers
curl -v -X POST http://localhost:8080/api/persons \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_access_token" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

# Include timing information
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8080/api/persons
```

Create `curl-format.txt`:
```
     time_namelookup:  %{time_namelookup}s\n
        time_connect:  %{time_connect}s\n
     time_appconnect:  %{time_appconnect}s\n
    time_pretransfer:  %{time_pretransfer}s\n
       time_redirect:  %{time_redirect}s\n
  time_starttransfer:  %{time_starttransfer}s\n
                     ----------\n
          time_total:  %{time_total}s\n
```

---

## Common Issues

### Issue 1: Xdebug Connection Refused

**Symptoms:**
- Breakpoints not triggered
- PhpStorm shows "Waiting for incoming connection"
- Xdebug log shows connection errors

**Solutions:**

```bash
# Check Xdebug log for errors
docker-compose exec php tail -f /var/www/html/var/log/xdebug.log

# Verify host.docker.internal resolves
docker-compose exec php ping host.docker.internal

# Check port 9003 is accessible
# On host machine:
nc -l 9003
# In container:
docker-compose exec php nc -zv host.docker.internal 9003
```

**PhpStorm Firewall Configuration (Windows):**
```powershell
# Allow PhpStorm through firewall
netsh advfirewall firewall add rule name="PhpStorm Xdebug" dir=in action=allow protocol=TCP localport=9003
```

### Issue 2: Path Mapping Errors

**Symptoms:**
- "Cannot find file" errors in PhpStorm
- Breakpoints show as unverified
- Step debugging jumps to wrong files

**Solutions:**

```
# Verify path mapping in PhpStorm
Settings → PHP → Servers → sapien-docker

Local path: /Users/developer/projects/sapien
Remote path: /var/www/html

# Common mapping issues:
- Trailing slashes mismatch
- Case sensitivity (Linux containers)
- Symlink resolution differences
```

### Issue 3: OAuth2 Token Debugging

**Symptoms:**
- 401 Unauthorized responses
- Token refresh failures
- Authentication flow issues

**Debug Steps:**

```php
<?php
// Add debugging to token validation

namespace App\Security;

use Psr\Log\LoggerInterface;

class TokenValidator
{
    public function validate(string $token): bool
    {
        $this->logger->debug('Token validation started', [
            'token_prefix' => substr($token, 0, 20) . '...',
            'token_length' => strlen($token),
        ]);
        
        try {
            $decoded = $this->jwtDecoder->decode($token);
            
            $this->logger->debug('Token decoded', [
                'exp' => $decoded['exp'],
                'iat' => $decoded['iat'],
                'org_id' => $decoded['org_id'] ?? 'missing',
            ]);
            
            return true;
        } catch (\Exception $e) {
            $this->logger->error('Token validation failed', [
                'error' => $e->getMessage(),
            ]);
            return false;
        }
    }
}
```

### Issue 4: Rate Limiting Debug

**Symptoms:**
- 429 Too Many Requests responses
- Inconsistent rate limit behavior
- Organization-specific issues

**Debug Commands:**

```bash
# Check current rate limit status
curl -I http://localhost:8080/api/persons \
  -H "Authorization: Bearer your_token"

# Response headers to check:
# X-RateLimit-Limit: 1000
# X-RateLimit-Remaining: 999
# X-RateLimit-Reset: 1640000000

# Clear rate limit cache (Redis)
docker-compose exec redis redis-cli KEYS "rate_limit:*"
docker-compose exec redis redis-cli DEL "rate_limit:org_123"
```

### Issue 5: ESL Event System Issues

**Symptoms:**
- Events not being dispatched
- Availability updates not reflecting
- Event listener errors

**Debug Approach:**

```php
<?php
// src/EventSubscriber/DebugEventSubscriber.php

namespace App\EventSubscriber;

use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use App\Event\AvailabilityUpdateEvent;
use Psr\Log\LoggerInterface;

class DebugEventSubscriber implements EventSubscriberInterface
{
    public function __construct(
        private LoggerInterface $logger
    ) {}
    
    public static function getSubscribedEvents(): array
    {
        return [
            AvailabilityUpdateEvent::class => ['onAvailabilityUpdate', 1000],
        ];
    }
    
    public function onAvailabilityUpdate(AvailabilityUpdateEvent $event): void
    {
        $this->logger->debug('ESL Event Dispatched', [
            'event_class' => get_class($event),
            'entity_type' => $event->getEntityType(),
            'entity_id' => $event->getEntityId(),
            'changes' => $event->getChanges(),
            'timestamp' => (new \DateTime())->format('c'),
        ]);
    }
}
```

### Issue 6: Docker Container Debugging

**Symptoms:**
- Container crashes
- Service unavailable
- Memory/CPU issues

**Debug Commands:**

```bash
# View container logs
docker-compose logs -f php

# Check container resource usage
docker stats sapien_php_1

# Enter container for debugging
docker-compose exec php bash

# Check PHP-FPM status
docker-compose exec php php-fpm-healthcheck

# Verify PHP extensions
docker-compose exec php php -m | grep -E "(xdebug|pdo|redis)"

# Check PHP error log
docker-compose exec php tail -f /var/log/php/error.log
```

### Issue 7: Profiler Not Collecting Data

**Symptoms:**
- Empty profiler panels
- Missing database queries
- No timeline data

**Solutions:**

```yaml
# Ensure profiler is enabled in dev
# config/packages/dev/framework.yaml
framework:
    profiler:
        enabled: true
        collect: true
        only_exceptions: false
        only_master_requests: false
```

```php
<?php
// Force profiler collection for API requests
// src/EventSubscriber/ProfilerSubscriber.php

use Symfony\Component\HttpKernel\Profiler\Profiler;

class ProfilerSubscriber implements EventSubscriberInterface
{
    public function onResponse(ResponseEvent $event): void
    {
        if ($this->profiler && $event->isMainRequest()) {
            $this->profiler->collect(
                $event->getRequest(),
                $event->getResponse()
            );
        }
    }
}
```

---

## Additional Resources

### Debug Environment Variables

```bash
# .env.local for debugging
APP_ENV=dev
APP_DEBUG=true
XDEBUG_MODE=debug,develop,profile
XDEBUG_SESSION=PHPSTORM

# Database debugging
DATABASE_DEBUG=true
DOCTRINE_SQL_LOGGING=true

# Detailed error output
SYMFONY_DEPRECATIONS_HELPER=disabled
```

### Useful Debugging Commands

```bash
# Clear all caches
docker-compose exec php bin/console cache:clear

# Warm up caches
docker-compose exec php bin/console cache:warmup

# Debug router
docker-compose exec php bin/console debug:router

# Debug container services
docker-compose exec php bin/console debug:container

# Debug event dispatcher
docker-compose exec php bin/console debug:event-dispatcher

# Debug autowiring
docker-compose exec php bin/console debug:autowiring
```

This guide provides comprehensive debugging capabilities for the Sapien service. For additional support, consult the Symfony documentation and Xdebug manual for advanced debugging scenarios.