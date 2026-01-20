# Networking Architecture Deep-Dive

> **Last Updated:** 2026-01-20  
> **Sources:** Confluence (Advanced Networking for Dummies, IP Address Allocation, Direct Connects), GitHub (aws-terraform-network-rt)  
> **Status:** ✅ Complete

---

## Overview

Natterbox operates a sophisticated multi-region, hybrid-cloud networking architecture spanning:
- **6 Production AWS regions** (us-east-2, us-west-2, eu-west-2, eu-central-1, ap-southeast-1, ap-southeast-2)
- **2 On-premise data centers** (S01 in London/Croydon, S02 in Frankfurt/Equinix)
- **Global Platform VPCs** for omnichannel services
- **Site-to-Site VPN tunnels** connecting AWS to on-premise infrastructure
- **Direct Connects** for high-bandwidth carrier connectivity

This document provides a comprehensive technical reference for the networking infrastructure.

---

## High-Level Architecture

```
                              ┌─────────────────────────────────────────────────────────────┐
                              │                    INTERNET / PSTN                          │
                              └───────────────────────────┬─────────────────────────────────┘
                                                          │
              ┌───────────────────────────────────────────┼───────────────────────────────────────────┐
              │                                           │                                           │
              ▼                                           ▼                                           ▼
┌──────────────────────────┐               ┌──────────────────────────┐               ┌──────────────────────────┐
│     ON-PREMISE DCs       │               │      AWS REGIONS         │               │     SIP CARRIERS         │
│                          │               │                          │               │                          │
│  ┌────────────────────┐  │               │  ┌────────────────────┐  │               │  • BT                    │
│  │ S01 (London/6Dg)   │  │◄──────────────┤  │   EU-WEST-2        │  │               │  • Vonage                │
│  │ • PFW-S01          │  │  VPN Tunnels  │  │   EU-CENTRAL-1     │  │               │  • Twilio                │
│  │ • GFW-S01          │  │  Direct       │  │   US-EAST-2        │  │               │  • BICS                  │
│  │ • Legacy Platform  │  │  Connects     │  │   US-WEST-2        │  │               │  • Sinch                 │
│  └────────────────────┘  │               │  │   AP-SOUTHEAST-1   │  │               │  • PCCW                  │
│                          │               │  │   AP-SOUTHEAST-2   │  │               │                          │
│  ┌────────────────────┐  │               │  └────────────────────┘  │               └──────────────────────────┘
│  │ S02 (Frankfurt/LD5)│  │◄──────────────┤                          │
│  │ • PFW-S02          │  │               │  ┌────────────────────┐  │
│  │ • GFW-S02          │  │               │  │   GLOBAL PLATFORM  │  │
│  │ • Legacy Platform  │  │               │  │   (Multi-region)   │  │
│  └────────────────────┘  │               │  └────────────────────┘  │
│                          │               │                          │
└──────────────────────────┘               └──────────────────────────┘
```

---

## On-Premise Data Centers

### S01 - London (Croydon/6Degrees)

| Attribute | Value |
|-----------|-------|
| **Location** | London, UK (6Degrees DC) |
| **Primary Function** | Legacy platform, SIP carrier interconnects |
| **ASN (Private)** | 65502 |
| **ASN (Public)** | 65502 |
| **Key Equipment** | PFW-S01 (Private FW), GFW-S01 (Public FW), MikroTik |
| **Direct Connect** | Digital Realty LHR20 via 6Dg |

### S02 - Frankfurt (Equinix LD5)

| Attribute | Value |
|-----------|-------|
| **Location** | Frankfurt, Germany (Equinix LD5) |
| **Primary Function** | Redundant legacy platform, carrier peering |
| **ASN (Private)** | 65500 (alternates 65501) |
| **ASN (Public)** | 65500 |
| **Key Equipment** | PFW-S02 (Private FW), GFW-S02 (Public FW) |
| **Direct Connect** | Equinix LD5 via Direct Xconnect |

### Firewall Architecture

