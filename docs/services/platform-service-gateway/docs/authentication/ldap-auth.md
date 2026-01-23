# LDAP Authentication

## Overview

LDAP (Lightweight Directory Access Protocol) authentication enables the Platform Service Gateway to authenticate users against enterprise directory services such as Microsoft Active Directory, OpenLDAP, and other LDAP-compliant directories. This integration is critical for organizations that maintain centralized user management and require single sign-on (SSO) capabilities across their CRM integrations.

The Platform Service Gateway's LDAP implementation supports multiple authentication modes, secure connections via LDAPS and STARTTLS, group-based authorization, and failover configurations for high availability deployments.

## LDAP Server Requirements

### Supported Directory Services

The Platform Service Gateway supports authentication against the following LDAP-compliant directory services:

| Directory Service | Minimum Version | Notes |
|-------------------|-----------------|-------|
| Microsoft Active Directory | Windows Server 2012 R2+ | Full support including nested groups |
| OpenLDAP | 2.4.x+ | Recommended for Linux environments |
| 389 Directory Server | 1.4.x+ | Red Hat/Fedora environments |
| Apache Directory | 2.0.x+ | Java-based LDAP server |
| Oracle Internet Directory | 11g+ | Oracle enterprise environments |

### Network Requirements

Before configuring LDAP authentication, ensure the following network requirements are met:

1. **Port Accessibility**: The gateway server must be able to reach the LDAP server on the configured port:
   - Port 389 (LDAP standard)
   - Port 636 (LDAPS - LDAP over SSL)
   - Port 3268 (Global Catalog - AD)
   - Port 3269 (Global Catalog over SSL - AD)

2. **Firewall Rules**: Ensure bidirectional communication is allowed between the gateway and LDAP servers.

3. **DNS Resolution**: The LDAP server hostname must be resolvable from the gateway server.

4. **Certificate Trust**: For LDAPS connections, the gateway must trust the LDAP server's SSL certificate.

### Service Account Requirements

Create a dedicated service account for the Platform Service Gateway with the following permissions:

```plaintext
# Minimum required permissions for LDAP bind account:
- Read access to user objects (cn, uid, mail, memberOf attributes)
- Read access to group objects (for group-based authorization)
- Search permissions on the configured base DN
- No write permissions required (read-only operations)
```

## Configuration Options

### Environment Variables

Configure LDAP authentication using the following environment variables in your `.env` file or Docker environment:

```bash
# LDAP Connection Settings
LDAP_ENABLED=true
LDAP_HOST=ldap.example.com
LDAP_PORT=389
LDAP_VERSION=3
LDAP_TIMEOUT=10

# Security Settings
LDAP_USE_SSL=false
LDAP_USE_TLS=true
LDAP_VERIFY_CERTIFICATE=true
LDAP_CA_CERT_PATH=/etc/ssl/certs/ldap-ca.crt

# Directory Structure
LDAP_BASE_DN=dc=example,dc=com
LDAP_USER_BASE_DN=ou=Users,dc=example,dc=com
LDAP_GROUP_BASE_DN=ou=Groups,dc=example,dc=com

# Bind Account Credentials
LDAP_BIND_DN=cn=gateway-service,ou=ServiceAccounts,dc=example,dc=com
LDAP_BIND_PASSWORD=your-secure-password

# User Search Settings
LDAP_USER_FILTER=(|(uid=%s)(mail=%s)(sAMAccountName=%s))
LDAP_USER_ATTRIBUTE=uid
LDAP_EMAIL_ATTRIBUTE=mail
LDAP_DISPLAY_NAME_ATTRIBUTE=displayName

# Group Settings
LDAP_GROUP_FILTER=(objectClass=groupOfNames)
LDAP_GROUP_MEMBER_ATTRIBUTE=member
LDAP_REQUIRED_GROUPS=cn=GatewayUsers,ou=Groups,dc=example,dc=com

# Failover Configuration
LDAP_FAILOVER_HOSTS=ldap2.example.com,ldap3.example.com
LDAP_FAILOVER_TIMEOUT=5
```

### PHP Configuration File

For more granular control, configure LDAP settings in `application/config/ldap.php`:

```php
<?php
defined('BASEPATH') OR exit('No direct script access allowed');

$config['ldap'] = [
    // Connection Settings
    'enabled' => env('LDAP_ENABLED', false),
    'hosts' => [
        [
            'hostname' => env('LDAP_HOST', 'localhost'),
            'port' => env('LDAP_PORT', 389),
            'priority' => 1,
        ],
        // Failover hosts with lower priority
        [
            'hostname' => env('LDAP_FAILOVER_HOST_1', ''),
            'port' => env('LDAP_PORT', 389),
            'priority' => 2,
        ],
    ],
    
    // Protocol Settings
    'version' => env('LDAP_VERSION', 3),
    'timeout' => env('LDAP_TIMEOUT', 10),
    'network_timeout' => env('LDAP_NETWORK_TIMEOUT', 5),
    'referrals' => false,
    
    // Security Configuration
    'security' => [
        'use_ssl' => env('LDAP_USE_SSL', false),
        'use_tls' => env('LDAP_USE_TLS', true),
        'verify_certificate' => env('LDAP_VERIFY_CERTIFICATE', true),
        'ca_cert_file' => env('LDAP_CA_CERT_PATH', '/etc/ssl/certs/ca-certificates.crt'),
        'cert_file' => env('LDAP_CLIENT_CERT_PATH', ''),
        'key_file' => env('LDAP_CLIENT_KEY_PATH', ''),
    ],
    
    // Directory Structure
    'base_dn' => env('LDAP_BASE_DN', ''),
    'user_base_dn' => env('LDAP_USER_BASE_DN', ''),
    'group_base_dn' => env('LDAP_GROUP_BASE_DN', ''),
    
    // Authentication
    'bind_dn' => env('LDAP_BIND_DN', ''),
    'bind_password' => env('LDAP_BIND_PASSWORD', ''),
    
    // User Schema Mapping
    'user_schema' => [
        'filter' => env('LDAP_USER_FILTER', '(uid=%s)'),
        'object_class' => 'inetOrgPerson',
        'attributes' => [
            'username' => env('LDAP_USER_ATTRIBUTE', 'uid'),
            'email' => env('LDAP_EMAIL_ATTRIBUTE', 'mail'),
            'display_name' => env('LDAP_DISPLAY_NAME_ATTRIBUTE', 'displayName'),
            'first_name' => 'givenName',
            'last_name' => 'sn',
            'phone' => 'telephoneNumber',
            'department' => 'department',
            'title' => 'title',
        ],
    ],
    
    // Group Schema Mapping
    'group_schema' => [
        'filter' => env('LDAP_GROUP_FILTER', '(objectClass=groupOfNames)'),
        'member_attribute' => env('LDAP_GROUP_MEMBER_ATTRIBUTE', 'member'),
        'name_attribute' => 'cn',
    ],
    
    // Authorization
    'authorization' => [
        'required_groups' => array_filter(explode(',', env('LDAP_REQUIRED_GROUPS', ''))),
        'admin_groups' => array_filter(explode(',', env('LDAP_ADMIN_GROUPS', ''))),
        'check_nested_groups' => true,
    ],
    
    // Cache Settings
    'cache' => [
        'enabled' => true,
        'ttl' => 300, // 5 minutes
        'prefix' => 'ldap_auth_',
    ],
];
```

## Bind Settings

### Anonymous Bind

Anonymous binding is not recommended for production environments but can be useful for testing:

```php
<?php
// Anonymous bind configuration (NOT RECOMMENDED FOR PRODUCTION)
$config['ldap']['bind_dn'] = '';
$config['ldap']['bind_password'] = '';

// Note: Most production LDAP servers disable anonymous binds
// If required, explicitly enable in your LDAP server configuration
```

### Simple Bind (Username/Password)

The most common authentication method using a service account:

```php
<?php
// Simple bind with service account
$ldap_config = [
    'bind_dn' => 'cn=gateway-service,ou=ServiceAccounts,dc=example,dc=com',
    'bind_password' => 'secure-password-from-vault',
];

// For Active Directory, you can also use UPN format
$ldap_config = [
    'bind_dn' => 'gateway-service@example.com',
    'bind_password' => 'secure-password-from-vault',
];
```

### SASL Bind

For environments requiring stronger authentication:

```php
<?php
// SASL DIGEST-MD5 bind configuration
$config['ldap']['sasl'] = [
    'enabled' => true,
    'mechanism' => 'DIGEST-MD5',
    'realm' => 'EXAMPLE.COM',
    'authc_id' => 'gateway-service',
    'authz_id' => '',
    'props' => [],
];
```

