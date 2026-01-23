# Telephony Models

This document covers the telephony-related data models in the platform-api, including phones, devices, SIP trunks, gateways, routing, call status, and related configurations.

## Overview

The telephony subsystem manages all voice communication infrastructure including:

- **Phone Devices** - Physical phone hardware configuration and state
- **Generic Devices** - SIP endpoints and device management
- **SIP Trunks** - External connectivity for calls
- **Gateways** - SIP routing destinations
- **Routes** - Call routing rules
- **Call Status** - Real-time call monitoring
- **LCR (Least Cost Routing)** - Carrier and rate management
- **Subscriptions** - SIP event subscriptions (BLF, voicemail)

## Entity Relationship Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  PhoneType  │────<│    Phone    │     │    Org      │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                          │                    │
                          │              ┌─────┴─────┐
                          │              │           │
                    ┌─────┴─────┐  ┌─────┴────┐ ┌────┴─────┐
                    │  Device   │  │ SIPTrunk │ │  Domain  │
                    └─────┬─────┘  └────┬─────┘ └────┬─────┘
                          │             │            │
                    ┌─────┴─────┐  ┌────┴─────┐ ┌────┴─────┐
                    │  OSReg    │  │ Gateway  │ │  SIPURI  │
                    └───────────┘  └────┬─────┘ └────┬─────┘
                                        │            │
                                   ┌────┴─────┐      │
                                   │  Route   │      │
                                   └──────────┘      │
                                                     │
┌─────────────┐                              ┌───────┴───────┐
│ CallStatus  │──────────────────────────────│ Subscription  │
└─────────────┘                              └───────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    LCR Subsystem                            │
│  ┌───────────┐   ┌──────────┐   ┌────────────┐             │
│  │LCR_Carrier│──<│LCR_Bands │──<│LCR_Numbers │             │
│  └─────┬─────┘   └────┬─────┘   └────────────┘             │
│        │              │                                     │
│  ┌─────┴──────────┐   │                                    │
│  │LCR_CarrierGW   │   │                                    │
│  └─────┬──────────┘   │                                    │
│        │         ┌────┴─────┐                              │
│  ┌─────┴──────┐  │LCR_Rates │                              │
│  │GWHealth    │  └──────────┘                              │
│  └────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Phone

Represents physical phone device configuration and real-time state.

### Purpose

The Phone model tracks auto-provisioned phone hardware, storing MAC addresses, configuration passwords, and current device states (DND, Hold, Mute, etc.).

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| MAC | bigint | Yes | MAC address stored as decimal (base 10), serves as primary key |
| OrgID | int | Yes | Organization ID the phone belongs to |
| PhoneTypeID | int | Yes | Foreign key to PhoneTypes table |
| AdminPassword | string | No | Administrative password for phone configuration |
| RemoteAddress | int | No | Remote IP address stored as integer |
| LocalAddress | int | No | Local IP address stored as integer |
| LastTime | datetime | No | Timestamp of last activity/check-in |
| Reinitialise | enum | No | Flag to trigger phone reinitialization |
| States | int | No | Bitmask representing phone states (DND=1, Hold=2, Offhook=4, Mute=8, etc.) |

### Validation Rules

- MAC address must be unique across the system
- OrgID must reference a valid organization
- PhoneTypeID must reference a valid phone type
- States bitmask values: DND(1), Hold(2), Offhook(4), Mute(8)

### Example

```json
{
  "MAC": 123456789012,
  "OrgID": 1001,
  "PhoneTypeID": 5,
  "AdminPassword": "admin123",
  "RemoteAddress": 3232235777,
  "LocalAddress": 167772161,
  "LastTime": "2024-01-15T14:30:00Z",
  "Reinitialise": "NO",
  "States": 0
}
```

### Relationships

- **PhoneType** (many-to-one): References phone model/type via PhoneTypeID
- **Org** (many-to-one): Belongs to an organization via OrgID
- **Device** (one-to-one): May be linked to a Device record via MAC address

