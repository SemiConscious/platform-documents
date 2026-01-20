# Guardian - RPM Package Management System

**Last Updated:** 2026-01-20  
**Repository:** `redmatter/infrastructure-guardian`  
**Status:** Legacy (Active for DEV→QA promotion only)  
**Technology:** PHP (Kohana Framework)

---

## Overview

Guardian is a web-based **RPM package management and promotion system** that controls the movement of software packages through the release pipeline. It provides a user interface for pushing packages between repository branches (DEV → QA → STAGE → PROD) while enforcing access controls via LDAP authentication.

### Current Role

Guardian currently handles **DEV to QA package promotions only**. Promotions from QA to STAGE and STAGE to PROD are now managed through the newer `infrastructure-versions` repository using GitHub Actions workflows and SaltStack deployment.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RELEASE PIPELINE OVERVIEW                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   BUILD         DEV            QA           STAGE          PROD             │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━            │
│                                                                             │
│   Jenkins  ───────►  DEV Repo ───────►  QA Repo ───────►  STAGE ───────►  PROD
│   (CI/CD)         (auto-deploy)        (Guardian)     (infra-versions)      │
│                                                                             │
│   ┌─────────┐     ┌─────────┐        ┌─────────┐     ┌──────────────────┐   │
│   │ RPM     │     │ buildbot│        │Guardian │     │ GitHub Actions   │   │
│   │ Build   │────►│ rsync   │───────►│ Web UI  │────►│ infrastructure-  │   │
│   │ Server  │     │ to DEV  │        │         │     │ versions repo    │   │
│   └─────────┘     └─────────┘        └─────────┘     └──────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Architecture

### System Components

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           GUARDIAN ARCHITECTURE                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────┐         ┌─────────────────────────────────────────────┐  │
│  │   Browser   │         │              Guardian Server                 │  │
│  │  (Engineer) │         │              (relay.redmatter.com)           │  │
│  └──────┬──────┘         │                                             │  │
│         │                │  ┌─────────────────────────────────────────┐│  │
│         │ HTTPS          │  │           Apache + mod_php              ││  │
│         │                │  │                                         ││  │
│         ▼                │  │  ┌───────────────────────────────────┐  ││  │
│  ┌─────────────┐         │  │  │     Kohana PHP Framework         │  ││  │
│  │    LDAP     │◄────────┤  │  │                                   │  ││  │
│  │   Server    │         │  │  │  ┌───────────┐  ┌─────────────┐  │  ││  │
│  │ (redmatter) │         │  │  │  │Controllers│  │   Models    │  │  ││  │
│  └─────────────┘         │  │  │  │           │  │             │  │  ││  │
│                          │  │  │  │-guardian  │  │-guardian    │  │  ││  │
│                          │  │  │  │-rpm       │  │-rpm         │  │  ││  │
│                          │  │  │  │-rri       │  │-rri         │  │  ││  │
│                          │  │  │  └───────────┘  └─────────────┘  │  ││  │
│                          │  │  └───────────────────────────────────┘  ││  │
│                          │  └─────────────────────────────────────────┘│  │
│                          │                       │                     │  │
│                          │                       ▼                     │  │
│                          │  ┌─────────────────────────────────────────┐│  │
│                          │  │         YUM Repository Storage          ││  │
│                          │  │         /home/builduser/repo/           ││  │
│                          │  │                                         ││  │
│                          │  │   5/                    7/              ││  │
│                          │  │   ├── dev/              ├── dev/        ││  │
│                          │  │   │   ├── noarch/       │   ├── noarch/ ││  │
│                          │  │   │   └── x86_64/       │   └── x86_64/ ││  │
│                          │  │   ├── qa/               ├── qa/         ││  │
│                          │  │   ├── stage/            ├── stage/      ││  │
│                          │  │   └── prod/             └── prod/       ││  │
│                          │  └─────────────────────────────────────────┘│  │
│                          └─────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Repository Structure