```
                    ┌─────────────────────────────────────────────────────┐
                    │              DATA CENTER (S01 or S02)               │
                    │                                                     │
                    │   ┌─────────────────────┐   ┌─────────────────────┐ │
     Internet ◄─────┼───│   GFW (Green FW)    │   │   PFW (Private FW)  │─┼─────► AWS VPNs
   (Public IPs)     │   │ • Public traffic    │   │ • Private traffic   │ │      (Private IPs)
                    │   │ • Carrier SIP       │   │ • AWS VPN tunnels   │ │
                    │   │ • Direct Connects   │   │ • Internal services │ │
                    │   └─────────────────────┘   └─────────────────────┘ │
                    │                                                     │
                    │   ┌─────────────────────────────────────────────────┘
                    │   │  Internal Infrastructure:
                    │   │  • Legacy Platform servers
                    │   │  • SIP proxy/media servers
                    │   │  • Database clusters
                    └───┴─────────────────────────────────────────────────
```

---

## AWS VPC Architecture

### VPC Naming Convention

VPCs follow the pattern: `{account}-{region_short}-{purpose}`

| Pattern | Example | Description |
|---------|---------|-------------|
| `{acct}-{region}-rt` | `prod-euw2-rt` | RT Platform VPC |
| `{acct}-{region}-global-platform` | `prod-euw2-global-platform` | Global/Omnichannel VPC |
| `{acct}-{region}-nexus` | `prod-use2-nexus` | Nexus shared services VPC |

### RT VPC Structure

Each RT region VPC is organized into **security zones** with color-coded subnet tiers:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           RT REGION VPC (e.g., prod-euw2-rt)                         │
│                                CIDR: 10.224.0.0/16                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────┐  │
│  │                      🔴 RED ZONE (Public-Facing)                                │  │
│  │                                                                                 │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │  │
│  │  │ red-external-a  │  │ red-external-b  │  │ red-external-c  │  (3 AZs)        │  │
│  │  │ x.x.0.0/26      │  │ x.x.0.64/26     │  │ x.x.0.128/26    │                  │  │
│  │  │ • PBX public    │  │ • PBX public    │  │ • PBX public    │                  │  │
│  │  │ • SIP public    │  │ • SIP public    │  │ • SIP public    │                  │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │  │
│  │                                                                                 │  │
│  │  ┌─────────────────┐  ┌─────────────────┐                                       │  │
│  │  │ red-internal-a  │  │ red-internal-b  │  (CTI, WebPhone, VPN)                │  │
│  │  │ x.x.1.0/24      │  │ x.x.2.0/24      │                                       │  │
│  │  └─────────────────┘  └─────────────────┘                                       │  │
│  └────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────┐  │
│  │                    🟠 AMBER ZONE (Internal Services)                            │  │
│  │                                                                                 │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │  │
│  │  │ amber-internal-a│  │ amber-internal-b│  │ amber-internal-c│  (3 AZs)        │  │
│  │  │ x.x.16.0/20     │  │ x.x.32.0/20     │  │ x.x.48.0/20     │                  │  │
│  │  │ • Core API (ECS)│  │ • FSX (EC2)     │  │ • CAI services  │                  │  │
│  │  │ • Service GW    │  │ • Workers       │  │ • WebSocket     │                  │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │  │
│  │                                                                                 │  │
│  │  ┌─────────────────┐                                                            │  │
│  │  │ amber-nat-a/b/c │  (NAT Gateway subnets for outbound)                       │  │
│  │  │ x.x.64.0/28 ea  │                                                            │  │
│  │  └─────────────────┘                                                            │  │
│  └────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────┐  │
│  │                      🟢 GREEN ZONE (Data Tier)                                  │  │
│  │                                                                                 │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │  │
│  │  │ green-database-a│  │ green-database-b│  │ green-database-c│  (3 AZs)        │  │
│  │  │ x.x.128.0/20    │  │ x.x.144.0/20    │  │ x.x.160.0/20    │                  │  │
│  │  │ • RDS instances │  │ • Aurora        │  │ • ElastiCache   │                  │  │
│  │  │ • Redis         │  │ • Primary DB    │  │ • Replicas      │                  │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │  │
│  │                                                                                 │  │
│  │  ┌─────────────────┐                                                            │  │
│  │  │ green-vpn-db    │  (VPN-accessible database subnets)                        │  │
│  │  │ x.x.192.0/24    │                                                            │  │
│  │  └─────────────────┘                                                            │  │
│  └────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Subnet Types by Zone