---

## PhoneType

Defines phone model and series information for auto-provisioning.

### Purpose

Stores supported phone hardware models with their series codes, enabling proper configuration template selection during auto-provisioning.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| PhoneTypeID | int | Yes | Primary key identifier |
| SeriesCode | string | Yes | Phone series/model code (e.g., "SIP-T28P", "SIP-T46G") |

### Validation Rules

- SeriesCode must be unique
- SeriesCode format typically follows manufacturer naming conventions

### Example

```json
{
  "PhoneTypeID": 5,
  "SeriesCode": "SIP-T28P"
}
```

### Relationships

- **Phone** (one-to-many): Multiple phones can reference this phone type

---

## Device

Generic SIP device/endpoint configuration.

### Purpose

Represents any SIP-capable device in the system including desk phones, softphones, and other endpoints. Devices are assigned extensions and can be auto-provisioned.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| DevID | int | Yes | Primary key device identifier |
| Desc | string | No | Human-readable device description |
| Location | string | No | Physical location of the device |
| Extension | string | Yes | SIP extension number |
| OrgID | int | Yes | Organization ID |
| Status | string | Yes | Device status (Enable, Suspend) |
| DeviceType | string | Yes | Type classification (Device, Softphone, etc.) |
| MAC | bigint | No | MAC address as decimal (for hardware devices) |
| Password | string | Yes | SIP authentication password |
| AutoProvRandPwd | datetime | No | Timestamp when auto-provisioning password was randomized |

### Validation Rules

- Extension must be unique within the organization's domain
- Status must be one of: Enable, Suspend
- Password should meet complexity requirements
- MAC address, if provided, should be valid and unique

### Example

```json
{
  "DevID": 5001,
  "Desc": "Reception Desk Phone",
  "Location": "Building A, Floor 1",
  "Extension": "1001",
  "OrgID": 1001,
  "Status": "Enable",
  "DeviceType": "Device",
  "MAC": 123456789012,
  "Password": "SecureP@ss123",
  "AutoProvRandPwd": "2024-01-10T09:00:00Z"
}
```

### Relationships

- **Org** (many-to-one): Belongs to organization via OrgID
- **Domain** (many-to-one): Associated with a SIP domain via DMID
- **OSReg** (one-to-one): Registration status tracking
- **Phone** (one-to-one): May link to Phone record via MAC
- **GroupMaps** (one-to-many): Can be member of groups
- **Subscription** (one-to-many): Can subscribe to SIP events

---

## Devices

Extended SIP device model with additional provisioning fields.

### Purpose

Extended device model used in the Devices API, including roaming and provisioning settings.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| DevID | int | Yes | Primary key device identifier |
| Extension | string | Yes | SIP extension number |
| DMID | int | Yes | Foreign key to Domains table |
| OrgID | int | Yes | Organization ID |
| DeviceType | enum | Yes | Type of device |
| Password | string | Yes | SIP authentication password |
| Status | enum | Yes | Device status (Enable/Suspend) |
| Desc | string | No | Device description |
| Location | string | No | Physical location |
| AllowRoaming | enum | No | Whether device can roam (YES/NO) |
| Provisioned | enum | No | Auto-provisioned status (YES/NO) |
| MAC | bigint | No | MAC address as decimal |

### Example

```json
{
  "DevID": 5002,
  "Extension": "1002",
  "DMID": 100,
  "OrgID": 1001,
  "DeviceType": "Device",
  "Password": "SIPAuth456",
  "Status": "Enable",
  "Desc": "Conference Room Phone",
  "Location": "Meeting Room B",
  "AllowRoaming": "NO",
  "Provisioned": "YES",
  "MAC": 223456789012
}
```

---

## Phones

Auto-provisioned phone configuration model.

### Purpose