```
infrastructure-guardian/
├── RM-guardian.spec           # RPM package specification
├── apache.conf                # Apache virtual host configuration
├── rsyslog.conf               # Syslog configuration for audit logging
├── logrotate.conf             # Log rotation settings
│
├── application/               # Kohana application
│   ├── config/
│   │   ├── guardian.php       # Main configuration (branches, LDAP, paths)
│   │   └── routes.php         # URL routing
│   │
│   ├── controllers/
│   │   ├── guardian.php       # Main package management controller
│   │   ├── rpm.php            # RPM package sync controller
│   │   └── rri.php            # Red Matter Release Info controller
│   │
│   ├── models/
│   │   ├── guardian.php       # Package operations (move, list, jobs)
│   │   ├── rpm.php            # RPM sync from external repos
│   │   └── rri.php            # RRI version parsing
│   │
│   ├── views/
│   │   ├── header.php         # Page header with navigation
│   │   ├── footer.php         # Page footer
│   │   ├── packagelist.php    # Package listing view
│   │   ├── confirm.php        # Move confirmation view
│   │   └── rri.php            # RRI information display
│   │
│   ├── libraries/
│   │   └── LDAPHelper.php     # LDAP authentication helper
│   │
│   └── jobs/                  # Job log directory
│
└── js/
    └── guardian.js            # Client-side JavaScript
```

---

## Configuration Reference

### Main Configuration (`application/config/guardian.php`)

```php
<?php
// LDAP Authentication Configuration
$config['ldapconfig'] = array(
    'server' => 'ldap://ldap.redmatter.com:389',
    'base' => 'ou=group,dc=redmatter,dc=com',
    'protocol_version' => 3,
);

// Repository Paths
$config['repopath'] = '/home/builduser/repo';           // Base repository path
$config['refreshpath'] = '/home/builduser/.repo/refresh'; // Refresh marker path
$config['jobdir'] = APPPATH.'jobs/';                   // Job log directory

// Architecture Configuration
$config['archlist'] = array("noarch", "x86_64");       // Supported architectures
$config['centosver'] = array("5", "7");                // Supported CentOS versions

// Commands for Package Operations
$config['mvcommand']['default'] = "/usr/bin/sudo -u builduser /bin/mv %src% %dst% 2>&1";
$config['mvcommand']['dev-bin'] = "/usr/bin/sudo -u builduser /bin/rm -f %src% 2>&1";
$config['mvcommand']['prod-bin'] = "/usr/bin/sudo -u builduser /bin/rm -f %src% 2>&1";

// Repository Regeneration Command
$config['crcommand'] = "/usr/bin/sudo -H -u builduser /usr/bin/repo-refresh 2>&1";

// Virtual Branches (don't run createrepo)
$config['virtbranch'] = array('bin');

// Branch Configuration (defines allowed moves)
// Format: 'branch' => array('lower_branch', 'upper_branch')
// Empty string means no link in that direction

// Default branches (minimal)
$config['branches'] = array(
    'dev' => array('', ''),
    'qa' => array('', ''),
    'stage' => array('', ''),
    'prod' => array('', ''),
);

// Extended branch configurations for different environments
$config['branches_qa'] = array(
    'dev' => array('bin', 'qa'),    // bin <- dev -> qa
    'qa' => array('dev', ''),       // dev <- qa -> (none)
    'stage' => array('', ''),
    'prod' => array('', ''),
);

$config['branches_stage'] = array(
    'dev' => array('bin', 'qa'),
    'qa' => array('dev', 'stage'),  // dev <- qa -> stage
    'stage' => array('qa', ''),     // qa <- stage -> (none)
    'prod' => array('', ''),
);

$config['branches_prod'] = array(
    'dev' => array('bin', 'qa'),
    'qa' => array('dev', 'stage'),
    'stage' => array('qa', 'prod'), // qa <- stage -> prod
    'prod' => array('stage', 'bin'), // stage <- prod -> bin (cleanup)
);

// Hide packages that exist in target branch
$config['hidecopies'] = array();
```

### Configuration Options Explained