| Zone | Subnet Type | CIDR Pattern | Purpose | Internet Access |
|------|-------------|--------------|---------|-----------------|
| **Red** | red-external | /26 per AZ | Public PBX/SIP with BYOIP | Direct (IGW) |
| **Red** | red-internal | /24 per AZ | CTI, WebPhone, VPN endpoints | NAT Gateway |
| **Amber** | amber-internal | /20 per AZ | Core API, FSX, workers | NAT Gateway |
| **Amber** | amber-nat | /28 per AZ | NAT Gateway placement | Direct (IGW) |
| **Green** | green-database | /20 per AZ | RDS, Aurora, ElastiCache | None |
| **Green** | green-vpn-db | /24 | VPN-accessible databases | Via VPN |

---

## IP Address Allocation

### Private Address Space (10.0.0.0/8)

The 10.0.0.0/8 address space is allocated hierarchically by environment:

```
10.0.0.0/8 Master Block
├── 10.0.0.0/10   - Legacy/Reserved
├── 10.64.0.0/10  - AWS Development (dev01-dev05)
├── 10.128.0.0/11 - AWS QA (qa01, qa02)
├── 10.160.0.0/11 - AWS Staging
└── 10.192.0.0/10 - AWS Production
```

### Production VPC CIDR Allocations

| VPC Name | CIDR Block | AWS Region | Purpose |
|----------|------------|------------|---------|
| `prod-euw2-rt` | 10.224.0.0/16 | eu-west-2 | RT Platform UK |
| `prod-euc1-rt` | 10.226.0.0/16 | eu-central-1 | RT Platform EU |
| `prod-use2-rt` | 10.228.0.0/16 | us-east-2 | RT Platform US East |
| `prod-usw2-rt` | 10.230.0.0/16 | us-west-2 | RT Platform US West |
| `prod-apse2-rt` | 10.232.0.0/16 | ap-southeast-2 | RT Platform APAC |
| `prod-apse1-rt` | 10.234.0.0/16 | ap-southeast-1 | RT Platform Singapore |
| `prod-apse2-global-platform` | 10.238.0.0/16 | ap-southeast-2 | Global Platform APAC |
| `prod-euc1-global-platform` | 10.240.0.0/16 | eu-central-1 | Global Platform EU |
| `prod-euw2-global-platform` | 10.243.0.0/16 | eu-west-2 | Global Platform UK |
| `prod-use2-global-platform` | 10.244.0.0/16 | us-east-2 | Global Platform US East |
| `prod-usw2-global-platform` | 10.245.0.0/16 | us-west-2 | Global Platform US West |
| `prod-use2-nexus` | 10.246.0.0/16 | us-east-2 | Nexus US East |
| `prod-usw2-nexus` | 10.247.0.0/16 | us-west-2 | Nexus US West |

### BYOIP (Bring Your Own IP) Ranges

Production uses company-owned public IP ranges for SIP/PBX services:

| CIDR Block | RIR | AWS Region | Purpose |
|------------|-----|------------|---------|
| 185.185.77.0/24 | RIPE | eu-west-2 | RT SIP/PBX UK |
| 185.185.78.0/24 | RIPE | eu-central-1 | RT SIP/PBX EU |
| 5.180.188.0/24 | RIPE | us-east-2 | RT SIP/PBX US East |
| 5.180.189.0/24 | RIPE | us-west-2 | RT SIP/PBX US West |
| 103.73.186.0/24 | APNIC | ap-southeast-2 | RT SIP/PBX APAC |
| 103.73.187.0/24 | APNIC | ap-southeast-1 | RT SIP/PBX Singapore |
| 5.180.191.0/24 | RIPE | Global | Global Accelerator |

