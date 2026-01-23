# Configuration Reference

## Overview

The `platform-api` service is a complex telecommunications platform API that interfaces with multiple external services including telecom providers, emergency services, FTP servers, and mobile device management systems. This configuration reference provides comprehensive documentation for all configuration variables required to deploy and operate the service across different environments.

### Configuration Approach

The platform-api uses a hierarchical configuration system that supports:

- **Environment variables** for runtime configuration
- **Environment-specific defaults** that change between development, QA, staging, and production
- **External service integrations** requiring credentials and endpoint configurations
- **Security-sensitive values** that must be protected in production environments

Configuration variables follow a dot-notation naming convention (e.g., `NumberAllocator.Magrathea.Host`) which maps to nested configuration structures in the application.

---

## Configuration Files Overview

### Primary Configuration Files

| File | Purpose | Environment |
|------|---------|-------------|
| `.env` | Environment-specific variables | All |
| `config/database.php` | Database connection settings | All |
| `config/services.php` | External service endpoints | All |
| `config/ftp.php` | FTP server configurations | All |
| `config/security.php` | Encryption keys and security settings | All |
| `config/dialplan.php` | Dial plan templates and limits | All |

### Configuration Loading Order

1. Default values from configuration files
2. Environment-specific overrides
3. Environment variables (highest priority)
4. Runtime configuration from remote config service

---

## Database Configuration

### Core Database Settings

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `SQLMODE` | Database driver type selection. Determines which MySQL driver to use for database connections. | `string` | `mysql` | No | `mysqli` |

### Driver Options

- **`mysql`**: Legacy MySQL driver (PHP < 7.0 compatible)
- **`mysqli`**: Improved MySQL driver with better performance and security features (recommended)

### Example Database Configuration

```ini
# Database Configuration
SQLMODE=mysqli
DB_HOST=localhost
DB_PORT=3306
DB_NAME=platform_api
DB_USER=platform_user
DB_PASSWORD=secure_password_here
```

---

## Cache Configuration

Cache configuration is managed through the service gateway and HAPI server connections. The platform relies on distributed caching through these services rather than local cache stores.

### Related Variables

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `HAPIServer` | HAPI server URL providing caching and session management. Set to null in development mode for local testing. | `string` | `http://hapi.<hapiSearchDomain>` | No | `http://hapi.prod.internal` |

---

## OAuth Settings

OAuth and authentication settings are managed through the HAPI server integration. The `HAPIServer` variable points to the authentication service that handles OAuth token validation and user session management.

---

## Billing Integration (JBilling)

Billing integration is handled through the Service Gateway. Configure billing endpoints through the following variables:

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `ServiceGatewayUrl` | URL of the message gateway used for talking to external resources (XRES) including billing systems. | `string` | `http://servicegateway.<hapiSearchDomain>` | **Yes** | `http://servicegateway.prod.internal:8080` |
| `MessageGatewayAddress` | Alias for ServiceGatewayUrl. Can be used interchangeably for backward compatibility. | `string` | `http://servicegateway.<hapiSearchDomain>` | **Yes** | `http://messagegateway.prod.internal:8080` |

---

## Remote Config

The platform supports remote configuration through the HAPI server and Service Gateway. Dynamic configuration values can be updated without service restarts.

### Dynamic Mappings Configuration

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `DynamicMappingsFallbackCountryCode` | Fallback country codes for DynamicMappings used with global SIM cards. Comma-separated list of country codes. | `string` | `44, 1` | No | `44, 1, 33, 49` |
| `MNODefaultDynamicNumberTTL` | Default Mobile Network Operator Dynamic Number (MSRN) Time-To-Live in minutes. Controls how long dynamic number mappings remain valid. | `integer` | `15` | No | `30` |

---

## Environment Variables

### Service Gateway & Messaging

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `ServiceGatewayUrl` | URL of the message gateway for external resource communication (XRES). Critical for all external service integrations. | `string` | `http://servicegateway.<hapiSearchDomain>` | **Yes** | `http://servicegateway.prod.internal:8080` |
| `MessageGatewayAddress` | Alias for ServiceGatewayUrl. Maintains backward compatibility with legacy configurations. | `string` | `http://servicegateway.<hapiSearchDomain>` | **Yes** | `http://servicegateway.prod.internal:8080` |
| `HAPIServer` | HAPI server URL for core platform services. Set to null in development for local testing without HAPI dependency. | `string` | `http://hapi.<hapiSearchDomain>` | No | `http://hapi.prod.internal` |
| `SIPLocalServer` | Local SIP server hostname for voice routing. Must be accessible from the platform-api service. | `string` | `sip-local.<hapiSearchDomain>` | **Yes** | `sip-local.prod.internal` |