| Option | Type | Description |
|--------|------|-------------|
| `ldapconfig.server` | string | LDAP server URL for authentication |
| `ldapconfig.base` | string | LDAP search base DN |
| `repopath` | string | Base path to YUM repository directory |
| `refreshpath` | string | Path to refresh marker file |
| `archlist` | array | List of supported CPU architectures |
| `centosver` | array | List of supported CentOS/RHEL versions |
| `mvcommand.default` | string | Default shell command for moving packages |
| `mvcommand.<src>-<dst>` | string | Override command for specific branch transitions |
| `crcommand` | string | Command to regenerate repository metadata |
| `branches` | array | Branch configuration defining allowed promotions |
| `virtbranch` | array | Virtual branches that don't need createrepo |
| `hidecopies` | array | Branches to hide duplicates from |
| `jobdir` | string | Directory for job log files |

---

## Controllers and API Endpoints

### Guardian Controller (`application/controllers/guardian.php`)

The main controller handling package listing and promotion operations.

```
URL Routes:
  GET  /guardian/               → index()      # Package listing UI
  POST /guardian/move/          → move()       # Initiate package move
  POST /guardian/confirm/       # Confirm and execute move
```

**Key Methods:**

```php
class Guardian_Controller extends Controller
{
    /**
     * Display package listing
     * Shows all packages in each branch with checkboxes for selection
     */
    public function index()
    {
        $packages = $this->guardian->GetPackageList();
        // Renders packagelist.php view with checkboxes for each package
    }
    
    /**
     * Process move request
     * Validates selected packages and branch transition
     * Either shows confirmation or executes move based on 'confirmed' param
     */
    public function move()
    {
        // Parses POST data: srcbranch, dstbranch, pkgs[], confirmed
        // If not confirmed: shows confirm.php view
        // If confirmed: executes move via Guardian_Model::Change()
    }
}
```

### RPM Controller (`application/controllers/rpm.php`)

Handles synchronization of RPM packages from external servers via rsync.

```
URL Routes:
  GET /rpm/                     → index()      # RPM sync UI
  POST /rpm/sync/               → sync()       # Execute rsync operation
```

**Key Methods:**

```php
class Rpm_Controller extends Controller
{
    /**
     * Display sync UI
     * Shows available servers and packages to sync
     */
    public function index()
    {
        // Lists packages available for rsync from external servers
    }
    
    /**
     * Execute rsync
     * Syncs selected packages from source to destination
     */
    public function sync()
    {
        // Runs: rsync -avz --progress <src> <dst>
    }
}
```

### RRI Controller (`application/controllers/rri.php`)

Displays Red Matter Release Information (software version tracking).

```
URL Routes:
  GET /rri/                     → index()      # Version information UI
```

---

## Models and Business Logic

### Guardian Model (`application/models/guardian.php`)

Core business logic for package management operations.

```php
class Guardian_Model extends Model
{
    /**
     * Get list of all packages organized by branch and architecture
     * 
     * @return array Multi-dimensional array:
     *               [branch][arch][] = package filenames
     *               [branch]['_moves'] = allowed destination branches
     */
    public function GetPackageList()
    {
        $packagelist = array();
        
        foreach (Kohana::config('guardian.branches') as $branch => $moves) {
            foreach (Kohana::config('guardian.archlist') as $arch) {
                foreach (Kohana::config('guardian.centosver') as $cver) {
                    // Scan directory: /home/builduser/repo/{cver}/{branch}/{arch}/
                    $repo = Kohana::config('guardian.repopath')."/{$cver}/{$branch}/{$arch}";
                    // Read all *.rpm files
                }
            }
            $packagelist[$branch]['_moves'] = $moves;
        }
        
        // Apply hidecopies filter to remove duplicates
        return $packagelist;
    }
    
    /**
     * Move packages between branches
     *
     * @param string $srcbranch  Source branch (e.g., 'dev')
     * @param string $dstbranch  Destination branch (e.g., 'qa')
     * @param string $confirmed  'true' to execute, 'false' for confirmation view
     * @param array  $pkgs       Packages to move: [arch][] = package names
     */
    public function Change($srcbranch, $dstbranch, $confirmed, $pkgs)
    {
        // Validate branch transition is allowed
        if (!in_array($dstbranch, $branches[$srcbranch])) {
            throw new Exception("Bad move: {$srcbranch} -> {$dstbranch}");
        }
        
        if ($confirmed === 'true') {
            $this->_ClearJobs();  // Clean up old job files
            
            foreach ($pkgs as $arch => $packages) {
                foreach ($packages as $package) {
                    // Log the action
                    LogMessage("{$user} pushed {$arch} {$package} from {$srcbranch} to {$dstbranch}");
                    
                    // Execute move command
                    // /usr/bin/sudo -u builduser /bin/mv <src> <dst>
                    $this->_RunCommand($cmd);
                }
            }
            
            // Regenerate repository metadata
            // /usr/bin/sudo -H -u builduser /usr/bin/repo-refresh
            $this->_RunCommand($crcommand);
            
            // Log job for audit
            $this->_LogJob($jobs);
        }
        
        return $confirmlist;
    }
    
    /**
     * Execute shell command with error handling
     */
    private function _RunCommand($cmd)
    {
        LogDebug("COMMAND: {$cmd}");
        exec($cmd, $output, $ret);
        if ($ret != 0) {
            throw new Exception("Command failed: {$cmd}");
        }
    }
    
    /**
     * Log job to file for audit trail
     * Creates file: {jobdir}/{timestamp}_{uuid}.job
     */
    private function _LogJob($jobs)
    {
        $jobfile = Kohana::config('guardian.jobdir') . time() . '_' . $this->_UUID_v4() . '.job';
        file_put_contents($jobfile, $jobs);
    }
    
    /**
     * Clean up job files older than 24 hours
     */
    private function _ClearJobs()
    {
        // Removes *.job files older than 86400 seconds
    }
}
```

