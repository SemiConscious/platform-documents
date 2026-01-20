# Platform-API (CoreAPI)

> **Last Updated**: 2026-01-20  
> **Repository**: [redmatter/platform-api](https://github.com/redmatter/platform-api)  
> **Language**: PHP (Kohana Framework)  
> **Status**: Production - Legacy Monolith (being gradually decomposed via Strangler pattern)

## Overview

Platform-API (also known as CoreAPI) is the central internal API hub for the Natterbox platform. It serves as the primary interface between the web portal, mobile applications, and the underlying databases and services. This is a PHP-based monolithic application built on the Kohana framework that handles all core platform operations including user management, call control, dialplan configuration, and organization administration.

### Key Responsibilities

- **Database Hub**: Primary interface to all platform databases (Organization, CDR, Freeswitch, LCR, Billing)
- **Call Control**: Real-time call management and FreeSWITCH integration
- **User Management**: Authentication, authorization, and user administration
- **Dialplan Generation**: Dynamic generation of FreeSWITCH dialplans
- **Organization Management**: Multi-tenant organization configuration
- **Device Management**: SIP phones, softphones, and mobile device provisioning
- **Caching**: Memcached-based caching for performance optimization

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Platform Architecture                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐  │
│  │   Web Portal │   │  Mobile App  │   │    Sapien    │   │  FreeSWITCH  │  │
│  │   (Vue.js)   │   │  (iOS/Andr)  │   │  (Public API)│   │   Servers    │  │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘  │
│         │                  │                  │                  │          │
│         └──────────────────┴────────┬─────────┴──────────────────┘          │
│                                     │                                        │
│                                     ▼                                        │
│         ┌───────────────────────────────────────────────────────┐           │
│         │                   Platform-API (CoreAPI)               │           │
│         │  ┌─────────────────────────────────────────────────┐  │           │
│         │  │                  Controllers                     │  │           │
│         │  │  auth, users, orgs, callcontrol, dialplan, etc. │  │           │
│         │  └─────────────────────┬───────────────────────────┘  │           │
│         │                        │                               │           │
│         │  ┌─────────────────────▼───────────────────────────┐  │           │
│         │  │                Service Layer                     │  │           │
│         │  │  AuthService, UserService, CallControlService,  │  │           │
│         │  │  OrgService, FSDialplanService, etc.            │  │           │
│         │  └─────────────────────┬───────────────────────────┘  │           │
│         │                        │                               │           │
│         │  ┌─────────────────────▼───────────────────────────┐  │           │
│         │  │                  Base Service                    │  │           │
│         │  │  Database connections, caching, logging         │  │           │
│         │  └─────────────────────┬───────────────────────────┘  │           │
│         └────────────────────────┼───────────────────────────────┘           │
│                                  │                                           │
│         ┌────────────────────────┼────────────────────────────┐              │
│         │                        ▼                            │              │
│  ┌──────┴──────┐  ┌─────────────────────────┐  ┌─────────────┴──────┐       │
│  │   OrgDB     │  │       BigDB (CDR)       │  │   FreeSwitchDB     │       │
│  │  (MySQL)    │  │       (MySQL)           │  │     (MySQL)        │       │
│  │  - orgs     │  │  - cdr_records          │  │  - sofia_contacts  │       │
│  │  - users    │  │  - call_logs            │  │  - registrations   │       │
│  │  - devices  │  │  - recordings           │  │  - channels        │       │
│  └─────────────┘  └─────────────────────────┘  └────────────────────┘       │
│                                                                              │
│  ┌─────────────┐  ┌─────────────────────────┐  ┌────────────────────┐       │
│  │   LCRDB     │  │       BillingDB         │  │     Memcached      │       │
│  │  (MySQL)    │  │       (MySQL)           │  │     (Cache)        │       │
│  └─────────────┘  └─────────────────────────┘  └────────────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Repository Structure

```
platform-api/
├── application/
│   ├── config/
│   │   ├── config.php          # Kohana core configuration
│   │   ├── coreapi.php         # Platform-API specific configuration
│   │   ├── database.php        # Database connection settings
│   │   └── routes.php          # URL routing configuration
│   ├── controllers/            # API endpoints (79 controllers)
│   │   ├── auth.php            # Authentication endpoints
│   │   ├── users.php           # User management
│   │   ├── orgs.php            # Organization management
│   │   ├── callcontrol.php     # Call control operations
│   │   ├── dialplan.php        # Dialplan management
│   │   ├── devices.php         # Device management
│   │   └── ... (75+ more)
│   ├── models/                 # Service layer (90 services)
│   │   ├── service.php         # Base service class (114KB)
│   │   ├── authservice.php     # Authentication logic
│   │   ├── userservice.php     # User business logic
│   │   ├── callcontrolservice.php  # Call control logic
│   │   ├── fsdialplanservice.php   # Dialplan generation (179KB)
│   │   └── ... (85+ more)
│   ├── helpers/                # Utility functions
│   └── views/                  # Response templates
├── modules/                    # Kohana modules
├── system/                     # Kohana framework core
├── Dockerfile                  # Container definition
├── docker-compose.yml          # Local development setup
└── README.md
```

## Database Architecture

Platform-API connects to multiple MySQL databases with read/write separation for scalability:

### Database Connections

| Database | Purpose | Read Replica | Write Master |
|----------|---------|--------------|--------------|
| **Org** | Organization, user, device data | ✓ | ✓ |
| **CDR/Big** | Call detail records, call logs | ✓ | ✓ |
| **Freeswitch** | Sofia registrations, channels | ✓ | ✓ |
| **LCR** | Least cost routing tables | ✓ | ✓ |
| **Billing** | Billing and accounting data | ✓ | ✓ |
| **Archiving** | Long-term data storage | ✓ | ✓ |

### Connection Configuration

```php
// From application/config/database.php
$config['org'] = array(
    'type'     => 'MySQL',
    'connection' => array(
        'hostname' => $_SERVER['ORGDB_HOST'],
        'port'     => $_SERVER['ORGDB_PORT'] ?? 3306,
        'socket'   => $_SERVER['ORGDB_SOCKET'] ?? null,
        'database' => $_SERVER['ORGDB_NAME'],
        'username' => $_SERVER['ORGDB_USER'],
        'password' => $_SERVER['ORGDB_PASS'],
    ),
    'table_prefix' => '',
    'charset'      => 'utf8',
);

// Read replicas follow naming convention: {db}_reader
$config['org_reader'] = array(
    'connection' => array(
        'hostname' => $_SERVER['ORGDB_HOST_READER'] ?? $_SERVER['ORGDB_HOST'],
        // ... same structure
    ),
);
```

## Configuration Reference

### Core Configuration (`coreapi.php`)

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `caching` | boolean | Enable memcached caching | `true` |
| `memcached_servers` | array | Memcached server list | `["127.0.0.1:11211"]` |
| `dgapi` | string | Data Gateway API URL | Environment-based |
| `servicegateway` | string | Service Gateway URL | Environment-based |
| `cdrmunch_url` | string | CDR processing service URL | Environment-based |
| `archiving_base_url` | string | Archiving service base URL | Environment-based |
| `freeswitch_servers` | array | FreeSWITCH server configuration | Environment-based |
| `cti_event_servers` | array | CTI event server URLs | Environment-based |
| `google_recaptcha_secret` | string | reCAPTCHA secret key | Environment variable |
| `dialplan_cache_ttl` | integer | Dialplan cache duration (seconds) | `3600` |
| `session_timeout` | integer | Session expiry (seconds) | `3600` |
| `max_login_attempts` | integer | Before account lockout | `5` |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ORGDB_HOST` | Yes | Organization database host |
| `ORGDB_PORT` | No | Database port (default: 3306) |
| `ORGDB_NAME` | Yes | Organization database name |
| `ORGDB_USER` | Yes | Database username |
| `ORGDB_PASS` | Yes | Database password |
| `BIGDB_HOST` | Yes | CDR database host |
| `BIGDB_NAME` | Yes | CDR database name |
| `MEMCACHED_SERVERS` | No | Comma-separated memcached hosts |
| `DGAPI_URL` | Yes | Data Gateway API URL |
| `SERVICE_GATEWAY_URL` | Yes | Service Gateway URL |
| `GOOGLE_RECAPTCHA_SECRET` | No | reCAPTCHA validation key |
| `LOG_LEVEL` | No | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |

## API Endpoints

Platform-API exposes RESTful endpoints through 79 controllers. Key endpoint categories:

### Authentication (`/auth`)

```
POST /auth/login
    Body: { "username": "user@example.com", "password": "..." }
    Response: { "session_id": "...", "user": {...}, "org": {...} }

POST /auth/logout
    Headers: X-Session-ID: <session_id>
    Response: { "success": true }

POST /auth/refresh
    Headers: X-Session-ID: <session_id>
    Response: { "session_id": "...", "expires_at": "..." }

GET /auth/permissions
    Headers: X-Session-ID: <session_id>
    Response: { "permissions": ["view_users", "edit_dialplan", ...] }
```

### Users (`/users`)

```
GET /users
    Query: org_id, status, search, limit, offset
    Response: { "users": [...], "total": 100, "limit": 20, "offset": 0 }

GET /users/{id}
    Response: { "id": 123, "username": "...", "email": "...", ... }

POST /users
    Body: { "username": "...", "email": "...", "org_id": 1, ... }
    Response: { "id": 124, "success": true }

PUT /users/{id}
    Body: { "email": "new@example.com", ... }
    Response: { "success": true }

DELETE /users/{id}
    Response: { "success": true }
```

### Call Control (`/callcontrol`)

```
POST /callcontrol/originate
    Body: {
        "from_user_id": 123,
        "to": "+441onal234567",
        "caller_id": "+441onal987654"
    }
    Response: { "call_uuid": "abc-123-def", "status": "originated" }

POST /callcontrol/transfer
    Body: { "call_uuid": "abc-123-def", "target": "+44700123456" }
    Response: { "success": true }

POST /callcontrol/hangup
    Body: { "call_uuid": "abc-123-def" }
    Response: { "success": true }

GET /callcontrol/active
    Query: org_id
    Response: { "calls": [...] }

POST /callcontrol/hold
    Body: { "call_uuid": "abc-123-def" }
    Response: { "success": true }

POST /callcontrol/unhold
    Body: { "call_uuid": "abc-123-def" }
    Response: { "success": true }

POST /callcontrol/mute
    Body: { "call_uuid": "abc-123-def", "direction": "in|out|both" }
    Response: { "success": true }

POST /callcontrol/dtmf
    Body: { "call_uuid": "abc-123-def", "digits": "1234#" }
    Response: { "success": true }

POST /callcontrol/record
    Body: { "call_uuid": "abc-123-def", "action": "start|stop" }
    Response: { "success": true, "recording_id": "..." }
```

### Organizations (`/orgs`)

```
GET /orgs
    Query: search, status, limit, offset
    Response: { "orgs": [...], "total": 50 }

GET /orgs/{id}
    Response: { "id": 1, "name": "Acme Corp", "domain": "acme.natterbox.com", ... }

POST /orgs
    Body: { "name": "New Org", "domain": "...", "settings": {...} }
    Response: { "id": 51, "success": true }

PUT /orgs/{id}
    Body: { "name": "Updated Name", ... }
    Response: { "success": true }

GET /orgs/{id}/settings
    Response: { "settings": { "voicemail_enabled": true, ... } }

PUT /orgs/{id}/settings
    Body: { "voicemail_enabled": false }
    Response: { "success": true }
```

### Dialplan (`/dialplan`)

```
GET /dialplan/export/{org_id}
    Response: XML dialplan for FreeSWITCH

GET /dialplan/validate/{org_id}
    Response: { "valid": true, "errors": [], "warnings": [] }

POST /dialplan/reload/{org_id}
    Response: { "success": true, "servers_updated": 3 }
```

### Devices (`/devices`)

```
GET /devices
    Query: org_id, user_id, type, status
    Response: { "devices": [...] }

GET /devices/{id}
    Response: { "id": 456, "type": "yealink", "mac": "...", ... }

POST /devices
    Body: { "user_id": 123, "type": "yealink", "mac": "AA:BB:CC:DD:EE:FF" }
    Response: { "id": 457, "success": true }

POST /devices/{id}/provision
    Response: { "config_url": "https://...", "success": true }

GET /devices/{id}/config
    Response: Device-specific provisioning configuration (XML/JSON)
```

## Service Layer Architecture

The service layer (`application/models/`) implements business logic. All services extend the base `Service` class:

### Base Service Class (`service.php`)

```php
class Service {
    // Database connections (with read/write separation)
    protected $db;           // Write master
    protected $db_reader;    // Read replica
    
    // Caching
    protected $cache;        // Memcached instance
    protected $cache_prefix; // Namespace prefix
    
    // Core methods
    public function __construct() {
        $this->db = Database::instance('org');
        $this->db_reader = Database::instance('org_reader');
        $this->cache = Cache::instance();
    }
    
    // Caching helpers
    protected function cache_get($key) {
        return $this->cache->get($this->cache_prefix . $key);
    }
    
    protected function cache_set($key, $value, $ttl = 3600) {
        return $this->cache->set($this->cache_prefix . $key, $value, $ttl);
    }
    
    protected function cache_delete($key) {
        return $this->cache->delete($this->cache_prefix . $key);
    }
}
```

### Key Service Classes

| Service | File Size | Description |
|---------|-----------|-------------|
| `service.php` | 114 KB | Base service with database/cache utilities |
| `fsdialplanservice.php` | 179 KB | FreeSWITCH dialplan generation |
| `fsdirectoryservice.php` | 111 KB | FreeSWITCH directory management |
| `opensipsservice.php` | 111 KB | OpenSIPS integration |
| `mobileservice.php` | 100 KB | Mobile app backend |
| `dataconnectorservice.php` | 100 KB | Data connector integrations |
| `auxservice.php` | 129 KB | Auxiliary/utility functions |
| `baseuserservice.php` | 83 KB | User management base class |
| `xmno.php` | 85 KB | Mobile number operations |
| `callcontrolservice.php` | 74 KB | Call control operations |
| `numberservice.php` | 74 KB | Number management |
| `siptrunkservice.php` | 63 KB | SIP trunk configuration |
| `assetsservice.php` | 64 KB | Asset management |
| `fsdirectservice.php` | 62 KB | Direct FreeSWITCH operations |
| `profileservice.php` | 62 KB | User profile management |

## Authentication & Authorization

### Session-Based Authentication

Platform-API uses session-based authentication with tokens stored in memcached:

```php
// From authservice.php
class AuthService extends Service {
    
    public function login($username, $password) {
        // Validate credentials against database
        $user = $this->validate_credentials($username, $password);
        
        if (!$user) {
            $this->increment_login_attempts($username);
            throw new AuthenticationException('Invalid credentials');
        }
        
        // Generate session token
        $session_id = $this->generate_session_token();
        
        // Store session in memcached
        $session_data = [
            'user_id' => $user['id'],
            'org_id' => $user['org_id'],
            'permissions' => $this->get_user_permissions($user['id']),
            'created_at' => time(),
            'expires_at' => time() + $this->config['session_timeout'],
        ];
        
        $this->cache_set("session:{$session_id}", $session_data, $this->config['session_timeout']);
        
        return [
            'session_id' => $session_id,
            'user' => $user,
            'expires_at' => $session_data['expires_at'],
        ];
    }
    
    public function validate_session($session_id) {
        $session = $this->cache_get("session:{$session_id}");
        
        if (!$session || $session['expires_at'] < time()) {
            return false;
        }
        
        return $session;
    }
}
```

### Permission System

Permissions are role-based with granular access control:

```php
// Permission categories
$permissions = [
    'users' => ['view_users', 'create_users', 'edit_users', 'delete_users'],
    'dialplan' => ['view_dialplan', 'edit_dialplan', 'publish_dialplan'],
    'calls' => ['view_calls', 'control_calls', 'record_calls'],
    'admin' => ['manage_org', 'manage_billing', 'manage_licenses'],
];

// Permission check in controller
class Users_Controller extends CoreAPI_Controller {
    
    public function action_index() {
        $this->require_permission('view_users');
        // ... list users
    }
    
    public function action_create() {
        $this->require_permission('create_users');
        // ... create user
    }
}
```

## Caching Strategy

Platform-API uses memcached extensively for performance:

### Cache Key Patterns

| Pattern | TTL | Description |
|---------|-----|-------------|
| `session:{id}` | 1h | User session data |
| `user:{id}` | 5m | User profile data |
| `org:{id}` | 5m | Organization settings |
| `dialplan:{org_id}` | 1h | Compiled dialplan XML |
| `permissions:{user_id}` | 5m | User permissions |
| `fs_contacts:{org_id}` | 30s | FreeSWITCH contacts |
| `lcr:{prefix}` | 15m | LCR routing data |

### Cache Invalidation

```bash
# Clear all caches for an organization
curl -X POST "https://coreapi.internal/cache/clear" \
  -H "X-Admin-Token: ..." \
  -d '{"org_id": 123}'

# Clear specific cache type
curl -X POST "https://coreapi.internal/cache/clear" \
  -H "X-Admin-Token: ..." \
  -d '{"type": "dialplan", "org_id": 123}'
```

## FreeSWITCH Integration

Platform-API is the primary interface between the Natterbox platform and FreeSWITCH servers:

### Dialplan Generation

The `FSDialplanService` (179KB - largest service) generates XML dialplans dynamically:

```php
class FSDialplanService extends Service {
    
    public function generate_dialplan($org_id) {
        // Check cache first
        $cached = $this->cache_get("dialplan:{$org_id}");
        if ($cached) return $cached;
        
        // Load organization configuration
        $org = $this->load_org_config($org_id);
        
        // Build dialplan XML
        $xml = $this->build_context($org);
        $xml .= $this->build_inbound_extensions($org);
        $xml .= $this->build_outbound_extensions($org);
        $xml .= $this->build_internal_extensions($org);
        
        // Cache and return
        $this->cache_set("dialplan:{$org_id}", $xml, 3600);
        return $xml;
    }
}
```

### Call Control Flow

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Client    │         │ Platform-API │         │ FreeSWITCH  │
│  (Portal)   │         │             │         │   Server    │
└──────┬──────┘         └──────┬──────┘         └──────┬──────┘
       │                       │                       │
       │  POST /callcontrol    │                       │
       │  /originate           │                       │
       │──────────────────────>│                       │
       │                       │                       │
       │                       │  ESL: originate       │
       │                       │  {call_command}       │
       │                       │──────────────────────>│
       │                       │                       │
       │                       │  Call UUID            │
       │                       │<──────────────────────│
       │                       │                       │
       │  { call_uuid: "..." } │                       │
       │<──────────────────────│                       │
       │                       │                       │
       │                       │  CDR Events           │
       │                       │<──────────────────────│
       │                       │  (via event socket)   │
       │                       │                       │
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM redmatter/kohana-app:latest

# Copy application code
COPY application/ /var/www/html/application/
COPY modules/ /var/www/html/modules/

# Set permissions
RUN chown -R www-data:www-data /var/www/html

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost/health || exit 1

EXPOSE 80
```

### Docker Compose (Development)

```yaml
version: '3.8'

services:
  coreapi:
    build: .
    ports:
      - "8080:80"
    environment:
      - ORGDB_HOST=mysql
      - ORGDB_NAME=natterbox_org
      - ORGDB_USER=natterbox
      - ORGDB_PASS=password
      - BIGDB_HOST=mysql
      - BIGDB_NAME=natterbox_cdr
      - MEMCACHED_SERVERS=memcached:11211
    depends_on:
      - mysql
      - memcached
    volumes:
      - ./application:/var/www/html/application

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
    volumes:
      - mysql_data:/var/lib/mysql

  memcached:
    image: memcached:1.6

volumes:
  mysql_data:
```

## Operational Procedures

### Tailing Logs

```bash
# View CoreAPI access logs
kubectl logs -f deployment/coreapi -n production

# Filter for errors
kubectl logs -f deployment/coreapi -n production | grep -i error

# View specific request
kubectl logs deployment/coreapi -n production | grep "request_id=abc123"
```

### Cache Management

```bash
# Connect to memcached and flush all caches
echo "flush_all" | nc memcached.internal 11211

# View cache statistics
echo "stats" | nc memcached.internal 11211

# Delete specific key pattern (requires custom script)
./scripts/clear-cache.sh --pattern "dialplan:*" --org 123
```

### Database Queries

```sql
-- Check active sessions
SELECT COUNT(*) as active_sessions
FROM cache_entries
WHERE cache_key LIKE 'session:%'
  AND expires_at > NOW();

-- Find slow queries
SELECT * FROM mysql.slow_log
WHERE db_name = 'natterbox_org'
ORDER BY query_time DESC
LIMIT 10;

-- Check user activity
SELECT u.username, COUNT(l.id) as login_count, MAX(l.created_at) as last_login
FROM users u
LEFT JOIN login_log l ON u.id = l.user_id
WHERE l.created_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY u.id
ORDER BY login_count DESC;
```

## Troubleshooting

### Common Issues

#### 1. Session Timeout Errors

**Symptom**: Users getting logged out unexpectedly

**Diagnosis**:
```bash
# Check memcached connectivity
echo "stats" | nc memcached.internal 11211

# Check session TTL configuration
grep -r "session_timeout" application/config/
```

**Resolution**:
- Verify memcached is running and accessible
- Check `session_timeout` configuration value
- Ensure clocks are synchronized across servers

#### 2. Dialplan Not Updating

**Symptom**: Changes in portal not reflected in calls

**Diagnosis**:
```bash
# Check dialplan cache
echo "get dialplan:123" | nc memcached.internal 11211

# Force cache refresh
curl -X POST "https://coreapi.internal/dialplan/reload/123" \
  -H "X-Session-ID: ..."
```

**Resolution**:
- Clear dialplan cache for the organization
- Verify FreeSWITCH servers are receiving updates
- Check for validation errors in dialplan

#### 3. Database Connection Failures

**Symptom**: 500 errors with database connection messages

**Diagnosis**:
```bash
# Test database connectivity
mysql -h $ORGDB_HOST -u $ORGDB_USER -p$ORGDB_PASS $ORGDB_NAME -e "SELECT 1"

# Check connection pool
SELECT COUNT(*) FROM information_schema.processlist
WHERE db = 'natterbox_org';
```

**Resolution**:
- Verify database credentials
- Check network connectivity
- Monitor connection pool usage

#### 4. High Memory Usage

**Symptom**: Container OOM kills or slow responses

**Diagnosis**:
```bash
# Check PHP memory usage
curl "https://coreapi.internal/debug/memory" -H "X-Admin-Token: ..."

# View container metrics
kubectl top pod coreapi-xxx -n production
```

**Resolution**:
- Increase container memory limits
- Review caching strategy
- Check for memory leaks in custom code

### Performance Optimization

```php
// Use read replicas for read-heavy operations
$users = $this->db_reader->select('*')
    ->from('users')
    ->where('org_id', '=', $org_id)
    ->execute();

// Batch database operations
$this->db->query(Database::INSERT, 
    "INSERT INTO audit_log (user_id, action, data) VALUES " .
    implode(',', $batch_values)
);

// Use caching for expensive operations
$settings = $this->cache_get("org_settings:{$org_id}");
if (!$settings) {
    $settings = $this->load_org_settings($org_id);
    $this->cache_set("org_settings:{$org_id}", $settings, 300);
}
```

## Migration Strategy (Strangler Pattern)

Platform-API is being gradually decomposed into microservices following the Strangler Fig pattern:

### Already Migrated
- User synchronization → `user-sync-service`
- CDR processing → `cdrmunch`
- Public API → `platform-sapien`
- TTS → `tts-gateway`

### In Progress
- Authentication → `auth-service`
- Number management → `number-service`

### Planned
- Dialplan management
- Device provisioning
- Call control

### Migration Approach

```
┌──────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│  (Routes requests to CoreAPI or new microservices)           │
└──────────────────────────┬───────────────────────────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐   ┌─────────────────┐   ┌────────────────┐
│  CoreAPI    │   │  Auth Service   │   │ Number Service │
│ (Legacy)    │   │  (New)          │   │ (New)          │
└─────────────┘   └─────────────────┘   └────────────────┘
```

## Related Services

| Service | Relationship | Description |
|---------|--------------|-------------|
| [platform-sapien](./platform-sapien.md) | Consumer | Public API that proxies to CoreAPI |
| [cdrmunch](./cdrmunch.md) | Consumer | Processes CDR data from CoreAPI |
| [tts-gateway](./tts-gateway.md) | Consumer | Text-to-speech service |
| [FreeSWITCH](../voice/freeswitch.md) | Integration | Voice processing platform |
| [OpenSIPS](../voice/opensips.md) | Integration | SIP proxy |

## Source References

- **Repository**: https://github.com/redmatter/platform-api
- **Confluence**: 
  - [API Strategy](https://natterbox.atlassian.net/wiki/spaces/NPD/pages/1539604500)
  - [Tailing CoreAPI logs](https://natterbox.atlassian.net/wiki/spaces/EN/pages/713752503)
  - [Clear CoreAPI caches](https://natterbox.atlassian.net/wiki/spaces/EN/pages/713949102)
- **Key Files Reviewed**:
  - `application/config/coreapi.php` - Main configuration
  - `application/config/database.php` - Database connections
  - `application/controllers/callcontrol.php` - Call control endpoints
  - `application/controllers/auth.php` - Authentication endpoints
  - `application/models/service.php` - Base service class
  - `application/models/fsdialplanservice.php` - Dialplan generation
  - `Dockerfile` - Container definition
  - `docker-compose.yml` - Local development setup