### Public VPC Subnet Allocations (per AZ)

| Region | AZ A | AZ B | AZ C |
|--------|------|------|------|
| eu-west-2 | 185.185.77.0/26 | 185.185.77.64/26 | 185.185.77.128/26 |
| eu-central-1 | 185.185.78.0/26 | 185.185.78.64/26 | 185.185.78.128/26 |
| us-east-2 | 5.180.188.0/26 | 5.180.188.64/26 | 5.180.188.128/28 |
| us-west-2 | 5.180.189.0/26 | 5.180.189.64/26 | 5.180.189.128/28 |
| ap-southeast-2 | 103.73.186.0/26 | 103.73.186.64/26 | 103.73.186.128/26 |
| ap-southeast-1 | 103.73.187.0/26 | 103.73.187.64/26 | 103.73.187.128/26 |

---

## VPN Connectivity

### Site-to-Site VPN Architecture

AWS VPCs connect to on-premise data centers via IPsec VPN tunnels:

```
┌──────────────────────┐              ┌──────────────────────┐              ┌──────────────────────┐
│     AWS VPC          │              │    INTERNET          │              │   ON-PREMISE DC      │
│                      │              │                      │              │                      │
│  ┌────────────────┐  │              │                      │              │  ┌────────────────┐  │
│  │ VPN Gateway    │  │◄────────────►│  IPsec Tunnels       │◄────────────►│  │ PFW Firewall   │  │
│  │ (Virtual       │  │              │  (2 tunnels per      │              │  │ (FortiGate)    │  │
│  │  Private GW)   │  │              │   connection for HA) │              │  │                │  │
│  └────────────────┘  │              │                      │              │  └────────────────┘  │
│         │            │              └──────────────────────┘              │         │            │
│         ▼            │                                                    │         ▼            │
│  ┌────────────────┐  │                                                    │  ┌────────────────┐  │
│  │ Route Tables   │  │                                                    │  │ Internal       │  │
│  │ • 10.x.x.x/16  │  │                                                    │  │ Networks       │  │
│  │   via VPN GW   │  │                                                    │  │ • Legacy       │  │
│  └────────────────┘  │                                                    │  │ • Carriers     │  │
│                      │                                                    │  └────────────────┘  │
└──────────────────────┘                                                    └──────────────────────┘
```

### BGP ASN Assignments

| Entity | ASN | Type | Purpose |
|--------|-----|------|---------|
| S01 DC (Private) | 65502 | Private | VPN peering with AWS (private traffic) |
| S01 DC (Public) | 65502 | Private | Direct Connect public VIF |
| S02 DC (Private) | 65500/65501 | Private | VPN peering with AWS (private traffic) |
| S02 DC (Public) | 65500 | Private | Direct Connect public VIF |
| AWS VPCs | 64600-64699 | Private | AWS-side BGP sessions |
| Transit Gateway | 4220224000 | Extended | Transit Gateway routing |

### VPN Tunnel Configuration (from Terraform)

```hcl
# Example VPN configuration from aws-terraform-network-rt/vpn.tf

variable "vpn_asn" {
  description = "BGP ASN values per DC"
  type        = map(number)
  default = {
    s01 = 65502
    s02 = 65500
  }
}

variable "vpn_endpoints" {
  description = "VPN endpoint IPs for each DC"
  type        = map(list(string))
  default = {
    s01 = ["185.185.79.250", "185.185.79.251"]  # PFW-S01 tunnel endpoints
    s02 = ["185.185.79.248", "185.185.79.249"]  # PFW-S02 tunnel endpoints
  }
}
```

### VPN Tunnel Details (Production RT VPCs)

Each RT VPC has 4 VPN tunnels (2 to each DC) for redundancy:

| VPC | Tunnel IP | Target | DC | ASN |
|-----|-----------|--------|-----|-----|
| prod-euw2-rt | 169.254.224.0/30 | vti11 / PFW | S01 | 64602 |
| prod-euw2-rt | 169.254.224.4/30 | vti12 / PFW | S01 | 64602 |
| prod-euw2-rt | 169.254.224.8/30 | vti11 / PFW | S02 | 64601 |
| prod-euw2-rt | 169.254.224.12/30 | vti12 / PFW | S02 | 64601 |
| prod-use2-rt | 169.254.228.0/30 | vti21 / PFW | S01 | 64602 |
| prod-use2-rt | 169.254.228.4/30 | vti22 / PFW | S01 | 64602 |
| prod-use2-rt | 169.254.228.8/30 | vti21 / PFW | S02 | 64601 |
| prod-use2-rt | 169.254.228.12/30 | vti22 / PFW | S02 | 64601 |

---

## Direct Connect

### Direct Connect Architecture

Direct Connects provide dedicated network connections between AWS and on-premise/carrier facilities:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              DIRECT CONNECT ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐       │
│   │  S01 DC         │         │  AWS Direct     │         │  AWS Region     │       │
│   │  (6Degrees)     │◄───────►│  Connect        │◄───────►│  (eu-west-1)    │       │
│   │                 │  DXVIF  │  Location       │  VIF    │                 │       │
│   │  • GFW-S01      │         │  (LHR20)        │         │  • Transit GW   │       │
│   │  • Carrier PoP  │         │                 │         │  • VPCs         │       │
│   └─────────────────┘         └─────────────────┘         └─────────────────┘       │
│                                                                                     │
│   ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐       │
│   │  S02 DC         │         │  AWS Direct     │         │  AWS Region     │       │
│   │  (Equinix LD5)  │◄───────►│  Connect        │◄───────►│  (eu-west-1)    │       │
│   │                 │  DXVIF  │  Location       │  VIF    │                 │       │
│   │  • GFW-S02      │         │  (LD5)          │         │  • Transit GW   │       │
│   │  • Carrier PoP  │         │                 │         │  • VPCs         │       │
│   └─────────────────┘         └─────────────────┘         └─────────────────┘       │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Direct Connect Virtual Interfaces

| Location | RM IP | AWS IP | VIF ID | Region | Account | DC Location |
|----------|-------|--------|--------|--------|---------|-------------|
| S01 via 6Dg | 185.185.79.255 | 185.185.79.254 | dxvif-fftisolz | eu-west-1 | 371360243830 | LHR20 |
| S02 via 6Dg | 185.185.79.253 | 185.185.79.252 | dxvif-fgz71yzh | eu-west-1 | 371360243830 | LD5 |
| MikroTik/LON | 185.185.79.249 | 185.185.79.248 | TBC | eu-west-1 | 371360243830 | LHR20 |

### Transit Gateway

The Transit Gateway provides centralized routing for Direct Connect traffic:

| Attribute | Value |
|-----------|-------|
| **Location** | eu-west-2 |
| **ASN** | 4220224000 |
| **VIF** | prod-shared-tgw |
| **Tunnel IPs** | 169.254.224.64/30 - 169.254.224.76/30 |

---

## Security Groups

### Security Group Architecture (from Terraform)

Security groups are managed in `aws-terraform-network-rt/security_group.tf`:

```hcl
# Example security group definitions

# Core API Security Group
resource "aws_security_group" "core_api" {
  name_prefix = "${local.name_prefix}-core-api"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    description = "HTTPS from ALB"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  ingress {
    description = "Health check from ALB"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# SIP/PBX Security Group
resource "aws_security_group" "sip" {
  name_prefix = "${local.name_prefix}-sip"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    description = "SIP signaling UDP"
    from_port   = 5060
    to_port     = 5060
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    description = "SIP signaling TCP"
    from_port   = 5060
    to_port     = 5060
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    description = "SIP TLS"
    from_port   = 5061
    to_port     = 5061
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    description = "RTP media"
    from_port   = 10000
    to_port     = 30000
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

### Standard Security Groups

| Security Group | Purpose | Key Ports |
|----------------|---------|-----------|
| `alb` | Application Load Balancer | 443 (HTTPS) |
| `core-api` | Core API ECS tasks | 443, 8080 (health) |
| `sip` | SIP proxy servers | 5060/udp, 5061/tcp, 10000-30000/udp |
| `pbx` | PBX servers | 5060/udp, 5061/tcp, 10000-30000/udp |
| `fsx` | FreeSWITCH instances | 5060, 8021, 10000-30000/udp |
| `database` | RDS/Aurora | 3306 (MySQL), 5432 (PostgreSQL) |
| `redis` | ElastiCache Redis | 6379 |
| `vpn` | VPN endpoint | All (for VPN traffic) |

---

## Load Balancing

### Application Load Balancer Configuration (from Terraform)

ALBs are provisioned in `aws-terraform-network-rt/alb.tf`:

```hcl
# Internal ALB for RT services
resource "aws_lb" "internal" {
  name               = "${local.name_prefix}-internal"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_internal.id]
  subnets            = aws_subnet.amber_internal[*].id
  
  enable_deletion_protection = true
  
  tags = {
    Environment = var.environment
    Service     = "rt"
  }
}

# External ALB for public APIs
resource "aws_lb" "external" {
  name               = "${local.name_prefix}-external"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_external.id]
  subnets            = aws_subnet.red_internal[*].id
  
  enable_deletion_protection = true
}
```

### ALB Configuration per Region

| Region | ALB Type | DNS Name | Subnet Zone |
|--------|----------|----------|-------------|
| eu-west-2 | Internal | internal.euw2.rt.natterbox.com | amber-internal |
| eu-west-2 | External | api.euw2.rt.natterbox.com | red-internal |
| us-east-2 | Internal | internal.use2.rt.natterbox.com | amber-internal |
| us-east-2 | External | api.use2.rt.natterbox.com | red-internal |

---

## Global Accelerator

AWS Global Accelerator provides low-latency global routing for CTI traffic:

```hcl
# From aws-terraform-network-rt/global_accelerator.tf

resource "aws_globalaccelerator_accelerator" "cti" {
  name            = "${local.name_prefix}-cti"
  ip_address_type = "IPV4"
  enabled         = true
  
  attributes {
    flow_logs_enabled   = true
    flow_logs_s3_bucket = aws_s3_bucket.flow_logs.bucket
    flow_logs_s3_prefix = "global-accelerator/"
  }
}

resource "aws_globalaccelerator_listener" "cti" {
  accelerator_arn = aws_globalaccelerator_accelerator.cti.id
  protocol        = "TCP"
  
  port_range {
    from_port = 443
    to_port   = 443
  }
}

resource "aws_globalaccelerator_endpoint_group" "cti" {
  for_each = toset(var.deployed_regions)
  
  listener_arn          = aws_globalaccelerator_listener.cti.id
  endpoint_group_region = each.value
  
  endpoint_configuration {
    endpoint_id = aws_lb.cti[each.key].arn
    weight      = 100
  }
  
  health_check_path             = "/health"
  health_check_interval_seconds = 30
  threshold_count               = 3
}
```

### Global Accelerator IPs

| IP Range | Purpose |
|----------|---------|
| 5.180.191.0/24 | BYOIP for Global Accelerator |

---

## VPC Endpoints

Private connectivity to AWS services (from `aws-terraform-network-rt/vpc_endpoint.tf`):

### Gateway Endpoints

| Service | Type | Purpose |
|---------|------|---------|
| S3 | Gateway | Object storage without internet transit |
| DynamoDB | Gateway | NoSQL database access |

### Interface Endpoints

| Service | Type | Purpose |
|---------|------|---------|
| ecr.api | Interface | ECR API calls |
| ecr.dkr | Interface | Docker image pulls |
| logs | Interface | CloudWatch Logs |
| secretsmanager | Interface | Secrets retrieval |
| ssm | Interface | Parameter Store |
| ssmmessages | Interface | Session Manager |
| ecs | Interface | ECS API calls |
| ecs-agent | Interface | ECS agent communication |
| ecs-telemetry | Interface | ECS telemetry |

---

## NAT Gateways

NAT Gateways provide outbound internet access for private subnets:

```hcl
# From aws-terraform-network-rt/nat.tf