### Number API & Allocation

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `NumberAPIAddress` | Number API endpoint address for number management operations. Used for number lookups and allocations. | `string` | `http://127.0.0.1/NP` | **Yes** | `http://numberapi.prod.internal/NP` |
| `AllowedProviders` | List of allowed number allocation providers. Array of provider identifiers that can be used for number provisioning. | `array` | `['magrathea']` | **Yes** | `['magrathea', 'bandwidth', 'twilio']` |
| `NumberAllocator.DestinationAddress` | Number allocator gateway destination. Endpoint for routing number allocation requests. | `string` | `gateway.<hapiSearchDomain>` | **Yes** | `gateway.prod.internal` |

### Magrathea Telecom Integration

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `NumberAllocator.Magrathea.Host` | Magrathea telecom API host for UK number provisioning and management. | `string` | `api.magrathea-telecom.co.uk` | **Yes** | `api.magrathea-telecom.co.uk` |
| `NumberAllocator.Magrathea.Port` | Magrathea telecom API port. Default is the standard Magrathea API port. | `integer` | `777` | **Yes** | `777` |
| `NumberAllocator.Magrathea.User` | Magrathea telecom API username. Provided by Magrathea during account setup. | `string` | `redmatt-ap` | **Yes** | `your-magrathea-user` |
| `NumberAllocator.Magrathea.Pass` | Magrathea telecom API password. **SENSITIVE** - Must be stored securely. | `string` | `bread4` | **Yes** | `your-secure-password` |

### Choice HLR Integration

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `ExternalAPI.ChoiceHLR.Host` | Choice HLR API host for Home Location Register requests. Used for mobile number validation and routing. | `string` | `http://206.190.228.185/vl/` | **Yes** | `http://hlr-api.choice.com/vl/` |
| `ExternalAPI.ChoiceHLR.Port` | Choice HLR API port. Optional if included in host URL. | `integer` | - | No | `8080` |
| `ExternalAPI.ChoiceHLR.User` | Choice HLR API username for authentication. | `string` | `natterbox` | **Yes** | `your-hlr-user` |
| `ExternalAPI.ChoiceHLR.Pass` | Choice HLR API password. **SENSITIVE** - Must be stored securely. | `string` | `1234` | **Yes** | `your-secure-password` |

### Data Encryption

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `DataConnector.AESKey` | AES encryption key for data connector. Used to encrypt sensitive data in transit and at rest. **CRITICAL SECURITY** - Must be changed from default in production. | `string` | `UNSECURE` | **Yes** | `32-character-secure-key-here!!` |
| `LogsExportQ.AESKey` | AES encryption key for logs export queue. Encrypts log data before export. **CRITICAL SECURITY** - Must be changed from default in production. | `string` | `UNSECURE` | **Yes** | `another-32-char-secure-key!!!!` |

### UK Emergency Services (999)

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `EmergencyServices.44.PickUpMinutes` | UK emergency services pickup times in minutes from midnight. Array of scheduled times for emergency service data collection. | `array` | `[420, 540, 660, 780, 900, 1020, 1140]` | No | `[360, 480, 600, 720, 840, 960, 1080, 1200]` |
| `EmergencyServices.44.DefaultOutboundCLI` | UK emergency services default outbound Caller Line Identity. Used when originating CLI is unavailable. | `string` | `443331500999` | No | `443331500999` |
| `EmergencyServices.44.ProviderID` | UK emergency services provider ID. Identifies the service provider to emergency services. | `integer` | `3` | No | `3` |

### Transatel FTP Configuration

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `FTP.Transatel.Host` | Transatel FTP server host for SIM data exchange. Different hosts for production and development environments. | `string` | `ftp-public.transatel.com` (prod) / `localhost` (dev) | **Yes** | `ftp-public.transatel.com` |
| `FTP.Transatel.User` | Transatel FTP username for authentication. | `string` | `natterbox` | **Yes** | `your-transatel-user` |
| `FTP.Transatel.Pass` | Transatel FTP password. **SENSITIVE** - Different defaults for production vs development. | `string` | `94HRBR05` (prod) / `password` (dev) | **Yes** | `your-secure-ftp-password` |
| `FTP.Transatel.AllowDelete` | Allow file deletion on Transatel FTP server. Enable with caution in production. | `boolean` | `false` | No | `true` |