### RPM Model (`application/models/rpm.php`)

Handles RPM package synchronization from external sources.

```php
class Rpm_Model extends Model
{
    /**
     * Get list of packages available for sync
     */
    public function GetSyncList()
    {
        // Scans external repository paths
        // Returns available packages for rsync
    }
    
    /**
     * Execute rsync to pull packages
     */
    public function Sync($packages)
    {
        // Runs: rsync -avz --progress {source} {destination}
    }
}
```

### RRI Model (`application/models/rri.php`)

Parses and displays version information from RRI files.

```php
class RRI_Model extends Model
{
    /**
     * Get release information
     * Parses /etc/redmatter/rmht-release.rri format files
     */
    public function GetReleaseInfo()
    {
        // Returns structured version data
    }
}
```

---

## LDAP Authentication

Guardian uses LDAP for authentication and authorization.

### LDAPHelper Library (`application/libraries/LDAPHelper.php`)

```php
class LDAPHelper
{
    private $conn;
    private $config;
    
    public function __construct()
    {
        $this->config = Kohana::config('guardian.ldapconfig');
    }
    
    /**
     * Authenticate user against LDAP
     *
     * @param string $username LDAP username
     * @param string $password User password
     * @return bool True if authentication successful
     */
    public function authenticate($username, $password)
    {
        $this->conn = ldap_connect($this->config['server']);
        ldap_set_option($this->conn, LDAP_OPT_PROTOCOL_VERSION, $this->config['protocol_version']);
        
        $dn = "uid={$username}," . $this->config['base'];
        return @ldap_bind($this->conn, $dn, $password);
    }
    
    /**
     * Check user group membership for authorization
     */
    public function isMemberOf($username, $group)
    {
        // Searches LDAP for group membership
    }
}
```

---

## Web Interface

### Package List View (`application/views/packagelist.php`)

The main UI displays packages in a table organized by branch and architecture.