Stores phone-specific configuration for auto-provisioned devices, particularly admin credentials.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| MAC | bigint | Yes | Primary key - MAC address as decimal |
| AdminPassword | string | No | Phone administrative password |

### Example

```json
{
  "MAC": 123456789012,
  "AdminPassword": "PhoneAdmin789"
}
```

---

## OSReg

Device registration status tracking.

### Purpose

Tracks the current registration status of devices with FreeSWITCH servers, enabling the system to know which devices are online and where they're registered.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| DevID | int | Yes | Foreign key to Device |
| FSPath | int | Yes | FreeSWITCH server IP stored as long integer |

### Validation Rules

- DevID must reference a valid device
- FSPath is converted using ip2long()

### Example

```json
{
  "DevID": 5001,
  "FSPath": 167772161
}
```

### Relationships

- **Device** (one-to-one): Links to the registered device

---

## SIPTrunk

SIP trunk configuration for external call routing.

### Purpose

Defines SIP trunk connections to external carriers or other PBX systems, enabling inbound and outbound calling outside the organization.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| TrunkID | int | Yes | Primary key trunk identifier |
| TrunkName | string | Yes | Human-readable trunk name |
| OrgID | int | Yes | Organization ID owning this trunk |

### Validation Rules

- TrunkName should be unique within the organization
- OrgID must reference a valid organization

### Example

```json
{
  "TrunkID": 100,
  "TrunkName": "Primary PSTN Trunk",
  "OrgID": 1001
}
```

### Relationships

- **Org** (many-to-one): Belongs to organization via OrgID
- **Gateway** (one-to-many): Has multiple gateway configurations
- **Route** (one-to-many): Has routing rules
- **DataConnectorDependencies** (one-to-many): Can be linked to data connectors

---

## Gateway

SIP gateway configuration for trunk routing.

### Purpose

Defines individual gateway endpoints within a SIP trunk, including authentication, capacity limits, and health monitoring settings.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| GatewayID | int | Yes | Primary key gateway identifier |
| TrunkID | int | Yes | Foreign key to SIPTrunk |
| Priority | int | Yes | Gateway selection priority (lower = higher priority) |
| OptionPings | enum | No | Enable SIP OPTIONS ping for health checking |
| PingErrors | string | No | Comma-separated SIP error codes that indicate failure |
| Enabled | enum | Yes | Whether gateway is active (YES/NO) |
| Path | string | Yes | Gateway URI (hostname or IP address) |
| Username | string | No | SIP authentication username |
| Password | string | No | SIP authentication password |
| Port | int | No | SIP port number (default 5060) |
| MaxChannels | int | No | Maximum concurrent call channels |
| ReservedChannelsIn | int | No | Channels reserved for inbound calls |
| ReservedChannelsOut | int | No | Channels reserved for outbound calls |
| WarnChannelsAt | int | No | Channel count threshold for capacity warnings |
| Prefix | string | No | Prefix to add when dialing through this gateway |

### Validation Rules

- TrunkID must reference a valid SIP trunk
- Priority should be unique within the trunk
- Port must be valid (1-65535), defaults to 5060
- MaxChannels must be positive if specified
- ReservedChannelsIn + ReservedChannelsOut should not exceed MaxChannels

### Example

```json
{
  "GatewayID": 200,
  "TrunkID": 100,
  "Priority": 1,
  "OptionPings": "YES",
  "PingErrors": "503,504,408",
  "Enabled": "YES",
  "Path": "sip.carrier.example.com",
  "Username": "trunk_user",
  "Password": "trunk_secret",
  "Port": 5060,
  "MaxChannels": 100,
  "ReservedChannelsIn": 20,
  "ReservedChannelsOut": 20,
  "WarnChannelsAt": 80,
  "Prefix": "9"
}
```

### Relationships

- **SIPTrunk** (many-to-one): Belongs to a trunk via TrunkID

---

## Route

SIP trunk routing rules for number matching.

### Purpose