### BT 999 Emergency Services FTP

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `FTP.BT999.Host` | BT 999 emergency services FTP host. Production uses live system, QA uses test environment. | `string` | `calypso.bt.com` (prod) / `calypsotest.bt.com` (qa) | **Yes** | `calypso.bt.com` |
| `FTP.BT999.User` | BT 999 FTP username assigned by BT for operator access. | `string` | `OLO615` | **Yes** | `OLO615` |
| `FTP.BT999.Pass` | BT 999 FTP password. **SENSITIVE** - Must be kept secure and rotated annually per BT requirements. | `string` | `annua11y` | **Yes** | `your-bt999-password` |
| `FTP.BT999.AllowDelete` | Allow file deletion on BT 999 FTP server. Should be disabled in production. | `boolean` | `false` | No | `false` |
| `FTP.BT999.SSL` | Enable SSL/TLS for BT 999 FTP connection. Must be enabled for production per BT security requirements. | `boolean` | `true` | No | `true` |
| `FTP.BT999.BaseDir` | Base directory on BT 999 FTP server for file operations. | `string` | `/` | No | `/natterbox/uploads/` |
| `FTP.BT999.GPGHomeDirectory` | GPG home directory containing keys for BT 999 file encryption. | `string` | `<appdir>/../../bt999-gpg-homedir` | **Yes** | `/opt/platform-api/gpg/bt999/` |
| `FTP.BT999.PassPhraseKey` | GPG passphrase key for BT 999 encryption. **CRITICAL SECURITY** - Must be stored securely. | `string` | `78oyngw654T*Bonvweho8709*&%` | **Yes** | `your-secure-gpg-passphrase` |
| `FTP.BT999.GPGKeyID` | GPG key ID for BT 999 encryption operations. | `string` | `BT999-Calypso` | **Yes** | `BT999-Calypso` |

### Blackberry Provisioning

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `HTTPS.Blackberry.Host` | Blackberry provisioning API host for device management. | `string` | `choicewl.provisioning.blackberry.com/ari/submitXML` (prod) | **Yes** | `choicewl.provisioning.blackberry.com/ari/submitXML` |
| `HTTPS.Blackberry.User` | Blackberry provisioning API username. Different accounts for production and development. | `string` | `natterbox` (prod) / `choicexl_admin` (dev) | **Yes** | `your-blackberry-user` |
| `HTTPS.Blackberry.Pass` | Blackberry provisioning API password. **SENSITIVE** - Environment-specific credentials. | `string` | `Natterbox123` (prod) / `Password789` (dev) | **Yes** | `your-secure-password` |

### XML Processing Configuration

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `XMLVersion` | XML document version for generated XML documents. | `string` | `1.0` | No | `1.0` |
| `XMLEncoding` | XML document encoding for all generated XML. UTF-8 recommended for international character support. | `string` | `UTF-8` | No | `UTF-8` |
| `XMLFormatOutput` | Enable nicely formatted XML output with indentation and line breaks. Disable in production for smaller payloads. | `boolean` | `true` | No | `false` |
| `XMLRecover` | Enable recovery mode for parsing non-well-formed XML documents. Helps handle malformed external API responses. | `boolean` | `true` | No | `true` |

### Dial Plan Configuration

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `DialPlanTemplateVersion` | Dial plan template version number. Increment when making breaking changes to templates. | `integer` | `1` | No | `2` |
| `DialPlanRecursionLimit` | Maximum recursion depth for dial plan processing. Prevents infinite loops in complex dial plans. | `integer` | `4` | No | `6` |
| `DialPlanTemplateMap.ModStartNC_Trigger` | Dial plan template ID for ModStartNC_Trigger template. Maps trigger names to template IDs. | `integer` | `93` | No | `93` |

### File System & Logging

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `FSLogPath` | FreeSWITCH log file path for telephony event logging. Directory must exist and be writable. | `string` | `/var/www/API/application/logs/FSLog/` | **Yes** | `/var/log/platform-api/freeswitch/` |
| `CallDebugPath` | Path for logging received calls and output. Set to `false` to disable call debugging. | `string\|boolean` | `false` | No | `/var/log/platform-api/calls/` |
| `FileSysBase` | RMFS (Remote Managed File System) mount point base path. Must be accessible and mounted. | `string` | `/mnt/rmfs/` | **Yes** | `/mnt/rmfs/` |
| `URLDownloadPath` | File service URL for client file downloads. Must be publicly accessible HTTPS endpoint. | `string` | `https://fileservice.natterbox.com` | **Yes** | `https://files.yourdomain.com` |