```
┌───────────────────────────────────────────────────────────────────────────┐
│  Guardian - Package Management                    [user@redmatter.com]    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Branch: DEV                                                   [→ QA]    │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ ☑ noarch │ RM-sbc-3.1.0-1.el7.noarch.rpm                           │ │
│  │ ☑ noarch │ RM-platform-api-2.5.1-1.el7.noarch.rpm                  │ │
│  │ ☐ x86_64 │ RM-freeswitch-1.10.9-1.el7.x86_64.rpm                   │ │
│  │ ☐ x86_64 │ RM-asterisk-18.15.0-1.el7.x86_64.rpm                    │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  Branch: QA                                                    [→ STAGE]  │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ ☐ noarch │ RM-sbc-3.0.0-1.el7.noarch.rpm                           │ │
│  │ ☐ noarch │ RM-platform-api-2.5.0-1.el7.noarch.rpm                  │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│                                           [ Push Selected Packages ]      │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

**Features:**
- Checkbox selection for multiple packages
- Visual separation by branch and architecture
- Push button initiates confirmation flow
- Packages hidden if already in destination (hidecopies config)

### Confirmation View (`application/views/confirm.php`)

Displays packages to be moved before execution.

```
┌───────────────────────────────────────────────────────────────────────────┐
│  Confirm Package Move                                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Moving packages from DEV to QA:                                          │
│                                                                           │
│  • RM-sbc-3.1.0-1.el7.noarch.rpm                                         │
│  • RM-platform-api-2.5.1-1.el7.noarch.rpm                                │
│                                                                           │
│                          [ Cancel ]  [ Confirm Move ]                     │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Client-Side JavaScript (`js/guardian.js`)

```javascript
// Package selection and form handling
$(document).ready(function() {
    // Select all packages in a branch
    $('.select-all').click(function() {
        var branch = $(this).data('branch');
        $('input[name="pkgs[' + branch + '][]"]').prop('checked', true);
    });
    
    // Clear all selections
    $('.clear-all').click(function() {
        $('input[type="checkbox"]').prop('checked', false);
    });
    
    // Form submission with validation
    $('form#package-form').submit(function(e) {
        var selected = $('input[name^="pkgs"]:checked').length;
        if (selected === 0) {
            alert('Please select at least one package');
            e.preventDefault();
            return false;
        }
        
        if (!confirm('Move ' + selected + ' package(s)?')) {
            e.preventDefault();
            return false;
        }
    });
});
```

---

## Apache Configuration

### Virtual Host Configuration (`apache.conf`)

```apache
<VirtualHost *:80>
    ServerName guardian.redmatter.com
    ServerAlias relay.redmatter.com
    
    DocumentRoot /var/www/guardian
    
    <Directory /var/www/guardian>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    
    # Kohana URL rewriting
    <IfModule mod_rewrite.c>
        RewriteEngine On
        RewriteBase /
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule ^(.*)$ index.php/$1 [L,QSA]
    </IfModule>
    
    # LDAP Authentication
    <Location />
        AuthType Basic
        AuthName "Guardian - LDAP Authentication"
        AuthBasicProvider ldap
        AuthLDAPURL "ldap://ldap.redmatter.com:389/ou=people,dc=redmatter,dc=com?uid"
        AuthLDAPBindDN "cn=admin,dc=redmatter,dc=com"
        AuthLDAPBindPassword "REDACTED"
        Require valid-user
    </Location>
    
    ErrorLog /var/log/httpd/guardian-error.log
    CustomLog /var/log/httpd/guardian-access.log combined
</VirtualHost>
```

---

## Logging and Audit

### Syslog Configuration (`rsyslog.conf`)

```
# Guardian application logging
local6.*    /var/log/guardian/guardian.log

# Format with timestamp and user
$template GuardianFormat,"%timegenerated% %syslogtag%%msg%\n"
local6.*    /var/log/guardian/guardian.log;GuardianFormat
```

### Log Rotation (`logrotate.conf`)

```
/var/log/guardian/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 apache apache
    sharedscripts
    postrotate
        /bin/systemctl reload rsyslog > /dev/null 2>&1 || true
    endscript
}
```

### Audit Trail

Guardian maintains audit logs for all package movements:

1. **Syslog messages**: Every package move is logged with username and timestamp
2. **Job files**: Each operation creates a `.job` file in `application/jobs/`
3. **Apache access logs**: All web requests are logged

Example log entry:
```
2026-01-20 14:35:22 john.smith pushed noarch RM-sbc-3.1.0-1.el7.noarch.rpm from DEV to QA
```

---

## RPM Package Specification

### Package Build (`RM-guardian.spec`)