Defines routing rules that determine which calls should use a specific SIP trunk based on number pattern matching.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| RouteID | int | Yes | Primary key route identifier |
| TrunkID | int | Yes | Foreign key to SIPTrunk |
| Match | enum | Yes | Match type (prefix, exact, regex) |
| Number | int | Yes | Number pattern to match against |

### Validation Rules

- TrunkID must reference a valid SIP trunk
- Match type determines how Number is interpreted
- Number patterns should not overlap within a trunk

### Example

```json
{
  "RouteID": 300,
  "TrunkID": 100,
  "Match": "prefix",
  "Number": 44
}
```

### Relationships

- **SIPTrunk** (many-to-one): Belongs to trunk via TrunkID

---

## Domain

SIP domain configuration for organizations.

### Purpose

Associates SIP domains with organizations, enabling proper routing of SIP URIs and supporting multiple domains per organization.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| DMID | int | Yes | Primary key domain mapping ID |
| OrgID | int | Yes | Organization ID |
| Domain | string | Yes | Fully qualified domain name |
| Default | enum | No | Whether this is the organization's default domain (YES/NO) |

### Validation Rules

- Domain must be a valid FQDN
- Domain must be unique across the system
- Only one domain per organization can be marked as Default

### Example

```json
{
  "DMID": 100,
  "OrgID": 1001,
  "Domain": "company.sip.example.com",
  "Default": "YES"
}
```

### Relationships

- **Org** (many-to-one): Belongs to organization via OrgID
- **SIPURI** (one-to-many): Contains SIP URIs
- **Devices** (one-to-many): Devices registered to this domain

---

## Domains

SIP domains model (alias for Domain).

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| DMID | int | Yes | Primary key domain ID |
| Domain | string | Yes | Domain name |
| OrgID | int | Yes | Foreign key to organization |
| Default | enum | No | Is default domain (YES/NO) |

---

## SIPURI

SIP URI and extension mapping.

### Purpose

Maps SIP URIs (extensions) to users, enabling call routing to specific users and defining their primary contact address.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SIPID | int | Yes | Primary key SIP URI identifier |
| UserID | int | Yes | Foreign key to User |
| Local | string | Yes | Local extension number |
| Default | enum | No | Whether this is the user's default SIP URI (YES/NO) |

### Validation Rules

- UserID must reference a valid user
- Local must be unique within the user's domain
- Only one SIPURI per user can be marked as Default

### Example

```json
{
  "SIPID": 400,
  "UserID": 2001,
  "Local": "1001",
  "Default": "YES"
}
```

### Relationships

- **User** (many-to-one): Belongs to user via UserID
- **Subscription** (one-to-many): Can be monitored by subscriptions
- **GroupMaps** (one-to-many): Can be member of groups

---

## CallStatus

Real-time call status tracking from FreeSWITCH.

### Purpose

Provides live visibility into active calls, tracking call state, participants, codecs, and direction for monitoring and CDR generation.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OrgID | int | Yes | Organization ID |
| UserID | int | No | User ID if call involves a user |
| DevID | int | No | Device ID if call involves a device |
| SIPFromURI | string | Yes | SIP From header URI |
| SIPRequestURI | string | Yes | SIP Request-URI |
| DialPlanDestNumber | string | No | Destination number from dial plan |
| ChannelState | string | Yes | Current channel state (e.g., CS_EXECUTE, CS_EXCHANGE_MEDIA) |
| LastTime | datetime | Yes | Last update timestamp |
| FSMachine | string | Yes | FreeSWITCH server identifier |
| ReadCodec | string | No | Audio codec for receiving |
| WriteCodec | string | No | Audio codec for sending |
| UUID | string | Yes | Unique call leg identifier |
| OtherLegUUID | string | No | UUID of bridged call leg |
| CallDirection | string | Yes | Call direction (inbound/outbound) |

### Validation Rules

- UUID must be unique
- ChannelState must be a valid FreeSWITCH state
- CallDirection must be "inbound" or "outbound"