### Kerberos/GSSAPI Bind

For Active Directory environments with Kerberos:

```bash
# Configure Kerberos keytab for the service
kinit -k -t /etc/krb5/gateway.keytab gateway-service@EXAMPLE.COM
```

```php
<?php
// GSSAPI bind configuration
$config['ldap']['sasl'] = [
    'enabled' => true,
    'mechanism' => 'GSSAPI',
    'keytab_path' => '/etc/krb5/gateway.keytab',
    'principal' => 'gateway-service@EXAMPLE.COM',
];
```

## Code Examples

### Basic LDAP Authentication

```php
<?php
// application/libraries/Ldap_auth.php

class Ldap_auth {
    
    protected $CI;
    protected $config;
    protected $connection;
    
    public function __construct() {
        $this->CI =& get_instance();
        $this->CI->config->load('ldap');
        $this->config = $this->CI->config->item('ldap');
    }
    
    /**
     * Authenticate user against LDAP directory
     *
     * @param string $username
     * @param string $password
     * @return array|false User data array or false on failure
     */
    public function authenticate($username, $password) {
        if (!$this->config['enabled']) {
            log_message('debug', 'LDAP authentication is disabled');
            return false;
        }
        
        // Sanitize username input
        $username = $this->sanitize_username($username);
        
        if (empty($username) || empty($password)) {
            log_message('error', 'LDAP: Empty username or password provided');
            return false;
        }
        
        try {
            // Establish connection
            $this->connect();
            
            // Bind with service account
            $this->service_bind();
            
            // Search for user
            $user_dn = $this->find_user($username);
            
            if (!$user_dn) {
                log_message('info', "LDAP: User not found: {$username}");
                return false;
            }
            
            // Attempt user bind (verify password)
            if (!$this->user_bind($user_dn, $password)) {
                log_message('info', "LDAP: Invalid password for user: {$username}");
                return false;
            }
            
            // Re-bind as service account for further queries
            $this->service_bind();
            
            // Fetch user attributes
            $user_data = $this->get_user_attributes($user_dn);
            
            // Check group membership if required
            if (!empty($this->config['authorization']['required_groups'])) {
                if (!$this->check_group_membership($user_dn)) {
                    log_message('info', "LDAP: User not in required groups: {$username}");
                    return false;
                }
            }
            
            // Add admin flag if user is in admin groups
            $user_data['is_admin'] = $this->is_admin($user_dn);
            
            log_message('info', "LDAP: Successfully authenticated user: {$username}");
            return $user_data;
            
        } catch (Exception $e) {
            log_message('error', "LDAP authentication error: " . $e->getMessage());
            return false;
        } finally {
            $this->disconnect();
        }
    }
    
    /**
     * Establish connection to LDAP server
     */
    protected function connect() {
        $hosts = $this->config['hosts'];
        usort($hosts, function($a, $b) {
            return $a['priority'] - $b['priority'];
        });
        
        foreach ($hosts as $host) {
            if (empty($host['hostname'])) continue;
            
            $uri = $this->config['security']['use_ssl'] 
                ? "ldaps://{$host['hostname']}:{$host['port']}"
                : "ldap://{$host['hostname']}:{$host['port']}";
            
            $this->connection = ldap_connect($uri);
            
            if ($this->connection) {
                // Set protocol options
                ldap_set_option($this->connection, LDAP_OPT_PROTOCOL_VERSION, $this->config['version']);
                ldap_set_option($this->connection, LDAP_OPT_REFERRALS, $this->config['referrals']);
                ldap_set_option($this->connection, LDAP_OPT_NETWORK_TIMEOUT, $this->config['network_timeout']);
                
                // Start TLS if configured
                if ($this->config['security']['use_tls'] && !$this->config['security']['use_ssl']) {
                    if (!ldap_start_tls($this->connection)) {
                        log_message('error', "LDAP: Failed to start TLS for {$host['hostname']}");
                        ldap_close($this->connection);
                        continue;
                    }
                }
                
                log_message('debug', "LDAP: Connected to {$host['hostname']}");
                return;
            }
        }
        
        throw new Exception('Unable to connect to any LDAP server');
    }
    
    /**
     * Bind with service account credentials
     */
    protected function service_bind() {
        $bind_dn = $this->config['bind_dn'];
        $bind_password = $this->config['bind_password'];
        
        if (!@ldap_bind($this->connection, $bind_dn, $bind_password)) {
            $error = ldap_error($this->connection);
            throw new Exception("Service account bind failed: {$error}");
        }
    }
    
    /**
     * Find user DN by username
     *
     * @param string $username
     * @return string|false User DN or false if not found
     */
    protected function find_user($username) {
        $filter = str_replace('%s', ldap_escape($username, '', LDAP_ESCAPE_FILTER), 
                             $this->config['user_schema']['filter']);
        
        $search = ldap_search(
            $this->connection,
            $this->config['user_base_dn'],
            $filter,
            ['dn'],
            0,
            1
        );
        
        if (!$search) {
            return false;
        }
        
        $entries = ldap_get_entries($this->connection, $search);
        
        if ($entries['count'] === 0) {
            return false;
        }
        
        return $entries[0]['dn'];
    }
    
    /**
     * Attempt to bind as user (password verification)
     *
     * @param string $user_dn
     * @param string $password
     * @return bool
     */
    protected function user_bind($user_dn, $password) {
        return @ldap_bind($this->connection, $user_dn, $password);
    }
    
    /**
     * Get user attributes from directory
     *
     * @param string $user_dn
     * @return array
     */
    protected function get_user_attributes($user_dn) {
        $attributes = array_values($this->config['user_schema']['attributes']);
        
        $search = ldap_read(
            $this->connection,
            $user_dn,
            '(objectClass=*)',
            $attributes
        );
        
        $entries = ldap_get_entries($this->connection, $search);
        
        if ($entries['count'] === 0) {
            return [];
        }
        
        $user_data = ['dn' => $user_dn];
        $entry = $entries[0];
        
        foreach ($this->config['user_schema']['attributes'] as $key => $ldap_attr) {
            $ldap_attr_lower = strtolower($ldap_attr);
            $user_data[$key] = isset($entry[$ldap_attr_lower][0]) 
                ? $entry[$ldap_attr_lower][0] 
                : null;
        }
        
        return $user_data;
    }
    
    /**
     * Check if user is member of required groups
     *
     * @param string $user_dn
     * @return bool
     */
    protected function check_group_membership($user_dn) {
        $required_groups = $this->config['authorization']['required_groups'];
        
        foreach ($required_groups as $group_dn) {
            if ($this->is_member_of($user_dn, $group_dn)) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * Check if user is member of a specific group
     *
     * @param string $user_dn
     * @param string $group_dn
     * @return bool
     */
    protected function is_member_of($user_dn, $group_dn) {
        $member_attr = $this->config['group_schema']['member_attribute'];
        
        // Check direct membership
        $filter = "(&(objectClass=groupOfNames)({$member_attr}={$user_dn}))";
        
        $search = ldap_read(
            $this->connection,
            $group_dn,
            $filter,
            ['dn']
        );
        
        if ($search) {
            $entries = ldap_get_entries($this->connection, $search);
            if ($entries['count'] > 0) {
                return true;
            }
        }
        
        // Check nested groups if enabled
        if ($this->config['authorization']['check_nested_groups']) {
            return $this->check_nested_membership($user_dn, $group_dn);
        }
        
        return false;
    }
    
    /**
     * Sanitize username input
     *
     * @param string $username
     * @return string
     */
    protected function sanitize_username($username) {
        // Remove potentially dangerous characters
        $username = preg_replace('/[^a-zA-Z0-9@._-]/', '', $username);
        return trim($username);
    }
    
    /**
     * Close LDAP connection
     */
    protected function disconnect() {
        if ($this->connection) {
            ldap_close($this->connection);
            $this->connection = null;
        }
    }
}
```