```spec
Name:           RM-guardian
Version:        1.0.0
Release:        1%{?dist}
Summary:        Guardian RPM Package Management System
License:        Proprietary
Group:          Applications/Internet

Requires:       httpd >= 2.4
Requires:       php >= 7.0
Requires:       php-ldap
Requires:       mod_ssl
Requires:       createrepo

%description
Web-based RPM package management and promotion system for
managing software releases across DEV, QA, STAGE, and PROD environments.

%install
mkdir -p %{buildroot}/var/www/guardian
cp -r application %{buildroot}/var/www/guardian/
cp -r js %{buildroot}/var/www/guardian/
cp index.php %{buildroot}/var/www/guardian/

mkdir -p %{buildroot}/etc/httpd/conf.d
cp apache.conf %{buildroot}/etc/httpd/conf.d/guardian.conf

mkdir -p %{buildroot}/etc/rsyslog.d
cp rsyslog.conf %{buildroot}/etc/rsyslog.d/guardian.conf

mkdir -p %{buildroot}/etc/logrotate.d
cp logrotate.conf %{buildroot}/etc/logrotate.d/guardian

%post
# Create job directory
mkdir -p /var/www/guardian/application/jobs
chown apache:apache /var/www/guardian/application/jobs

# Restart services
systemctl restart httpd
systemctl restart rsyslog

%files
/var/www/guardian
/etc/httpd/conf.d/guardian.conf
/etc/rsyslog.d/guardian.conf
/etc/logrotate.d/guardian
```

---

## Deployment

### Where Guardian Runs

Guardian is deployed on the **relay server** (relay.redmatter.com) which acts as the central package repository server.

```
┌─────────────────────────────────────────────────────────────────┐
│                    relay.redmatter.com                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐     ┌───────────────────────────────────┐ │
│  │  Guardian App   │     │   YUM Repository                  │ │
│  │  (/var/www/     │────►│   /home/builduser/repo/           │ │
│  │   guardian/)    │     │                                   │ │
│  └─────────────────┘     │   5/                              │ │
│                          │   ├── dev/                        │ │
│                          │   ├── qa/                         │ │
│                          │   ├── stage/                      │ │
│                          │   └── prod/                       │ │
│                          │   7/                              │ │
│                          │   ├── dev/                        │ │
│                          │   ├── qa/                         │ │
│                          │   ├── stage/                      │ │
│                          │   └── prod/                       │ │
│                          └───────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Installation Steps

1. **Build RPM package:**
   ```bash
   rpmbuild -ba RM-guardian.spec
   ```

2. **Install dependencies:**
   ```bash
   yum install httpd php php-ldap mod_ssl createrepo
   ```

3. **Install Guardian:**
   ```bash
   rpm -ivh RM-guardian-1.0.0-1.el7.noarch.rpm
   ```

4. **Configure LDAP:**
   Edit `/var/www/guardian/application/config/guardian.php` with correct LDAP settings

5. **Set up builduser:**
   ```bash
   useradd -m builduser
   mkdir -p /home/builduser/repo/{5,7}/{dev,qa,stage,prod}/{noarch,x86_64}
   chown -R builduser:builduser /home/builduser/repo
   ```

6. **Configure sudo:**
   ```bash
   # /etc/sudoers.d/guardian
   apache ALL=(builduser) NOPASSWD: /bin/mv, /bin/rm, /usr/bin/repo-refresh
   ```

7. **Start services:**
   ```bash
   systemctl enable --now httpd
   systemctl restart rsyslog
   ```

---

## Integration with Modern Release Pipeline

### Transition Overview

Guardian's role has been reduced over time as the release pipeline modernized:

| Stage | Legacy (Guardian) | Modern (infra-versions) |
|-------|-------------------|-------------------------|
| DEV → QA | ✅ Still uses Guardian | - |
| QA → STAGE | ❌ Deprecated | GitHub Actions + SaltStack |
| STAGE → PROD | ❌ Deprecated | GitHub Actions + SaltStack |

### Modern Pipeline (infrastructure-versions)

The `infrastructure-versions` repository now handles most promotions:

1. **Version Files**: Branch-specific YAML files define target versions
2. **GitHub Actions**: Workflows triggered on version file changes
3. **SaltStack**: State files apply version changes to servers

Example workflow (`manual-run.yml`):
```yaml
name: Manual Deployment
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        type: choice
        options:
          - qa
          - stage
          - prod

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger SaltStack deployment
        run: |
          # Calls SaltStack API to apply state
          curl -X POST https://salt-api.redmatter.com/run \
            -d 'client=local' \
            -d "tgt=G@environment:${{ inputs.environment }}" \
            -d 'fun=state.apply' \
            -d 'arg=versions'