### Example

```json
{
  "OrgID": 1001,
  "UserID": 2001,
  "DevID": 5001,
  "SIPFromURI": "sip:1001@company.sip.example.com",
  "SIPRequestURI": "sip:+441onal234567890@sip.carrier.com",
  "DialPlanDestNumber": "+441234567890",
  "ChannelState": "CS_EXCHANGE_MEDIA",
  "LastTime": "2024-01-15T14:35:22Z",
  "FSMachine": "fs-node-01",
  "ReadCodec": "PCMA",
  "WriteCodec": "PCMA",
  "UUID": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "OtherLegUUID": "f0e9d8c7-b6a5-4321-fedc-ba0987654321",
  "CallDirection": "outbound"
}
```

### Relationships

- **Org** (many-to-one): Call belongs to organization
- **User** (many-to-one): Optional user association
- **Device** (many-to-one): Optional device association

---

## Subscription

SIP event subscription for presence and voicemail indicators.

### Purpose

Manages SIP SUBSCRIBE dialogs for features like BLF (Busy Lamp Field) and MWI (Message Waiting Indicator), allowing devices to monitor the state of extensions.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| FromDevID | int | Yes | Device ID of the subscriber |
| FromTag | string | Yes | SIP From tag for dialog identification |
| CallID | string | Yes | SIP Call-ID header |
| Expires | int | Yes | Seconds until subscription expires |
| Event | string | Yes | Event package (dialog, message-summary) |
| RegFSPath | string | No | FreeSWITCH registration path |
| RegExpires | int | No | Registration expiry in seconds |
| SubscriberURI | string | Yes | SIP URI of the subscriber |
| TargetURI | string | Yes | SIP URI being monitored |
| ToDevID | int | No | Target device ID |
| ToSIPID | int | No | Target SIP URI ID |

### Validation Rules

- FromDevID must reference a valid device
- Event must be a supported event package
- Expires should be positive
- CallID should be unique per subscription

### Example

```json
{
  "FromDevID": 5001,
  "FromTag": "abc123",
  "CallID": "unique-call-id-12345@192.168.1.100",
  "Expires": 3600,
  "Event": "dialog",
  "RegFSPath": "192.168.10.50",
  "RegExpires": 300,
  "SubscriberURI": "sip:1001@company.sip.example.com",
  "TargetURI": "sip:1002@company.sip.example.com",
  "ToDevID": 5002,
  "ToSIPID": 401
}
```

### Relationships

- **Device** (many-to-one): Subscriber device via FromDevID
- **Device** (many-to-one): Target device via ToDevID
- **SIPURI** (many-to-one): Target SIP URI via ToSIPID

---

## LCR_Carriers

Least Cost Routing carrier/provider definitions.

### Purpose

Defines carriers used for routing calls, including their capabilities and classification for routing decisions.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | int | Yes | Primary key carrier ID |
| CarrierName | string | Yes | Human-readable carrier name |
| Enabled | boolean | Yes | Whether carrier is active |
| Type | enum | Yes | Carrier type (retail, route) |
| ClosedLoopCarrier | boolean | No | Whether carrier is closed-loop |
| PrivateServicesCarrier | boolean | No | Whether carrier provides private services |

### Validation Rules

- CarrierName should be unique
- Type must be "retail" or "route"

### Example

```json
{
  "ID": 1,
  "CarrierName": "Primary Carrier",
  "Enabled": true,
  "Type": "retail",
  "ClosedLoopCarrier": false,
  "PrivateServicesCarrier": false
}
```

### Relationships

- **LCR_Bands** (one-to-many): Carrier has multiple rate bands
- **LCR_CarrierGateway** (one-to-many): Carrier has multiple gateways

---

## LCR_Bands

LCR rate bands/destinations for call pricing.

### Purpose