resource "aws_nat_gateway" "main" {
  for_each = toset(local.availability_zones)
  
  allocation_id = aws_eip.nat[each.key].id
  subnet_id     = aws_subnet.amber_nat[each.key].id
  
  tags = {
    Name = "${local.name_prefix}-nat-${each.key}"
  }
  
  depends_on = [aws_internet_gateway.main]
}

resource "aws_eip" "nat" {
  for_each = toset(local.availability_zones)
  
  domain = "vpc"
  
  tags = {
    Name = "${local.name_prefix}-nat-eip-${each.key}"
  }
}
```

### NAT Gateway Placement

Each region has one NAT Gateway per availability zone for high availability:

| Region | AZ | NAT Subnet | Purpose |
|--------|-----|------------|---------|
| eu-west-2 | a | amber-nat-a | Outbound for amber/green subnets in AZ-a |
| eu-west-2 | b | amber-nat-b | Outbound for amber/green subnets in AZ-b |
| eu-west-2 | c | amber-nat-c | Outbound for amber/green subnets in AZ-c |

---

## Route Tables

### Route Table Strategy

Each subnet type has dedicated route tables:

```
┌────────────────────────────────────────────────────────────────────┐
│                        ROUTE TABLE STRUCTURE                        │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  RED EXTERNAL (Public)                                              │
│  ├── 0.0.0.0/0         → Internet Gateway                          │
│  ├── 10.x.x.x/16       → Local (VPC)                               │
│  └── 10.0.0.0/8        → VPN Gateway (on-prem)                     │
│                                                                     │
│  RED INTERNAL (Semi-Public)                                         │
│  ├── 0.0.0.0/0         → NAT Gateway                               │
│  ├── 10.x.x.x/16       → Local (VPC)                               │
│  └── 10.0.0.0/8        → VPN Gateway (on-prem)                     │
│                                                                     │
│  AMBER INTERNAL (Private)                                           │
│  ├── 0.0.0.0/0         → NAT Gateway                               │
│  ├── 10.x.x.x/16       → Local (VPC)                               │
│  └── 10.0.0.0/8        → VPN Gateway (on-prem)                     │
│                                                                     │
│  GREEN DATABASE (Isolated)                                          │
│  ├── 10.x.x.x/16       → Local (VPC)                               │
│  ├── 10.0.0.0/8        → VPN Gateway (for VPN DB access)           │
│  └── (No internet route)                                            │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

## VPC Peering

Inter-region VPC peering connects RT VPCs for cross-region communication:

```hcl
# From aws-terraform-network-rt/vpc_peering.tf

resource "aws_vpc_peering_connection" "cross_region" {
  for_each = var.sibling_regions
  
  vpc_id        = aws_vpc.main.id
  peer_vpc_id   = each.value.vpc_id
  peer_region   = each.value.region
  peer_owner_id = data.aws_caller_identity.current.account_id
  
  auto_accept = false
  
  tags = {
    Name = "${local.name_prefix}-peer-${each.key}"
  }
}
```

### Sibling Region Mappings

| Primary Region | Sibling Region | Purpose |
|----------------|----------------|---------|
| us-east-2 | us-west-2 | US failover |
| us-west-2 | us-east-2 | US failover |
| eu-west-2 | eu-central-1 | EU failover |
| eu-central-1 | eu-west-2 | EU failover |
| ap-southeast-2 | ap-southeast-1 | APAC failover |
| ap-southeast-1 | ap-southeast-2 | APAC failover |

---

## Deployed Regions Configuration