---

## Environment-Specific Configurations

### Development Environment

```ini
# ==============================================
# Platform API - Development Configuration
# ==============================================

# Database
SQLMODE=mysqli

# Service Discovery (use localhost or docker-compose service names)
ServiceGatewayUrl=http://localhost:8080
MessageGatewayAddress=http://localhost:8080
HAPIServer=null
SIPLocalServer=sip-local.dev.internal

# Number API
NumberAPIAddress=http://localhost:8081/NP
AllowedProviders=["magrathea"]
NumberAllocator.DestinationAddress=gateway.dev.internal

# Magrathea (use test credentials)
NumberAllocator.Magrathea.Host=api.magrathea-telecom.co.uk
NumberAllocator.Magrathea.Port=777
NumberAllocator.Magrathea.User=test-user
NumberAllocator.Magrathea.Pass=test-password

# Choice HLR (use sandbox)
ExternalAPI.ChoiceHLR.Host=http://sandbox.choice-hlr.com/vl/
ExternalAPI.ChoiceHLR.User=sandbox-user
ExternalAPI.ChoiceHLR.Pass=sandbox-password

# Encryption (development only - NEVER use in production)
DataConnector.AESKey=dev-only-key-not-for-prod!!!
LogsExportQ.AESKey=dev-only-logs-key-not-prod!!

# Dynamic Mappings
DynamicMappingsFallbackCountryCode=44, 1
MNODefaultDynamicNumberTTL=15

# Transatel FTP (local mock)
FTP.Transatel.Host=localhost
FTP.Transatel.User=dev-user
FTP.Transatel.Pass=password
FTP.Transatel.AllowDelete=true

# BT 999 (test environment)
FTP.BT999.Host=calypsotest.bt.com
FTP.BT999.User=OLO615-TEST
FTP.BT999.Pass=test-password
FTP.BT999.SSL=true
FTP.BT999.BaseDir=/test/
FTP.BT999.GPGHomeDirectory=/opt/platform-api/gpg/bt999-test/
FTP.BT999.PassPhraseKey=dev-passphrase-not-for-prod
FTP.BT999.GPGKeyID=BT999-Calypso-Test

# Blackberry (sandbox)
HTTPS.Blackberry.Host=sandbox.provisioning.blackberry.com/ari/submitXML
HTTPS.Blackberry.User=choicexl_admin
HTTPS.Blackberry.Pass=Password789

# XML Processing
XMLVersion=1.0
XMLEncoding=UTF-8
XMLFormatOutput=true
XMLRecover=true

# Dial Plan
DialPlanTemplateVersion=1
DialPlanRecursionLimit=4
DialPlanTemplateMap.ModStartNC_Trigger=93

# File System
FSLogPath=/tmp/platform-api/logs/FSLog/
CallDebugPath=/tmp/platform-api/logs/calls/
FileSysBase=/tmp/platform-api/rmfs/
URLDownloadPath=http://localhost:9000
```

### Staging Environment