Groups destinations into bands for pricing purposes, associating country codes and destination types with carriers.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | int | Yes | Primary key band ID |
| BandName | string | Yes | Band/destination name (e.g., "UK Mobile", "US Landline") |
| CarrierID | int | Yes | Foreign key to Carriers |
| Type | string | Yes | Primary band type classification |
| CountryCode | string | No | ISO country code |
| Enabled | enum | Yes | Whether band is active (Yes/No) |

### Validation Rules

- CarrierID must reference a valid carrier
- BandName should be unique within a carrier

### Example

```json
{
  "ID": 10,
  "BandName": "UK Mobile - Vodafone",
  "CarrierID": 1,
  "Type": "Mobile",
  "CountryCode": "GB",
  "Enabled": "Yes"
}
```

### Relationships

- **LCR_Carriers** (many-to-one): Belongs to carrier via CarrierID
- **LCR_Numbers** (one-to-many): Has number prefixes
- **LCR_LCRRates** (one-to-many): Has rate definitions

---

## LCR_Numbers

LCR number prefix lookup table.

### Purpose

Maps dialed number prefixes to rate bands, enabling the system to determine call pricing based on the destination number.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | int | Yes | Primary key number ID |
| Number | string | Yes | Number prefix to match |
| BandID | int | Yes | Foreign key to Bands |
| Enabled | enum | Yes | Whether prefix is active (Yes/No) |
| OrgID | int | No | Organization ID for private number ranges |

### Validation Rules

- Number prefix should not overlap with existing prefixes
- BandID must reference a valid band
- OrgID is optional (0 or null for global prefixes)

### Example

```json
{
  "ID": 100,
  "Number": "447",
  "BandID": 10,
  "Enabled": "Yes",
  "OrgID": 0
}
```

### Relationships

- **LCR_Bands** (many-to-one): Belongs to band via BandID
- **Org** (many-to-one): Optional organization association

---

## LCR_LCRRates

LCR rate definitions for call pricing.

### Purpose

Defines per-minute rates and connection charges for rate bands, supporting time-based rate changes and number formatting rules.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | int | Yes | Primary key rate ID |
| BandID | int | Yes | Foreign key to Bands |
| Rate | decimal | Yes | Per-minute rate |
| Setup | decimal | No | Connection/setup charge |
| Currency | string | Yes | Currency code (e.g., GBP, USD) |
| Period | string | No | Rate period type (e.g., Peak, Off-Peak) |
| Start | datetime | Yes | Rate effective start date |
| Enabled | enum | Yes | Whether rate is active (Yes/No) |
| FormatNumber | string | No | Rule for formatting destination number |
| FormatCLI | string | No | Rule for formatting caller ID |
| ABandID | int | No | A-number band ID for CLI-based rating |

### Validation Rules

- BandID must reference a valid band
- Rate must be non-negative
- Start date must be valid
- Currency must be a valid ISO currency code

### Example

```json
{
  "ID": 500,
  "BandID": 10,
  "Rate": 0.045,
  "Setup": 0.01,
  "Currency": "GBP",
  "Period": "Standard",
  "Start": "2024-01-01T00:00:00Z",
  "Enabled": "Yes",
  "FormatNumber": "E164",
  "FormatCLI": "E164",
  "ABandID": null
}
```

### Relationships

- **LCR_Bands** (many-to-one): Belongs to band via BandID

---

## LCR_CarrierGateway

LCR carrier gateway configurations.

### Purpose

Defines gateway endpoints for LCR carriers, including capacity, reliability weighting, and data center distribution for failover.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | int | Yes | Primary key gateway ID |
| CarrierID | int | Yes | Foreign key to Carriers |
| Enabled | boolean | Yes | Whether gateway is active |
| Prefix | string | No | Dial prefix to add |
| Suffix | string | No | Dial suffix to add |
| ChannelVars | string | No | FreeSWITCH channel variables |
| PrivacyClass | string | No | Privacy classification level |
| PCIZone | string | No | PCI compliance zone |
| ConcCalls | int | No | Maximum concurrent calls |
| Reliability | int | No | Reliability weighting (higher = more reliable) |
| PingGateway | enum | No | Enable health pinging (YES/NO) |
| DataCentre | string | No | Data centers (comma-separated) |
| CarrierGroup | string | No | Carrier groups (comma-separated) |