From `aws-terraform-network-rt/variables.tf`:

```hcl
variable "deployed_regions" {
  description = "Regions deployed per account"
  type        = map(list(string))
  default = {
    prod = [
      "us-east-2",
      "us-west-2", 
      "eu-west-2",
      "eu-central-1",
      "ap-southeast-1",
      "ap-southeast-2"
    ]
    stage = [
      "eu-west-2",
      "ap-southeast-2"
    ]
    dev01 = [
      "us-east-2",
      "us-west-2"
    ]
    qa01 = [
      "us-east-2",
      "us-west-2"
    ]
    qa02 = [
      "us-east-2",
      "us-west-2"
    ]
  }
}
```

---

## Terraform Module Reference

### Repository

**GitHub:** `redmatter/aws-terraform-network-rt`

### Key Files

| File | Purpose |
|------|---------|
| `vpc.tf` | VPC creation |
| `subnets_red_internal.tf` | Red zone internal subnets |
| `subnets_red_external.tf` | Red zone external (BYOIP) subnets |
| `subnets_amber_internal.tf` | Amber zone internal subnets |
| `subnets_green_database.tf` | Green zone database subnets |
| `security_group.tf` | All security group definitions |
| `vpn.tf` | Site-to-Site VPN configuration |
| `vpc_peering.tf` | Cross-region VPC peering |
| `nat.tf` | NAT Gateway configuration |
| `alb.tf` | Application Load Balancer setup |
| `global_accelerator.tf` | Global Accelerator for CTI |
| `vpc_endpoint.tf` | VPC Endpoints for AWS services |
| `variables.tf` | Input variables |
| `data.tf` | Data sources |

### Workspace Naming

Terraform workspaces follow: `{account}-{region_short}`

| Workspace | Account | Region |
|-----------|---------|--------|
| `prod-euw2` | prod | eu-west-2 |
| `prod-use2` | prod | us-east-2 |
| `stage-apse2` | stage | ap-southeast-2 |
| `dev01-use2` | dev01 | us-east-2 |

---

## Troubleshooting

### Common Issues

#### VPN Tunnel Down

1. Check BGP session status in AWS VPN console
2. Verify on-premise firewall (PFW) IPsec configuration
3. Check ASN matching between AWS and DC
4. Review CloudWatch VPN metrics

```bash
# Check VPN status via AWS CLI
aws ec2 describe-vpn-connections \
  --filters "Name=state,Values=available" \
  --query 'VpnConnections[*].[VpnConnectionId,State,VgwTelemetry[*].Status]'
```

#### Cannot Reach On-Premise from AWS

1. Verify route table has 10.0.0.0/8 → VPN Gateway
2. Check security group allows traffic
3. Verify BGP routes are being advertised
4. Test from VPN-enabled subnet

#### BYOIP Address Not Working

1. Verify BYOIP is provisioned in the region
2. Check Elastic IP is allocated from BYOIP pool
3. Verify security group allows inbound traffic
4. Check instance has public IP assigned

### Useful AWS CLI Commands

```bash
# List VPCs
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=*rt*"

# Check VPN tunnel status
aws ec2 describe-vpn-connections --vpn-connection-ids vpn-xxx

# List NAT Gateways
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=vpc-xxx"

# Check route tables
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=vpc-xxx"

# List security groups
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=vpc-xxx"
```

---

## Related Documentation

- [Infrastructure Overview](./overview.md)
- [Guardian System](./guardian.md)
- [Global Architecture](../global-architecture.md)
- [Confluence: Advanced Networking for Dummies](https://natterbox.atlassian.net/wiki/spaces/CO/pages/688653015)
- [Confluence: AWS IP Address Allocation](https://natterbox.atlassian.net/wiki/spaces/CO/pages/690257734)
- [Confluence: Direct Connects and IP Tunnels](https://natterbox.atlassian.net/wiki/spaces/CO/pages/679411576)

---

*Documentation compiled from Confluence pages and aws-terraform-network-rt repository analysis*