```ini
# ==============================================
# Platform API - Staging Configuration
# ==============================================

# Database
SQLMODE=mysqli

# Service Discovery
ServiceGatewayUrl=http://servicegateway.staging.internal:8080
MessageGatewayAddress=http://servicegateway.staging.internal:8080
HAPIServer=http://hapi.staging.internal
SIPLocalServer=sip-local.staging.internal

# Number API
NumberAPIAddress=http://numberapi.staging.internal/NP
AllowedProviders=["magrathea"]
NumberAllocator.DestinationAddress=gateway.staging.internal

# Magrathea (staging credentials)
NumberAllocator.Magrathea.Host=api.magrathea-telecom.co.uk
NumberAllocator.Magrathea.Port=777
NumberAllocator.Magrathea.User=${MAGRATHEA_STAGING_USER}
NumberAllocator.Magrathea.Pass=${MAGRATHEA_STAGING_PASS}

# Choice HLR (staging)
ExternalAPI.ChoiceHLR.Host=http://staging.choice-hlr.com/vl/
ExternalAPI.ChoiceHLR.User=${CHOICE_HLR_STAGING_USER}
ExternalAPI.ChoiceHLR.Pass=${CHOICE_HLR_STAGING_PASS}

# Encryption (use secrets manager in staging)
DataConnector.AESKey=${DATA_CONNECTOR_AES_KEY}
LogsExportQ.AESKey=${LOGS_EXPORT_AES_KEY}

# Dynamic Mappings
DynamicMappingsFallbackCountryCode=44, 1
MNODefaultDynamicNumberTTL=15

# Transatel FTP (staging)
FTP.Transatel.Host=ftp-staging.transatel.com
FTP.Transatel.User=${TRANSATEL_STAGING_USER}
FTP.Transatel.Pass=${TRANSATEL_STAGING_PASS}
FTP.Transatel.AllowDelete=false

# BT 999 (test environment)
FTP.BT999.Host=calypsotest.bt.com
FTP.BT999.User=${BT999_STAGING_USER}
FTP.BT999.Pass=${BT999_STAGING_PASS}
FTP.BT999.SSL=true
FTP.BT999.BaseDir=/staging/
FTP.BT999.GPGHomeDirectory=/opt/platform-api/gpg/bt999/
FTP.BT999.PassPhraseKey=${BT999_GPG_PASSPHRASE}
FTP.BT999.GPGKeyID=BT999-Calypso

# Blackberry (staging)
HTTPS.Blackberry.Host=staging.provisioning.blackberry.com/ari/submitXML
HTTPS.Blackberry.User=${BLACKBERRY_STAGING_USER}
HTTPS.Blackberry.Pass=${BLACKBERRY_STAGING_PASS}

# XML Processing
XMLVersion=1.0
XMLEncoding=UTF-8
XMLFormatOutput=false
XMLRecover=true

# Dial Plan
DialPlanTemplateVersion=1
DialPlanRecursionLimit=4
DialPlanTemplateMap.ModStartNC_Trigger=93

# File System
FSLogPath=/var/log/platform-api/FSLog/
CallDebugPath=false
FileSysBase=/mnt/rmfs/
URLDownloadPath=https://files.staging.natterbox.com
```

### Production Environment

```ini
# ==============================================
# Platform API - Production Configuration
# ==============================================

# Database
SQLMODE=mysqli

# Service Discovery
ServiceGatewayUrl=http://servicegateway.prod.internal:8080
MessageGatewayAddress=http://servicegateway.prod.internal:8080
HAPIServer=http://hapi.prod.internal
SIPLocalServer=sip-local.prod.internal

# Number API
NumberAPIAddress=http://numberapi.prod.internal/NP
AllowedProviders=["magrathea"]
NumberAllocator.DestinationAddress=gateway.prod.internal

# Magrathea (production credentials - from secrets manager)
NumberAllocator.Magrathea.Host=api.magrathea-telecom.co.uk
NumberAllocator.Magrathea.Port=777
NumberAllocator.Magrathea.User=${MAGRATHEA_PROD_USER}
NumberAllocator.Magrathea.Pass=${MAGRATHEA_PROD_PASS}

# Choice HLR (production)
ExternalAPI.ChoiceHLR.Host=http://206.190.228.185/vl/
ExternalAPI.ChoiceHLR.User=${CHOICE_HLR_PROD_USER}
ExternalAPI.ChoiceHLR.Pass=${CHOICE_HLR_PROD_PASS}

# Encryption (MUST use secrets manager)
DataConnector.AESKey=${DATA_CONNECTOR_AES_KEY}
LogsExportQ.AESKey=${LOGS_EXPORT_AES_KEY}

# Dynamic Mappings
DynamicMappingsFallbackCountryCode=44, 1
MNODefaultDynamicNumberTTL=15

# Emergency Services
EmergencyServices.44.PickUpMinutes=[420, 540, 660, 780, 900, 1020, 1140]
EmergencyServices.44.DefaultOutboundCLI=443331500999
EmergencyServices.44.ProviderID=3

# Transatel FTP (production)
FTP.Transatel.Host=ftp-public.transatel.com
FTP.Transatel.User=${TRANSATEL_PROD_USER}
FTP.Transatel.Pass=${TRANSATEL_PROD_PASS}
FTP.Transatel.AllowDelete=false

# BT 999 (production)
FTP.BT999.Host=calypso.bt.com
FTP.BT999.User=${BT999_PROD_USER}
FTP.BT999.Pass=${BT999_PROD_PASS}
FTP.BT999.SSL=true
FTP.BT999.BaseDir=/
FTP.BT999.GPGHomeDirectory=/opt/platform-api/gpg/bt999/
FTP.BT999.PassPhraseKey=${BT999_GPG_PASSPHRASE}
FTP.BT999.GPGKeyID=BT999-Calypso

# Blackberry (production)
HTTPS.Blackberry.Host=choicewl.provisioning.blackberry.com/ari/submitXML
HTTPS.Blackberry.User=${BLACKBERRY_PROD_USER}
HTTPS.Blackberry.Pass=${BLACKBERRY_PROD_PASS}

# XML Processing
XMLVersion=1.0
XMLEncoding=UTF-8
XMLFormatOutput=false
XMLRecover=true

# Dial Plan
DialPlanTemplateVersion=1
DialPlanRecursionLimit=4
DialPlanTemplateMap.ModStartNC_Trigger=93

# File System
FSLogPath=/var/log/platform-api/FSLog/
CallDebugPath=false
FileSysBase=/mnt/rmfs/
URLDownloadPath=https://fileservice.natterbox.com
```