### Validation Rules

- CarrierID must reference a valid carrier
- ConcCalls must be positive if specified
- Reliability is typically 0-100

### Example

```json
{
  "ID": 50,
  "CarrierID": 1,
  "Enabled": true,
  "Prefix": "",
  "Suffix": "",
  "ChannelVars": "absolute_codec_string=PCMA",
  "PrivacyClass": "Standard",
  "PCIZone": "EU",
  "ConcCalls": 500,
  "Reliability": 95,
  "PingGateway": "YES",
  "DataCentre": "LON,AMS",
  "CarrierGroup": "primary"
}
```

### Relationships

- **LCR_Carriers** (many-to-one): Belongs to carrier via CarrierID
- **LCR_CarrierGatewayHealth** (one-to-many): Has health status records

---

## LCR_CarrierGatewayHealth

LCR gateway health monitoring status.

### Purpose

Tracks the health status of carrier gateways per data center, enabling intelligent failover and load balancing.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | int | Yes | Foreign key to CarrierGateway |
| DataCentre | string | Yes | Data center location |
| Healthy | enum | Yes | Health status (YES/NO) |
| LastUpdate | datetime | Yes | Last health check timestamp |

### Validation Rules

- ID must reference a valid carrier gateway
- DataCentre should match a configured data center

### Example

```json
{
  "ID": 50,
  "DataCentre": "LON",
  "Healthy": "YES",
  "LastUpdate": "2024-01-15T14:30:00Z"
}
```

### Relationships

- **LCR_CarrierGateway** (many-to-one): Belongs to gateway via ID

---

## WholesaleCallCostCache

Cached wholesale call costs for fraud detection.

### Purpose

Caches aggregated call costs for organizations to enable real-time fraud detection and cost limit enforcement.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OrgID | int | Yes | Organization ID |
| Cost | decimal | Yes | Accumulated cost amount |
| Time | datetime | Yes | Cache timestamp |

### Example

```json
{
  "OrgID": 1001,
  "Cost": 1250.75,
  "Time": "2024-01-15T14:00:00Z"
}
```

### Relationships

- **Org** (many-to-one): Organization being monitored

---

## AssocNumbers

Associated phone numbers for users.

### Purpose

Manages phone numbers associated with users for features like call routing, DDI assignment, and call queues.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| UserID | int | Yes | User ID reference |
| OrgID | int | Yes | Organization ID reference |
| Val | string | Yes | Phone number in E.164 format |
| Type | string | Yes | Number type classification |
| Rank | int | No | Priority rank for multiple numbers |
| CallQueue | boolean | No | Enable call queue routing |
| RouteUser | boolean | No | Enable direct user routing |
| RouteDDI | boolean | No | Enable DDI routing |
| RouteGroup | boolean | No | Enable group routing |
| ScreenCallQueue | boolean | No | Screen calls for queue |
| ScreenRouteUser | boolean | No | Screen calls for user |
| ScreenRouteDDI | boolean | No | Screen DDI calls |
| ScreenRouteGroup | boolean | No | Screen group calls |
| ScreenCTI | boolean | No | Enable CTI screening |
| Status | string | Yes | Number status |

### Validation Rules

- Val must be valid E.164 format
- UserID must reference a valid user
- OrgID must reference a valid organization

### Example

```json
{
  "UserID": 2001,
  "OrgID": 1001,
  "Val": "+441onal234567890",
  "Type": "DDI",
  "Rank": 1,
  "CallQueue": true,
  "RouteUser": true,
  "RouteDDI": false,
  "RouteGroup": false,
  "ScreenCallQueue": false,
  "ScreenRouteUser": true,
  "ScreenRouteDDI": false,
  "ScreenRouteGroup": false,
  "ScreenCTI": true,
  "Status": "Active"
}
```