### Using LDAP Authentication in Controllers

```php
<?php
// application/controllers/api/Auth.php

defined('BASEPATH') OR exit('No direct script access allowed');

class Auth extends REST_Controller {
    
    public function __construct() {
        parent::__construct();
        $this->load->library('ldap_auth');
    }
    
    /**
     * POST /api/auth/ldap
     * 
     * Authenticate user via LDAP and return JWT token
     */
    public function ldap_post() {
        $username = $this->post('username');
        $password = $this->post('password');
        
        // Validate input
        if (empty($username) || empty($password)) {
            return $this->response([
                'status' => false,
                'error' => 'Username and password are required'
            ], REST_Controller::HTTP_BAD_REQUEST);
        }
        
        // Attempt LDAP authentication
        $user = $this->ldap_auth->authenticate($username, $password);
        
        if ($user === false) {
            // Log failed attempt for security monitoring
            $this->log_auth_failure($username);
            
            return $this->response([
                'status' => false,
                'error' => 'Invalid credentials'
            ], REST_Controller::HTTP_UNAUTHORIZED);
        }
        
        // Generate JWT token
        $token = $this->generate_jwt_token($user);
        
        // Store session in database for token management
        $this->store_session($user, $token);
        
        return $this->response([
            'status' => true,
            'data' => [
                'token' => $token,
                'user' => [
                    'username' => $user['username'],
                    'email' => $user['email'],
                    'display_name' => $user['display_name'],
                    'is_admin' => $user['is_admin']
                ],
                'expires_at' => time() + 3600
            ]
        ], REST_Controller::HTTP_OK);
    }
    
    /**
     * Generate JWT token for authenticated user
     */
    protected function generate_jwt_token($user) {
        $this->load->library('jwt_helper');
        
        $payload = [
            'sub' => $user['username'],
            'email' => $user['email'],
            'name' => $user['display_name'],
            'admin' => $user['is_admin'],
            'iat' => time(),
            'exp' => time() + 3600,
            'auth_method' => 'ldap'
        ];
        
        return $this->jwt_helper->encode($payload);
    }
}
```