---

## Security Considerations

### Critical Security Variables

The following variables contain sensitive credentials and **MUST** be protected:

| Variable | Risk Level | Protection Required |
|----------|------------|---------------------|
| `DataConnector.AESKey` | **CRITICAL** | Must use secrets manager, rotate quarterly |
| `LogsExportQ.AESKey` | **CRITICAL** | Must use secrets manager, rotate quarterly |
| `NumberAllocator.Magrathea.Pass` | HIGH | Store in secrets manager |
| `ExternalAPI.ChoiceHLR.Pass` | HIGH | Store in secrets manager |
| `FTP.Transatel.Pass` | HIGH | Store in secrets manager |
| `FTP.BT999.Pass` | HIGH | Store in secrets manager, rotate annually |
| `FTP.BT999.PassPhraseKey` | **CRITICAL** | Store in secrets manager |
| `HTTPS.Blackberry.Pass` | HIGH | Store in secrets manager |

### Security Best Practices

1. **Never commit secrets to version control**
   - Use `.env.example` with placeholder values
   - Add `.env` to `.gitignore`

2. **Use a secrets manager in production**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Kubernetes Secrets (with encryption at rest)

3. **Rotate credentials regularly**
   - AES keys: Quarterly minimum
   - API passwords: Every 90 days
   - FTP credentials: Per provider requirements (BT requires annual)

4. **Encrypt at rest**
   - All AES keys must be 256-bit
   - Generate cryptographically secure keys:
     ```bash
     openssl rand -base64 32
     ```

5. **Network security**
   - Use HTTPS for all external API calls
   - Enable SSL for FTP connections
   - Use internal DNS for service discovery

6. **Default value warnings**
   - `DataConnector.AESKey=UNSECURE` - **NEVER** use in production
   - `LogsExportQ.AESKey=UNSECURE` - **NEVER** use in production
   - Default passwords are examples only

### Environment Variable Validation

Add startup validation to ensure critical security variables are not using defaults:

```php
$criticalVars = [
    'DataConnector.AESKey' => 'UNSECURE',
    'LogsExportQ.AESKey' => 'UNSECURE',
];

foreach ($criticalVars as $var => $insecureDefault) {
    if (getenv($var) === $insecureDefault) {
        throw new SecurityException("Critical variable {$var} using insecure default value");
    }
}
```

---

## Docker/Kubernetes Configuration

### Docker Compose Example

```yaml
version: '3.8'

services:
  platform-api:
    image: platform-api:latest
    environment:
      - SQLMODE=mysqli
      - ServiceGatewayUrl=http://servicegateway:8080
      - MessageGatewayAddress=http://servicegateway:8080
      - HAPIServer=http://hapi:8080
      - SIPLocalServer=sip-local
      - NumberAPIAddress=http://numberapi/NP
      - AllowedProviders=["magrathea"]
      - NumberAllocator.DestinationAddress=gateway
    env_file:
      - .env.secrets
    volumes:
      - ./logs:/var/log/platform-api
      - rmfs-data:/mnt/rmfs
      - gpg-keys:/opt/platform-api/gpg
    depends_on:
      - servicegateway
      - hapi
      - numberapi

volumes:
  rmfs-data:
  gpg-keys:
```

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: platform-api-config
data:
  SQLMODE: "mysqli"
  XMLVersion: "1.0"
  XMLEncoding: "UTF-8"
  XMLFormatOutput: "false"
  XMLRecover: "true"
  DialPlanTemplateVersion: "1"
  DialPlanRecursionLimit: "4"
  DialPlanTemplateMap.ModStartNC_Trigger: "93"
  DynamicMappingsFallbackCountryCode: "44, 1"
  MNODefaultDynamicNumberTTL: "15"
  EmergencyServices.44.DefaultOutboundCLI: "443331500999"
  EmergencyServices.44.ProviderID: "3"