### Relationships

- **User** (many-to-one): Belongs to user via UserID
- **Org** (many-to-one): Belongs to organization via OrgID

---

## DynamicMappings

Dynamic number remapping for MNO calls.

### Purpose

Provides temporary number mappings for mobile network operator integration, enabling proper call routing and CLI handling.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| RemapNumber | string | Yes | Number to remap from |
| CalledMobileNumber | string | Yes | Called mobile number |
| Direction | enum | Yes | Call direction (MO/MT) |
| AllocationExpiry | datetime | Yes | When mapping expires |
| Service | string | Yes | Service type |
| MNOID | int | Yes | Mobile Network Operator ID |
| ClientType | string | Yes | Client type (MNO) |
| MSC | string | No | Mobile Switching Center |
| RequestorIP | string | No | IP of requestor |
| OriginatorMCCMNC | string | No | Originating MCC/MNC |
| CallerMobileNumber | string | No | Caller mobile number |
| OpenCallerNumber | string | No | Open caller number |
| OrgID | int | No | Organization ID |
| OriginatorCC | string | No | Originator country code |
| ClientIdentifier | string | No | Client identifier |

### Validation Rules

- Direction must be "MO" or "MT"
- AllocationExpiry must be in the future when creating

### Example

```json
{
  "RemapNumber": "+441onal234500001",
  "CalledMobileNumber": "+447700900123",
  "Direction": "MO",
  "AllocationExpiry": "2024-01-15T15:00:00Z",
  "Service": "Voice",
  "MNOID": 1,
  "ClientType": "MNO",
  "MSC": "msc01.network.com",
  "RequestorIP": "192.168.1.100",
  "OriginatorMCCMNC": "23410",
  "CallerMobileNumber": "+447700900456",
  "OrgID": 1001,
  "OriginatorCC": "44",
  "ClientIdentifier": "client-001"
}
```

---

## DataConnectorDependencies

Data connector associations with telephony items.

### Purpose

Links external data connectors (like CRM systems) to telephony resources including SIP trunks, tracking synchronization status.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OrgID | int | Yes | Organization ID |
| DCCID | int | Yes | Data connector config ID |
| ConnectedApp | string | Yes | Connected application name |
| LandLine_CountryCode | string | No | Landline country code |
| LandLine_Number | string | No | Landline number |
| SIMID | int | No | SIM ID reference |
| VSIMID | int | No | Virtual SIM ID reference |
| TrunkID | int | No | SIP Trunk ID reference |
| UserID | int | No | User ID reference |
| SyncStatus | enum | No | Sync status (Changed, Delete, etc.) |

### Example

```json
{
  "OrgID": 1001,
  "DCCID": 5,
  "ConnectedApp": "Salesforce",
  "TrunkID": 100,
  "SyncStatus": "Synced"
}
```

### Relationships

- **SIPTrunk** (many-to-one): Optional trunk association
- **DataConnectorCredentials** (many-to-one): Connector configuration

---

## Common Use Cases

### Setting Up a New Phone

1. Create a Device record with extension and credentials
2. Optionally create Phone record for auto-provisioning
3. Create SIPURI linking to user
4. Device registers and creates OSReg entry

### Configuring Outbound Calling

1. Create SIPTrunk for the carrier
2. Add Gateway records with authentication
3. Configure Route rules for number matching
4. Set up LCR_Numbers and LCR_LCRRates for pricing

### Monitoring Active Calls

Query CallStatus records to see:
- Current call state
- Participants (UserID, DevID)
- Codec information
- Call direction and duration

### Implementing BLF

1. Device sends SIP SUBSCRIBE
2. System creates Subscription record
3. Monitor target SIPURI for state changes
4. Send NOTIFY updates to subscriber