```

### QA Deployment Workflow

From Confluence documentation, the current QA deployment process:

1. **Package Build**: Jenkins builds RPM and pushes to DEV repo
2. **DEV to QA Push**: Use Guardian to select and push packages
3. **Announce**: Post to #deployments Slack channel
4. **Deploy**: Run SaltStack highstate or targeted state

---

## Troubleshooting

### Common Issues

#### 1. LDAP Authentication Failure

**Symptoms:** Cannot log in, 401 Unauthorized

**Solutions:**
- Verify LDAP server is reachable: `ldapsearch -x -H ldap://ldap.redmatter.com:389`
- Check Apache LDAP configuration in `/etc/httpd/conf.d/guardian.conf`
- Review `/var/log/httpd/guardian-error.log`

#### 2. Package Move Fails

**Symptoms:** Error after clicking confirm

**Solutions:**
- Check sudo permissions: `sudo -u builduser ls /home/builduser/repo`
- Verify builduser owns repository files
- Check disk space on relay server
- Review `/var/log/guardian/guardian.log`

#### 3. Repository Not Updating

**Symptoms:** Packages moved but not visible to yum

**Solutions:**
- Run createrepo manually:
  ```bash
  sudo -u builduser createrepo /home/builduser/repo/7/qa/x86_64/
  ```
- Check `repo-refresh` script exists and is executable
- Verify `crcommand` configuration in guardian.php

#### 4. Packages Not Showing

**Symptoms:** Package list is empty or missing packages

**Solutions:**
- Verify repository paths exist:
  ```bash
  ls /home/builduser/repo/7/dev/noarch/
  ```
- Check `archlist` and `centosver` config matches directory structure
- Ensure Apache user can read repository directories

### Debug Mode

Enable debug logging in Kohana:

```php
// application/config/config.php
$config['log_threshold'] = 4;  // Log all messages
```

View debug logs:
```bash
tail -f /var/log/guardian/guardian.log
```

---

## Security Considerations

### Access Control

1. **LDAP Authentication**: All users must authenticate against LDAP
2. **Group Authorization**: Can restrict access to specific LDAP groups
3. **Audit Logging**: All package moves are logged with username

### Sudo Configuration

Guardian requires sudo access for the Apache user. The principle of least privilege is applied:

```
# Only allow specific commands
apache ALL=(builduser) NOPASSWD: /bin/mv
apache ALL=(builduser) NOPASSWD: /bin/rm
apache ALL=(builduser) NOPASSWD: /usr/bin/repo-refresh

# No shell access
Defaults:apache !requiretty
```

### Network Security

- Run Guardian behind VPN or internal network only
- Use HTTPS with valid certificates
- Firewall should block external access to port 80/443

---

## Related Documentation

- **Infrastructure-Versions**: [GitHub](https://github.com/redmatter/infrastructure-versions) - Modern deployment pipeline
- **Salt Stack**: [Salt Stack Infrastructure](/docs/infrastructure/salt-stack.md) - Configuration management
- **QA Deployment Runbook**: [Confluence](https://natterbox.atlassian.net/wiki/spaces/NPD/pages/2750840833/) - QA deployment procedures
- **Release Management**: [Confluence](https://natterbox.atlassian.net/wiki/spaces/NPD/pages/999096321/) - Release process overview

---

## Source Code Reference

**GitHub Repository:** `redmatter/infrastructure-guardian`

| File | Description |
|------|-------------|
| `application/config/guardian.php` | Main configuration |
| `application/controllers/guardian.php` | Package management controller |
| `application/models/guardian.php` | Core business logic |
| `application/libraries/LDAPHelper.php` | LDAP authentication |
| `apache.conf` | Apache virtual host |
| `RM-guardian.spec` | RPM package specification |

---

*This documentation was created from source code analysis of the `infrastructure-guardian` repository and cross-referenced with Confluence release management documentation.*