```

### Kubernetes Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: platform-api-secrets
type: Opaque
stringData:
  DataConnector.AESKey: "${DATA_CONNECTOR_AES_KEY}"
  LogsExportQ.AESKey: "${LOGS_EXPORT_AES_KEY}"
  NumberAllocator.Magrathea.Pass: "${MAGRATHEA_PASS}"
  ExternalAPI.ChoiceHLR.Pass: "${CHOICE_HLR_PASS}"
  FTP.Transatel.Pass: "${TRANSATEL_PASS}"
  FTP.BT999.Pass: "${BT999_PASS}"
  FTP.BT999.PassPhraseKey: "${BT999_GPG_PASSPHRASE}"
  HTTPS.Blackberry.Pass: "${BLACKBERRY_PASS}"
```

---

## Troubleshooting Common Configuration Issues

### Issue: Service Gateway Connection Failed

**Symptoms:**
- API calls to external services fail
- Timeout errors in logs

**Resolution:**
1. Verify `ServiceGatewayUrl` is accessible:
   ```bash
   curl -v ${ServiceGatewayUrl}/health
   ```
2. Check DNS resolution for service gateway hostname
3. Verify network policies allow traffic on the configured port

### Issue: Database Connection Errors

**Symptoms:**
- "Unknown MySQL driver" errors
- Connection timeouts

**Resolution:**
1. Verify `SQLMODE` is set to `mysql` or `mysqli`
2. Ensure the selected driver extension is installed:
   ```bash
   php -m | grep mysql
   ```
3. Check database credentials and network connectivity

### Issue: AES Encryption Failures

**Symptoms:**
- "Decryption failed" errors
- Data corruption in encrypted fields

**Resolution:**
1. Verify AES keys are exactly 32 characters (256-bit)
2. Ensure keys match between encrypting and decrypting services
3. Check for key rotation issues - encrypted data must use matching key

### Issue: FTP Connection Failures

**Symptoms:**
- "Could not connect to FTP server"
- SSL handshake errors

**Resolution:**
1. Verify FTP host is accessible:
   ```bash
   nc -zv ${FTP_HOST} 21
   ```
2. For SSL issues, verify certificates:
   ```bash
   openssl s_client -connect ${FTP_HOST}:21 -starttls ftp
   ```
3. Check firewall rules for FTP passive mode ports

### Issue: GPG Encryption Failures for BT 999

**Symptoms:**
- "GPG key not found" errors
- Encryption failures when uploading to BT 999

**Resolution:**
1. Verify GPG home directory exists and is readable:
   ```bash
   ls -la ${FTP.BT999.GPGHomeDirectory}
   ```
2. Check GPG key is imported:
   ```bash
   GNUPGHOME=${FTP.BT999.GPGHomeDirectory} gpg --list-keys
   ```
3. Verify key ID matches configuration
4. Test encryption manually:
   ```bash
   GNUPGHOME=${FTP.BT999.GPGHomeDirectory} gpg --encrypt --recipient ${FTP.BT999.GPGKeyID} test.txt
   ```

### Issue: Dial Plan Recursion Limit Exceeded

**Symptoms:**
- "Maximum recursion depth exceeded" errors
- Call routing failures

**Resolution:**
1. Review dial plan for circular references
2. Increase `DialPlanRecursionLimit` if complex routing is required
3. Optimize dial plan to reduce nesting depth

### Issue: XML Parsing Errors

**Symptoms:**
- "XML parsing failed" errors
- Malformed responses from external APIs

**Resolution:**
1. Enable `XMLRecover=true` to handle malformed XML
2. Check external API responses for encoding issues
3. Verify `XMLEncoding` matches source document encoding

---

## Complete Example .env File