### Docker Configuration for LDAP

```yaml
# docker-compose.yml
version: '3.8'

services:
  platform-gateway:
    build: .
    environment:
      - LDAP_ENABLED=true
      - LDAP_HOST=ldap.example.com
      - LDAP_PORT=636
      - LDAP_USE_SSL=true
      - LDAP_BASE_DN=dc=example,dc=com
      - LDAP_BIND_DN=cn=gateway-service,ou=ServiceAccounts,dc=example,dc=com
      - LDAP_BIND_PASSWORD_FILE=/run/secrets/ldap_password
    secrets:
      - ldap_password
    volumes:
      - ./certs/ldap-ca.crt:/etc/ssl/certs/ldap-ca.crt:ro

secrets:
  ldap_password:
    external: true
```

### Testing LDAP Configuration

```bash
#!/bin/bash
# scripts/test-ldap.sh

# Test LDAP connectivity
echo "Testing LDAP connectivity..."
ldapsearch -x -H ldap://${LDAP_HOST}:${LDAP_PORT} \
  -D "${LDAP_BIND_DN}" \
  -w "${LDAP_BIND_PASSWORD}" \
  -b "${LDAP_BASE_DN}" \
  "(uid=testuser)" dn

# Test with PHP
php -r "
\$conn = ldap_connect('ldap://${LDAP_HOST}:${LDAP_PORT}');
ldap_set_option(\$conn, LDAP_OPT_PROTOCOL_VERSION, 3);
if (@ldap_bind(\$conn, '${LDAP_BIND_DN}', '${LDAP_BIND_PASSWORD}')) {
    echo 'LDAP bind successful\n';
} else {
    echo 'LDAP bind failed: ' . ldap_error(\$conn) . '\n';
}
ldap_close(\$conn);
"
```

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Connection timeout | Network/firewall issues | Verify port accessibility and firewall rules |
| Invalid credentials | Wrong bind DN format | Check DN format matches directory structure |
| Certificate errors | Untrusted CA | Add CA certificate to trusted store |
| User not found | Incorrect search filter | Verify filter syntax and base DN |
| TLS handshake failed | Protocol mismatch | Ensure TLS version compatibility |

### Debug Logging

Enable detailed LDAP logging for troubleshooting:

```php
<?php
// application/config/ldap.php
$config['ldap']['debug'] = [
    'enabled' => env('LDAP_DEBUG', false),
    'log_searches' => true,
    'log_binds' => true,
    'log_level' => 7, // LDAP_DEBUG_ANY
];
```

## Related Documentation

- [OAuth Authentication](./oauth-authentication.md)
- [Token-Based Authentication](./token-authentication.md)
- [GoodData Authentication](./gooddata-authentication.md)
- [API Security Best Practices](./security-best-practices.md)