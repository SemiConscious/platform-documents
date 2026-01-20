# Salt Stack Infrastructure

> **Last Updated**: 2025-01-20
> **Status**: Active
> **Owner**: Platform Team
> **Source**: [salt-stack repository](https://github.com/Natterbox/salt-stack)

## Overview

Salt Stack is Natterbox's infrastructure configuration management and orchestration platform. It manages all server configurations, container deployments, networking, and system state across the entire infrastructure.

### Key Capabilities

- **Configuration Management**: Declarative state files define desired system configurations
- **Container Orchestration**: Manages Docker container lifecycle across all nodes
- **Secrets Management**: Pillar system securely distributes sensitive configuration data
- **Role-Based Targeting**: Nodes are targeted based on custom grains defining their roles
- **Version Management**: Centralized version control for all deployed components
- **External Formulas**: GitFS integration for community and custom formulas

## Architecture

### Master-Minion Topology

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SALT MASTER (OPS Nodes)                           │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │   File Server   │  │  Pillar Server  │  │      External Job Cache     │  │
│  │                 │  │                 │  │                             │  │
│  │  - State Files  │  │  - Secrets      │  │  - PostgreSQL Backend       │  │
│  │  - GitFS        │  │  - Versions     │  │  - Job History              │  │
│  │  - Formulas     │  │  - Node Config  │  │  - Event Storage            │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
│                                                                             │
│  Ports: 4505 (publish), 4506 (return), 8000 (API)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ ZeroMQ
                                    ▼
    ┌───────────────────────────────────────────────────────────────────┐
    │                        SALT MINIONS                                │
    │                                                                    │
    │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
    │  │   CNT   │  │   NTF   │  │   APP   │  │   DKR   │  │   DB    │  │
    │  │ (Media) │  │ (SIP)   │  │ (Apps)  │  │(Docker) │  │ (Data)  │  │
    │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘  │
    │                                                                    │
    │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
    │  │   SBC   │  │   RMQ   │  │   MON   │  │   LOG   │  │   OPS   │  │
    │  │ (SBC)   │  │(Rabbit) │  │(Monitor)│  │(Logging)│  │ (Ops)   │  │
    │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘  │
    └───────────────────────────────────────────────────────────────────┘
```

### Node Role Distribution

| Role | Description | Key Services |
|------|-------------|--------------|
| `cnt` | Media/Container nodes | FreeSWITCH, media processing |
| `ntf` | Notification/SIP nodes | SIP proxies, call routing |
| `app` | Application nodes | Core application services |
| `dkr` | Docker host nodes | Container workloads |
| `db` | Database nodes | PostgreSQL, Redis |
| `sbc` | Session Border Controllers | SIP edge services |
| `rmq` | RabbitMQ nodes | Message queuing |
| `mon` | Monitoring nodes | Prometheus, Grafana |
| `log` | Logging nodes | Elasticsearch, Kibana |
| `ops` | Operations nodes | Salt master, admin tools |

## Directory Structure

The Salt Stack repository follows a standard layout:

```
/var/lib/salt-stack/
├── etc/
│   ├── master                    # Salt master configuration
│   └── minion                    # Salt minion configuration template
├── srv/
│   ├── pillar/                   # Pillar data (secrets, config)
│   │   ├── top.sls              # Pillar targeting
│   │   ├── version.sls          # Component versions
│   │   ├── roles/               # Role-specific pillar data
│   │   └── secrets/             # Encrypted secrets
│   ├── salt/                    # State files
│   │   ├── top.sls             # State targeting
│   │   ├── containers/         # Container state definitions
│   │   ├── roles/              # Role-specific states
│   │   └── _modules/           # Custom execution modules
│   └── reactor/                 # Event reactor configurations
├── formulas/                    # External formula symlinks
└── scripts/                     # Utility scripts
```

## Configuration

### Master Configuration

The Salt master configuration (`etc/master`) defines server behavior:

```yaml
# File Server Configuration
file_roots:
  base:
    - /var/lib/salt-stack/srv/salt

# GitFS Backend for External Formulas
fileserver_backend:
  - roots
  - gitfs

gitfs_remotes:
  - https://github.com/saltstack-formulas/docker-formula.git:
    - base: master
  - https://github.com/saltstack-formulas/ntp-formula.git:
    - base: master
  - https://github.com/saltstack-formulas/resolver-formula.git:
    - base: master
  - https://github.com/saltstack-formulas/salt-formula.git:
    - base: master

gitfs_ssl_verify: True
gitfs_update_interval: 60

# Pillar Configuration
pillar_roots:
  base:
    - /var/lib/salt-stack/srv/pillar

# External Job Cache (PostgreSQL)
master_job_cache: pgjsonb
returner.pgjsonb.host: 'localhost'
returner.pgjsonb.user: 'salt'
returner.pgjsonb.passwd: '${SALT_DB_PASSWORD}'
returner.pgjsonb.db: 'salt'
returner.pgjsonb.port: 5432

# Reactor Configuration
reactor:
  - 'salt/minion/*/start':
    - /var/lib/salt-stack/srv/reactor/minion_start.sls
  - 'salt/auth':
    - /var/lib/salt-stack/srv/reactor/auth.sls

# REST API Configuration
rest_cherrypy:
  port: 8000
  ssl_crt: /etc/pki/tls/certs/localhost.crt
  ssl_key: /etc/pki/tls/private/localhost.key

# Performance Tuning
worker_threads: 5
timeout: 30
gather_job_timeout: 15
```

### Minion Configuration

The minion configuration (`etc/minion`) is deployed to all managed nodes:

```yaml
# Master Connection
master: salt.ops.natterbox.net

# Minion Identity
id: {{ grains['fqdn'] }}

# Custom Grains Module
grains_dirs:
  - /var/lib/salt-stack/srv/salt/_grains

# Startup States
startup_states: highstate

# Logging
log_level: warning
log_level_logfile: info

# Performance
multiprocessing: True
```

## Grains System

### Custom Grains

Custom grains are defined in `srv/salt/_grains/` and provide node metadata:

```python
# srv/salt/_grains/redmatter.py
"""
Custom grains for Natterbox infrastructure.
Determines node roles and environment based on hostname patterns.
"""

import re

def _get_environment():
    """Extract environment from hostname (e.g., prod, staging, dev)."""
    hostname = __grains__['host']
    
    env_patterns = {
        'prod': r'^[a-z]{3}\d+-',      # e.g., cnt01-prod
        'staging': r'-stg\d*$',         # e.g., app01-stg
        'dev': r'-dev\d*$',             # e.g., app01-dev
    }
    
    for env, pattern in env_patterns.items():
        if re.search(pattern, hostname):
            return env
    return 'unknown'

def _get_roles():
    """Determine node roles based on hostname prefix."""
    hostname = __grains__['host']
    prefix = hostname[:3].lower()
    
    role_mapping = {
        'cnt': ['container', 'media', 'freeswitch'],
        'ntf': ['sip', 'notification', 'proxy'],
        'app': ['application', 'api'],
        'dkr': ['docker', 'container-host'],
        'db':  ['database', 'postgresql'],
        'sbc': ['sbc', 'edge'],
        'rmq': ['rabbitmq', 'messaging'],
        'mon': ['monitoring', 'prometheus'],
        'log': ['logging', 'elasticsearch'],
        'ops': ['operations', 'salt-master'],
    }
    
    return role_mapping.get(prefix, ['unknown'])

def main():
    """Return custom grains."""
    return {
        'natterbox': {
            'environment': _get_environment(),
            'roles': _get_roles(),
            'primary_role': _get_roles()[0] if _get_roles() else 'unknown',
            'datacenter': __grains__['host'].split('-')[1] if '-' in __grains__['host'] else 'unknown',
        }
    }
```

### Querying Grains

```bash
# View all custom grains for a minion
salt 'cnt01-prod' grains.item natterbox

# Target by role
salt -G 'natterbox:primary_role:container' test.ping

# Target by environment
salt -G 'natterbox:environment:prod' test.ping
```

## Pillar System

### Pillar Structure

The pillar system provides secure, targeted configuration data:

```
srv/pillar/
├── top.sls                      # Pillar targeting rules
├── version.sls                  # Component version definitions
├── common/
│   ├── init.sls                # Common configuration
│   ├── users.sls               # User accounts
│   └── networking.sls          # Network configuration
├── roles/
│   ├── cnt.sls                 # Container node config
│   ├── ntf.sls                 # Notification node config
│   ├── app.sls                 # Application node config
│   ├── dkr.sls                 # Docker host config
│   ├── db.sls                  # Database node config
│   └── ...
└── secrets/
    ├── init.sls                # Secret references
    ├── database.sls            # Database credentials
    ├── api_keys.sls            # API keys
    └── certificates.sls        # TLS certificates
```

### Pillar Targeting (top.sls)

```yaml
# srv/pillar/top.sls
base:
  # All minions get common pillar data
  '*':
    - common
    - version
    - secrets
  
  # Role-specific pillar data
  'G@natterbox:primary_role:container':
    - roles.cnt
  
  'G@natterbox:primary_role:sip':
    - roles.ntf
  
  'G@natterbox:primary_role:application':
    - roles.app
  
  'G@natterbox:primary_role:docker':
    - roles.dkr
  
  'G@natterbox:primary_role:database':
    - roles.db
  
  # Environment-specific overrides
  'G@natterbox:environment:prod':
    - env.prod
  
  'G@natterbox:environment:staging':
    - env.staging
```

### Version Management (version.sls)

The `version.sls` file centralizes component version control:

```yaml
# srv/pillar/version.sls
versions:
  # Core Services
  freeswitch: '1.10.9'
  kamailio: '5.6.4'
  asterisk: '20.5.0'
  
  # Application Services
  redmatter-core: '2.45.3'
  redmatter-api: '2.45.3'
  redmatter-worker: '2.45.3'
  call-router: '1.23.0'
  
  # Infrastructure
  postgresql: '15.4'
  rabbitmq: '3.12.6'
  redis: '7.2.1'
  elasticsearch: '8.10.2'
  
  # Container Images
  containers:
    nginx: 'nginx:1.25-alpine'
    prometheus: 'prom/prometheus:v2.47.0'
    grafana: 'grafana/grafana:10.1.2'
    alertmanager: 'prom/alertmanager:v0.26.0'
```

## State Files

### State Organization

State files define the desired configuration for each node type:

```
srv/salt/
├── top.sls                     # State targeting
├── base/                       # Base states for all nodes
│   ├── init.sls
│   ├── packages.sls
│   ├── users.sls
│   └── ssh.sls
├── containers/                 # Container definitions
│   ├── freeswitch.sls
│   ├── kamailio.sls
│   ├── redmatter.sls
│   └── monitoring.sls
├── roles/                      # Role-specific states
│   ├── cnt/
│   ├── ntf/
│   ├── app/
│   └── ...
├── networking/                 # Network configuration
│   ├── interfaces.sls
│   ├── firewall.sls
│   └── routing.sls
└── _modules/                   # Custom execution modules
    ├── redmatter_node.py
    ├── redmatter_dict.py
    └── redmatter_rabbitmq.py
```

### State Targeting (top.sls)

```yaml
# srv/salt/top.sls
base:
  # All minions
  '*':
    - base
    - base.packages
    - base.users
    - base.ssh
    - networking
  
  # Container nodes
  'G@natterbox:primary_role:container':
    - roles.cnt
    - containers.freeswitch
    - containers.monitoring
  
  # SIP/Notification nodes  
  'G@natterbox:primary_role:sip':
    - roles.ntf
    - containers.kamailio
    - containers.monitoring
  
  # Application nodes
  'G@natterbox:primary_role:application':
    - roles.app
    - containers.redmatter
    - containers.monitoring
  
  # Docker hosts
  'G@natterbox:primary_role:docker':
    - roles.dkr
    - docker
    - containers.monitoring
  
  # Database nodes
  'G@natterbox:primary_role:database':
    - roles.db
    - postgresql
    - containers.monitoring
```

### Example State File: Container Deployment

```yaml
# srv/salt/containers/redmatter.sls
{% set versions = pillar['versions'] %}
{% set config = pillar['redmatter'] %}

include:
  - docker

# Pull the container image
redmatter-core-image:
  docker_image.present:
    - name: gcr.io/natterbox/redmatter-core:{{ versions['redmatter-core'] }}
    - require:
      - sls: docker

# Deploy configuration file
redmatter-config:
  file.managed:
    - name: /etc/redmatter/config.yaml
    - source: salt://containers/files/redmatter/config.yaml.jinja
    - template: jinja
    - makedirs: True
    - context:
        config: {{ config | json }}

# Run the container
redmatter-core:
  docker_container.running:
    - name: redmatter-core
    - image: gcr.io/natterbox/redmatter-core:{{ versions['redmatter-core'] }}
    - restart_policy: always
    - network_mode: host
    - environment:
        - NODE_ENV: {{ grains['natterbox']['environment'] }}
        - DATABASE_URL: {{ config['database_url'] }}
        - RABBITMQ_URL: {{ config['rabbitmq_url'] }}
    - binds:
        - /etc/redmatter:/etc/redmatter:ro
        - /var/log/redmatter:/var/log/redmatter
    - require:
      - docker_image: redmatter-core-image
      - file: redmatter-config
    - watch:
      - file: redmatter-config
```

### Example State File: User Management

```yaml
# srv/salt/base/users.sls
{% set users = pillar.get('users', {}) %}

# Create admin group
admin-group:
  group.present:
    - name: admin
    - system: True

# Create service accounts
{% for user, config in users.get('service_accounts', {}).items() %}
{{ user }}-user:
  user.present:
    - name: {{ user }}
    - uid: {{ config.get('uid') }}
    - gid: {{ config.get('gid', user) }}
    - home: {{ config.get('home', '/home/' + user) }}
    - shell: {{ config.get('shell', '/bin/bash') }}
    - groups: {{ config.get('groups', []) | json }}
    - require:
      - group: admin-group
{% endfor %}

# Deploy SSH keys for admin users
{% for user, config in users.get('admin_users', {}).items() %}
{{ user }}-ssh-keys:
  ssh_auth.present:
    - user: {{ user }}
    - names: {{ config.get('ssh_keys', []) | json }}
    - require:
      - user: {{ user }}-user
{% endfor %}
```

## Custom Execution Modules

### redmatter_node Module

Custom module for node management operations:

```python
# srv/salt/_modules/redmatter_node.py
"""
Custom Salt execution module for Natterbox node management.
"""

import logging
import requests

log = logging.getLogger(__name__)

__virtualname__ = 'redmatter_node'

def __virtual__():
    return __virtualname__

def drain(timeout=300):
    """
    Drain active calls from a media node before maintenance.
    
    Args:
        timeout: Maximum seconds to wait for calls to complete
        
    Returns:
        dict: Drain status including remaining calls
    """
    node_id = __grains__['id']
    api_url = __pillar__['redmatter']['api_url']
    
    response = requests.post(
        f"{api_url}/nodes/{node_id}/drain",
        json={'timeout': timeout},
        headers={'Authorization': f"Bearer {__pillar__['api_key']}"}
    )
    
    return response.json()

def health_check():
    """
    Perform comprehensive health check on the node.
    
    Returns:
        dict: Health status of all services
    """
    checks = {}
    
    # Check Docker
    docker_status = __salt__['cmd.run']('docker ps -q | wc -l')
    checks['docker_containers'] = int(docker_status)
    
    # Check disk space
    disk = __salt__['disk.usage']('/')
    checks['disk_percent'] = disk['/']['capacity']
    
    # Check memory
    mem = __salt__['status.meminfo']()
    checks['memory_available_mb'] = mem['MemAvailable']['value'] / 1024
    
    # Check service connectivity
    checks['salt_master'] = __salt__['network.connect']('salt.ops.natterbox.net', 4506)
    
    return {
        'node_id': __grains__['id'],
        'healthy': all([
            checks['docker_containers'] > 0,
            int(checks['disk_percent'].rstrip('%')) < 90,
            checks['memory_available_mb'] > 1024,
            checks['salt_master'],
        ]),
        'checks': checks
    }

def register():
    """
    Register node with the Natterbox control plane.
    
    Returns:
        dict: Registration result
    """
    node_info = {
        'node_id': __grains__['id'],
        'roles': __grains__['natterbox']['roles'],
        'environment': __grains__['natterbox']['environment'],
        'ip_addresses': __grains__['ip4_interfaces'],
        'os': __grains__['os'],
        'os_release': __grains__['osrelease'],
    }
    
    api_url = __pillar__['redmatter']['api_url']
    
    response = requests.post(
        f"{api_url}/nodes/register",
        json=node_info,
        headers={'Authorization': f"Bearer {__pillar__['api_key']}"}
    )
    
    return response.json()
```

### redmatter_dict Module

Custom module for distributed dictionary operations:

```python
# srv/salt/_modules/redmatter_dict.py
"""
Custom Salt execution module for distributed dictionary operations.
Used for sharing state across nodes via Redis.
"""

import json
import logging
import redis

log = logging.getLogger(__name__)

__virtualname__ = 'redmatter_dict'

_redis_client = None

def __virtual__():
    return __virtualname__

def _get_redis():
    """Get or create Redis connection."""
    global _redis_client
    if _redis_client is None:
        redis_url = __pillar__['redis']['url']
        _redis_client = redis.from_url(redis_url)
    return _redis_client

def get(key, default=None):
    """Get value from distributed dictionary."""
    r = _get_redis()
    value = r.get(f"salt:dict:{key}")
    if value is None:
        return default
    return json.loads(value)

def set(key, value, ttl=None):
    """Set value in distributed dictionary."""
    r = _get_redis()
    serialized = json.dumps(value)
    if ttl:
        r.setex(f"salt:dict:{key}", ttl, serialized)
    else:
        r.set(f"salt:dict:{key}", serialized)
    return True

def delete(key):
    """Delete key from distributed dictionary."""
    r = _get_redis()
    return r.delete(f"salt:dict:{key}") > 0

def keys(pattern='*'):
    """List keys matching pattern."""
    r = _get_redis()
    return [k.decode().replace('salt:dict:', '') 
            for k in r.keys(f"salt:dict:{pattern}")]
```

## Deployment Procedures

### Release Process

The standard release process for deploying new versions:

```bash
# 1. Update version.sls with new component versions
vim /var/lib/salt-stack/srv/pillar/version.sls

# 2. Commit and push changes
cd /var/lib/salt-stack
git add -A
git commit -m "Release: Update redmatter-core to 2.45.4"
git push origin main

# 3. Refresh pillar data on all minions
salt '*' saltutil.refresh_pillar

# 4. Preview changes (dry run)
salt -G 'natterbox:primary_role:application' state.highstate test=True

# 5. Apply to staging first
salt -G 'natterbox:environment:staging' state.highstate

# 6. Verify staging deployment
salt -G 'natterbox:environment:staging' redmatter_node.health_check

# 7. Rolling production deployment
salt -G 'natterbox:environment:prod' state.highstate --batch-size 10%

# 8. Verify production
salt -G 'natterbox:environment:prod' redmatter_node.health_check
```

### Emergency Rollback

```bash
# 1. Identify previous version
git log --oneline srv/pillar/version.sls

# 2. Revert version.sls
git revert <commit-hash>
git push origin main

# 3. Force immediate rollback
salt '*' saltutil.refresh_pillar
salt -G 'natterbox:environment:prod' state.highstate
```

### Node Maintenance

```bash
# 1. Drain node of active traffic
salt 'cnt01-prod' redmatter_node.drain timeout=600

# 2. Apply maintenance
salt 'cnt01-prod' state.highstate

# 3. Health check
salt 'cnt01-prod' redmatter_node.health_check

# 4. Re-register node to resume traffic
salt 'cnt01-prod' redmatter_node.register
```

## Common Commands

### Status and Monitoring

```bash
# Test connectivity to all minions
salt '*' test.ping

# Check minion versions
salt '*' test.version

# List all accepted minion keys
salt-key -L

# View minion grains
salt 'cnt01-prod' grains.items

# View pillar data for a minion (careful - may contain secrets)
salt 'cnt01-prod' pillar.items

# Check highstate status
salt '*' state.highstate test=True
```

### Targeting

```bash
# By role
salt -G 'natterbox:primary_role:container' test.ping

# By environment
salt -G 'natterbox:environment:prod' test.ping

# Compound targeting
salt -C 'G@natterbox:primary_role:container and G@natterbox:environment:prod' test.ping

# By regex
salt -E 'cnt\d+-prod' test.ping

# List matching minions
salt -G 'natterbox:primary_role:container' --preview-target
```

### State Management

```bash
# Apply highstate
salt '*' state.highstate

# Apply specific state
salt 'cnt01-prod' state.apply containers.freeswitch

# Show what would change
salt '*' state.highstate test=True

# Force state re-application
salt '*' state.apply containers.redmatter force=True
```

### Pillar Operations

```bash
# Refresh pillar data
salt '*' saltutil.refresh_pillar

# View specific pillar key
salt 'cnt01-prod' pillar.get versions:redmatter-core

# Debug pillar targeting
salt 'cnt01-prod' pillar.items --out=json | jq '.versions'
```

### GitFS Management

```bash
# Update GitFS cache
salt-run fileserver.update

# List available formulas
salt-run fileserver.file_list

# Clear GitFS cache
salt-run cache.clear_all
```

## Troubleshooting

### Common Issues

#### Minion Not Responding

```bash
# Check minion service status
ssh cnt01-prod 'systemctl status salt-minion'

# Check minion logs
ssh cnt01-prod 'journalctl -u salt-minion -n 100'

# Restart minion
ssh cnt01-prod 'systemctl restart salt-minion'

# On master, check for minion key
salt-key -L | grep cnt01-prod
```

#### State Apply Failures

```bash
# Run with debug output
salt 'cnt01-prod' state.highstate -l debug

# Check for pillar errors
salt 'cnt01-prod' pillar.items 2>&1 | grep -i error

# Test individual state
salt 'cnt01-prod' state.single docker_container.running name=redmatter-core test=True
```

#### GitFS Not Updating

```bash
# Check GitFS status
salt-run fileserver.update backend=gitfs

# View GitFS errors
tail -f /var/log/salt/master | grep -i gitfs

# Clear and rebuild cache
salt-run cache.clear_git_lock gitfs type=update
salt-run fileserver.update
```

#### Pillar Data Missing

```bash
# Check pillar compilation
salt 'cnt01-prod' pillar.items --out=json 2>&1

# Verify top.sls targeting
salt 'cnt01-prod' pillar.show_top

# Check for pillar render errors
salt-run pillar.show_pillar cnt01-prod
```

### Log Locations

| Component | Log Location |
|-----------|--------------|
| Salt Master | `/var/log/salt/master` |
| Salt Minion | `/var/log/salt/minion` |
| Salt API | `/var/log/salt/api` |
| Job Returns | PostgreSQL `salt` database |

### Health Check Script

```bash
#!/bin/bash
# /var/lib/salt-stack/scripts/health_check.sh

echo "=== Salt Infrastructure Health Check ==="

# Check master status
echo -n "Master service: "
systemctl is-active salt-master

# Check API status  
echo -n "API service: "
systemctl is-active salt-api

# Count connected minions
echo -n "Connected minions: "
salt '*' test.ping --timeout=5 --out=json 2>/dev/null | jq 'to_entries | map(select(.value == true)) | length'

# Check GitFS
echo -n "GitFS status: "
salt-run fileserver.update backend=gitfs 2>&1 | grep -q "True" && echo "OK" || echo "FAILED"

# Check job cache DB
echo -n "Job cache DB: "
psql -h localhost -U salt -d salt -c "SELECT 1" >/dev/null 2>&1 && echo "OK" || echo "FAILED"

echo "=== End Health Check ==="
```

## Security Considerations

### Key Management

- Salt uses AES encryption for master-minion communication
- Minion keys must be explicitly accepted by the master
- Key directory: `/etc/salt/pki/master/`

```bash
# View pending keys
salt-key -L

# Accept specific key
salt-key -a cnt01-prod

# Reject key
salt-key -r suspicious-minion

# Delete key
salt-key -d old-minion
```

### Pillar Security

- Pillar data is encrypted in transit
- Secrets should use Salt's GPG encryption or external secret management
- Use `pillar.get` with defaults to avoid exposing missing keys

```yaml
# Secure pillar reference with default
{% set db_password = salt['pillar.get']('database:password', 'MISSING_SECRET') %}
{% if db_password == 'MISSING_SECRET' %}
{{ raise('Database password not found in pillar!') }}
{% endif %}
```

### Network Security

- Ports 4505/4506 should be firewalled to only allow minion IPs
- Use TLS for the REST API (port 8000)
- Consider using Salt SSH for sensitive operations

## Integration Points

### External Systems

| System | Integration Method | Purpose |
|--------|-------------------|---------|
| PostgreSQL | External Job Cache | Job history and event storage |
| Redis | Custom modules | Distributed state sharing |
| Prometheus | Node exporter state | Metrics collection |
| Consul | Service discovery | Dynamic targeting |
| GitLab/GitHub | GitFS backend | External formula management |

### API Usage

The Salt REST API enables external automation:

```bash
# Authenticate and get token
curl -X POST https://salt-master:8000/login \
  -d username=admin \
  -d password=SECRET \
  -d eauth=pam

# Execute command
curl -X POST https://salt-master:8000 \
  -H "X-Auth-Token: <token>" \
  -d client=local \
  -d tgt='cnt*' \
  -d fun='test.ping'
```

## References

- **Source Repository**: [Natterbox/salt-stack](https://github.com/Natterbox/salt-stack)
- **Confluence**: [Salt Deployment](https://natterbox.atlassian.net/wiki/spaces/EN/pages/4947989/Deploying+Salt)
- **Confluence**: [Grains and Pillars](https://natterbox.atlassian.net/wiki/spaces/EN/pages/2805137506/Salt+Grains+Pillars)
- **Salt Documentation**: [docs.saltproject.io](https://docs.saltproject.io/)