```ini
# ==============================================
# Platform API - Complete Configuration Template
# ==============================================
# Copy to .env and modify values as needed
# DO NOT commit .env files to version control
# ==============================================

# ---------------------------------------------
# Database Configuration
# ---------------------------------------------
SQLMODE=mysqli

# ---------------------------------------------
# Service Discovery
# ---------------------------------------------
ServiceGatewayUrl=http://servicegateway.prod.internal:8080
MessageGatewayAddress=http://servicegateway.prod.internal:8080
HAPIServer=http://hapi.prod.internal
SIPLocalServer=sip-local.prod.internal

# ---------------------------------------------
# Number API & Allocation
# ---------------------------------------------
NumberAPIAddress=http://numberapi.prod.internal/NP
AllowedProviders=["magrathea"]
NumberAllocator.DestinationAddress=gateway.prod.internal

# Magrathea Integration
NumberAllocator.Magrathea.Host=api.magrathea-telecom.co.uk
NumberAllocator.Magrathea.Port=777
NumberAllocator.Magrathea.User=CHANGE_ME
NumberAllocator.Magrathea.Pass=CHANGE_ME

# ---------------------------------------------
# External APIs
# ---------------------------------------------
# Choice HLR
ExternalAPI.ChoiceHLR.Host=http://206.190.228.185/vl/
ExternalAPI.ChoiceHLR.Port=
ExternalAPI.ChoiceHLR.User=CHANGE_ME
ExternalAPI.ChoiceHLR.Pass=CHANGE_ME

# ---------------------------------------------
# Encryption Keys (MUST CHANGE IN PRODUCTION)
# ---------------------------------------------
DataConnector.AESKey=CHANGE_ME_32_CHARACTERS_MINIMUM
LogsExportQ.AESKey=CHANGE_ME_32_CHARACTERS_MINIMUM

# ---------------------------------------------
# Dynamic Mappings
# ---------------------------------------------
DynamicMappingsFallbackCountryCode=44, 1
MNODefaultDynamicNumberTTL=15

# ---------------------------------------------
# Emergency Services (UK)
# ---------------------------------------------
EmergencyServices.44.PickUpMinutes=[420, 540, 660, 780, 900, 1020, 1140]
EmergencyServices.44.DefaultOutboundCLI=443331500999
EmergencyServices.44.ProviderID=3

# ---------------------------------------------
# FTP - Transatel
# ---------------------------------------------
FTP.Transatel.Host=ftp-public.transatel.com
FTP.Transatel.User=CHANGE_ME
FTP.Transatel.Pass=CHANGE_ME
FTP.Transatel.AllowDelete=false

# ---------------------------------------------
# FTP - BT 999
# ---------------------------------------------
FTP.BT999.Host=calypso.bt.com
FTP.BT999.User=CHANGE_ME
FTP.BT999.Pass=CHANGE_ME
FTP.BT999.AllowDelete=false
FTP.BT999.SSL=true
FTP.BT999.BaseDir=/
FTP.BT999.GPGHomeDirectory=/opt/platform-api/gpg/bt999/
FTP.BT999.PassPhraseKey=CHANGE_ME
FTP.BT999.GPGKeyID=BT999-Calypso

# ---------------------------------------------
# HTTPS - Blackberry
# ---------------------------------------------
HTTPS.Blackberry.Host=choicewl.provisioning.blackberry.com/ari/submitXML
HTTPS.Blackberry.User=CHANGE_ME
HTTPS.Blackberry.Pass=CHANGE_ME

# ---------------------------------------------
# XML Processing
# ---------------------------------------------
XMLVersion=1.0
XMLEncoding=UTF-8
XMLFormatOutput=false
XMLRecover=true

# ---------------------------------------------
# Dial Plan
# ---------------------------------------------
DialPlanTemplateVersion=1
DialPlanRecursionLimit=4
DialPlanTemplateMap.ModStartNC_Trigger=93

# ---------------------------------------------
# File System & Logging
# ---------------------------------------------
FSLogPath=/var/log/platform-api/FSLog/
CallDebugPath=false
FileSysBase=/mnt/rmfs/
URLDownloadPath=https://fileservice.natterbox.com
```

---

## Appendix: Configuration Variable Quick Reference

| Category | Variable Count | Required Count |
|----------|---------------|----------------|
| Database | 1 | 0 |
| Service Discovery | 4 | 3 |
| Number API | 7 | 7 |
| External APIs | 4 | 4 |
| Encryption | 2 | 2 |
| Dynamic Mappings | 2 | 0 |
| Emergency Services | 3 | 0 |
| FTP - Transatel | 4 | 3 |
| FTP - BT 999 | 9 | 6 |
| HTTPS - Blackberry | 3 | 3 |
| XML Processing | 4 | 0 |
| Dial Plan | 3 | 0 |
| File System | 4 | 3 |
| **Total** | **50** | **31** |