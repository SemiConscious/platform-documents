# Natterbox Repository Inventory

> **Last Updated:** 2026-01-19  
> **Total Repositories:** ~450+  
> **Status:** ✅ Complete

This document provides a comprehensive inventory of all repositories in the Natterbox platform, organized by functional domain.

---

## Table of Contents

1. [Core Platform](#1-core-platform)
2. [Voice Routing & Telephony](#2-voice-routing--telephony)
3. [Omnichannel](#3-omnichannel)
4. [Salesforce Integration](#4-salesforce-integration)
5. [AI & Conversational AI](#5-ai--conversational-ai)
6. [Observability & Analytics](#6-observability--analytics)
7. [Auth & Permissions](#7-auth--permissions)
8. [Frontend Applications](#8-frontend-applications)
9. [Mobile Applications](#9-mobile-applications)
10. [Infrastructure - Terraform Modules](#10-infrastructure---terraform-modules)
11. [Infrastructure - Configuration Management](#11-infrastructure---configuration-management)
12. [Infrastructure - Containers & Images](#12-infrastructure---containers--images)
13. [Libraries & SDKs](#13-libraries--sdks)
14. [CI/CD & DevOps](#14-cicd--devops)
15. [Operations & Tools](#15-operations--tools)
16. [Testing](#16-testing)
17. [Documentation](#17-documentation)
18. [Internal Tools & Projects](#18-internal-tools--projects)
19. [Legacy & Archived](#19-legacy--archived)

---

## 1. Core Platform

Core services that form the backbone of the Natterbox platform.

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/platform-api` | Core API for machine and human interfacing, main hub for database interaction | PHP | Active |
| `redmatter/platform-sapien` | Platform Sapien - core platform service | PHP | Active |
| `redmatter/schema-api` | API Schema files | PHP | Active |
| `redmatter/schema-apidata` | Schema package for API Data (dbmigrate managed) | PHP | Active |
| `redmatter/schema-systemhealth` | System health schema | PHP | Active |
| `redmatter/platform-service-gateway` | Service Gateway | PHP | Active |
| `redmatter/platform-geoshim` | Core API proxy with keep-alive and connection pools for GDC latency | C++ | Active |
| `redmatter/go-geoshim` | Go implementation of GeoShim | Go | Active |
| `redmatter/platform-workflow-engine` | REST interface for workflow payload injection (formerly CDR2SGAPI) | PHP | Active |
| `redmatter/platform-toolbox` | Platform utilities | PHP | Active |
| `redmatter/delta` | Delta API | TypeScript | Active |
| `redmatter/delta-common` | Delta common components | HCL | Active |
| `redmatter/organization-management-api` | Organization Management API | TypeScript | Active |

---

## 2. Voice Routing & Telephony

FreeSWITCH-based voice routing, call handling, and telephony components.

### Core Telephony

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/platform-freeswitch` | FreeSWITCH telephony switch with RM modules and patches | C | Active |
| `redmatter/platform-opensips` | OpenSIPS 3.3.4 with custom Redmatter module | C | Active |
| `redmatter/platform-dialplan` | FreeSWITCH dialplan configuration XML | PHP/XML | Active |
| `redmatter/platform-dialplanscripts` | Scripts run by FreeSWITCH | JavaScript | Active |
| `redmatter/platform-fscore` | JS, PHP, Lua scripts and XML config for FreeSWITCH | Lua/PHP/JS | Active |

### Call Processing

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/platform-fsxinetdsocket` | FreeSWITCH task offloading for CRM, scripting engine integration | PHP | Active |
| `redmatter/platform-fsxinetdsocket-php8` | PHP 8 version of fsxinetdsocket | PHP | Active |
| `redmatter/natterbox-avsapp-scripts` | Lua scripts for AVS app (follows Natterbox flow) | Lua | Active |
| `redmatter/platform-fseventmonitor` | PHP daemon for FreeSWITCH events and call control | PHP | Active |
| `redmatter/platform-fseventfilemonitor` | PHP daemon for file-based actions from FS events | PHP | Active |
| `redmatter/platform-fscallcentermonitor` | PHP daemon for call queues, agents & stats | PHP | Active |
| `redmatter/go-fs-to-aws` | FreeSWITCH events to AWS | Go | Active |
| `redmatter/go-fsevents` | Non-blocking event handler for FreeSWITCH | Go | Active |

### CDR & Recording

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/platform-cdrmunch` | CDR processing components | C++ | Active |
| `redmatter/platform-cdr2sgapi` | CDR2SGAPI | PHP | Active |
| `redmatter/go-cdr-import` | CDR import utility | Go | Active |
| `redmatter/platform-archiving` | Policy-based archiving for CDR, Recordings, PCAP, SMS, MMS | C++ | Active |
| `redmatter/archiving-purge` | Archiving purge and monitoring in AWS | Go | Active |
| `redmatter/tools-archiving` | Miscellaneous archiving tools | Shell | Active |
| `redmatter/takeout-archiving` | Takeout for archiving data | Shell | Active |

### TTS & Transcription

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/platform-tts-gateway` | TTS gateway (replaced Java Ivona server) | C | Active |
| `redmatter/platform-transcribed` | BYOT Transcribe Service | C | Active |
| `redmatter/voices-api` | Voices API lambda code | TypeScript | Active |

### SIP & Gateway

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/platform-sipgwping` | Sends OPTIONS requests to monitor gateway health | C++ | Active |
| `redmatter/lcr-service` | LCR (Least Cost Routing) Service API | TypeScript | Active |

### Routing Policies

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/natterbox-routing-policies` | Routing Policies React App | JavaScript | Active |
| `redmatter/aws-routing-policies` | Routing policies infrastructure | HCL | Active |
| `redmatter/BWs-routing-policy-LUA` | Routing policy Lua scripts | Lua | Active |

### WebPhone

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/platform-webphoned` | WebRTC browser-based softphone daemon | C | Active |
| `redmatter/platform-webphone-web` | WebPhone web functionality | JavaScript | Active |
| `redmatter/platform-webphone-nginx` | WebPhone Nginx config | Shell | Active |

---

## 3. Omnichannel

Multi-channel communication services (SMS, chat, email alongside voice).

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/omnichannel-omniservice` | Omni Channel Pipeline, REST API and supporting services (monorepo) | TypeScript | Active |
| `redmatter/omnichannel-omnisettings` | Omnichannel settings service | TypeScript | Active |
| `redmatter/chat-widget` | Chat widget component | TypeScript | Active |
| `redmatter/omniclient-v2` | Omni-channel React components (v2) | TypeScript | Active |
| `redmatter/omnichannel-omniclient` | Original omniclient | JavaScript | Legacy |
| `redmatter/aws-omnichannel-client-v2` | Omnichannel client v2 infrastructure | HCL | Active |
| `redmatter/aws-omnichannel-search-engine` | Omnichannel search engine | HCL | Active |

---

## 4. Salesforce Integration

Salesforce CRM integration including AVS package and SCV connector.

### Salesforce Packages

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/natterbox-avs-sfdx` | AVS (Natterbox package) SFDX codebase | Apex | Active |
| `redmatter/natterbox-nbavs` | NBAVS package | Apex | Legacy |
| `redmatter/natterbox-nbcc` | Natterbox Call Centre Package | Apex | Active |
| `redmatter/natterbox-scv-package` | Salesforce SCV Package | Apex | Active |
| `SemiConscious/standalone-avs` | Standalone AVS | Apex | Active |

### Salesforce Connectors

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/platform-scv-byot-connector` | SCV BYOT integration with Natterbox telephony | JavaScript | Active |
| `redmatter/sfpbxproxy` | SF PBX Proxy app | PHP | Active |
| `redmatter/sf-internal-delta-connector` | 2GP Package for Delta API (internal SF team) | Apex | Active |

### Internal Salesforce

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/nbinternal-salesforce` | Internal Salesforce org | Apex | Active |
| `redmatter/natterbox-sf-ui` | Natterbox SF UI components | JavaScript | Active |

---

## 5. AI & Conversational AI

Conversational AI services using AWS Bedrock and other AI providers.

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/cai-service` | Conversational AI service with multiple model support | TypeScript | Active |
| `redmatter/aws-ai-prompt-pipeline` | AI prompt pipeline | JavaScript | Active |
| `redmatter/test-rig` | AI testing batch processor for prompt scenarios | TypeScript | Active |
| `redmatter/nbx-gemini-api` | Gemini API wrapper for internal/customer use | Python | Active |
| `redmatter/nbx-ai-hub-api` | AI API using Vertex AI | Python | Active |
| `redmatter/internal-knowledge-vertex` | Pipeline for processing Docs360 articles | Python | Active |
| `redmatter/bedrock-metrics-aggregator` | Cross-region usage aggregation for inference profiles | TypeScript | Active |
| `SemiConscious/guardrails` | AI guardrails | Python | Active |

---

## 6. Observability & Analytics

Monitoring, metrics, logging, and analytics services.

### Lumina (Observability Platform)

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/lumina` | Observability service for voice communications | TypeScript | Active |
| `redmatter/natterbox-lumina` | Lumina frontend (React 19) | TypeScript | Active |
| `redmatter/observability-service` | Observability service | TypeScript | Active |

### Insight (Analytics)

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/insight-player` | Insight player | JavaScript | Active |
| `redmatter/insight-search-fe` | Insight search frontend | TypeScript | Active |
| `redmatter/insight-insight-category-ui` | Category management UI | TypeScript | Active |
| `redmatter/insight-transcription-analysis` | Lambda for transcription analysis | JavaScript | Active |
| `redmatter/insight-transcription-callback` | Lambda for transcription uploads | JavaScript | Active |
| `redmatter/insight-transcription-stats` | Transcription statistics | JavaScript | Active |
| `redmatter/insight-transcription-manual-retrieve` | Manual transcription retrieval | JavaScript | Active |
| `redmatter/insight-analysis-notifier` | Analysis notifier | Go | Active |
| `redmatter/aws-insight-category-api` | Insight Category REST API | JavaScript | Active |

### Wallboards

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/natterbox-wallboards` | Real-time dashboards for contact center metrics | SCSS | Active |
| `redmatter/natterbox-wbapp` | Wallboards app | JavaScript | Active |
| `redmatter/wallboards-service` | Wallboards service | TypeScript | Active |

---

## 7. Auth & Permissions

Authentication, authorization, and permissions services.

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/naps` | Natterbox Permissions Service | HCL | Active |
| `redmatter/go-gatekeeper-authoriser` | API Gateway/AppSync authorizer | Go | Active |
| `redmatter/go-gatekeeper-jwt-creator` | Lambda for JWT creation | Go | Active |
| `redmatter/go-auth-scopes` | Scopes-based auth toolkit for Go | Go | Active |
| `redmatter/platform-auth-scopes` | Auth Scope YAMLs | Shell | Active |
| `SemiConscious/openid-auth` | OpenID authentication | TypeScript | Active |
| `redmatter/go-jwt` | JWT utilities | Go | Active |
| `redmatter/aws-cognito-internal-auth` | Cognito internal auth | HCL | Active |

---

## 8. Frontend Applications

Web-based frontend applications and UI components.

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/unified-settings` | Unified settings UI | TypeScript | Active |
| `redmatter/natterbox-queuemon` | Queue monitor utilities | PHP | Active |
| `redmatter/platform-cti-client` | CTI Frontend (CTI, CTI 2.0, FreedomCTI, FreedomWeb) | JavaScript | Active |
| `redmatter/frontend-library` | React/TS utility library and components | TypeScript | Active |
| `redmatter/graphiql` | GraphiQL IDE tool | - | Active |
| `redmatter/natterbox-nbcf` | Routing Policy Angular JS codebase | HTML | Legacy |
| `SemiConscious/svelte-portal` | Svelte Portal - modern web frontend | Svelte | Active |
| `redmatter/portal-portal-api` | Portal API | TypeScript | Active |
| `redmatter/portal-portal-web` | Portal web frontend | TypeScript | Active |

---

## 9. Mobile Applications

Native mobile applications for iOS and Android.

| Repository | Description | Language | Status |
|------------|-------------|----------|--------|
| `redmatter/freedom-mobile-ios` | Natterbox Freedom iOS app | Swift | Active |
| `redmatter/freedom-mobile-android` | Natterbox Freedom Android app | Kotlin | Active |
| `redmatter/freedom-mobile` | React Native cross-platform app (legacy) | JavaScript | Legacy |

---

## 10. Infrastructure - Terraform Modules

Terraform modules for AWS infrastructure. Organized by function.

### Networking

| Repository | Description |
|------------|-------------|
| `redmatter/aws-terraform-network` | Core networking |
| `redmatter/aws-terraform-network-rt` | RT platform networking |
| `redmatter/aws-terraform-network-nexus` | Nexus networking |
| `redmatter/aws-terraform-network-global-platform` | Global platform networking |
| `redmatter/aws-terraform-network-hybrid` | Hybrid cloud networking |
| `redmatter/aws-terraform-network-archiving` | Archiving networking |
| `redmatter/aws-terraform-network-build` | Build networking |
| `redmatter/aws-terraform-network-platform` | Platform networking |
| `redmatter/aws-terraform-network-info` | Network info module |
| `redmatter/aws-terraform-dns` | DNS management |
| `redmatter/aws-terraform-global-accelerator` | Global Accelerator |
| `redmatter/aws-terraform-transit-gateway` | Transit Gateway (decommissioned) |

### Compute (ECS, EC2)

| Repository | Description |
|------------|-------------|
| `redmatter/aws-terraform-rt-ecs` | RT ECS |
| `redmatter/aws-terraform-nexus-ecs` | Nexus ECS |
| `redmatter/aws-terraform-global-platform-ecs` | Global Platform ECS |
| `redmatter/aws-terraform-hybrid-ecs` | Hybrid ECS |
| `redmatter/aws-terraform-rt-pbx` | RT PBX |
| `redmatter/aws-terraform-pbx` | PBX module |

### RT Platform Services

| Repository | Description |
|------------|-------------|
| `redmatter/aws-terraform-rt-core-api` | RT Core API |
| `redmatter/aws-terraform-rt-db` | RT Database |
| `redmatter/aws-terraform-rt-log` | RT Logging |
| `redmatter/aws-terraform-rt-monitor` | RT Monitoring & alerting |
| `redmatter/aws-terraform-rt-global-monitor` | RT Global monitoring |
| `redmatter/aws-terraform-rt-notifier` | RT Notifier |
| `redmatter/aws-terraform-rt-service-gateway` | RT Service Gateway |
| `redmatter/aws-terraform-rt-sip` | RT SIP |
| `redmatter/aws-terraform-rt-sipgwping` | RT SIP gateway ping |
| `redmatter/aws-terraform-rt-tts` | RT TTS |
| `redmatter/aws-terraform-rt-transcribed` | RT Transcription |
| `redmatter/aws-terraform-rt-voices` | RT Voices API |
| `redmatter/aws-terraform-rt-cai-websocket` | RT CAI WebSocket |
| `redmatter/aws-terraform-rt-deepgram` | RT Deepgram |
| `redmatter/aws-terraform-rt-deepgram-on-premise` | RT Deepgram on-premise ECS |

### FSX (FreeSWITCH)

| Repository | Description |
|------------|-------------|
| `redmatter/aws-terraform-fsx` | FSX module |
| `redmatter/aws-terraform-fsx8` | FSX PHP 8 version |
| `redmatter/aws-terraform-hybrid-fsx` | Hybrid FSX |

### Omnichannel

| Repository | Description |
|------------|-------------|
| `redmatter/aws-terraform-omnichannel` | Omnichannel infrastructure |
| `redmatter/aws-terraform-omnichannel-territory-setup` | Territory setup |
| `redmatter/aws-terraform-omnichannel-settings` | Settings |
| `redmatter/aws-terraform-omnichannel-region-setup` | Region setup |

### AI/CAI

| Repository | Description |
|------------|-------------|
| `redmatter/aws-terraform-cai` | CAI infrastructure |
| `redmatter/aws-terraform-cai-territory-setup` | CAI territory setup |
| `redmatter/aws-terraform-cai-region-setup` | CAI region setup |
| `redmatter/aws-terraform-bedrock` | Bedrock GenAI configuration |
| `redmatter/aws-terraform-prismatic-cai-kb-poc` | CAI knowledge base POC |

### Lumina (Observability)

| Repository | Description |
|------------|-------------|
| `redmatter/aws-terraform-lumina` | Lumina build/deploy infrastructure |
| `redmatter/aws-terraform-lumina-pipeline` | Lumina metrics pipeline |
| `redmatter/aws-terraform-lumina-region-distributor` | Cross-region event distribution |
| `redmatter/aws-terraform-lumina-territory-setup` | Territory setup |
| `redmatter/aws-terraform-nexus-lumina-pipeline` | Athena metrics pipeline |
| `redmatter/aws-terraform-nexus-lumina-territory-setup` | Nexus Lumina territory |

### Security

| Repository | Description |
|------------|-------------|
| `redmatter/aws-terraform-security-tools` | Security Hub, Config, Inspector |
| `redmatter/aws-terraform-security-configs` | Regional security configs |
| `redmatter/aws-terraform-waf` | WAFv2 Web ACLs |
| `redmatter/aws-terraform-sapien-waf` | Sapien WAF |
| `redmatter/aws-terraform-gatekeeper` | Gatekeeper |

### IAM & Identity

| Repository | Description |
|------------|-------------|
| `redmatter/aws-terraform-iam` | IAM configuration |
| `redmatter/aws-terraform-iam-identity-center` | IAM Identity Center |
| `redmatter/nbinternal-terraform-iam` | Internal project IAM |
| `redmatter/aws-terraform-acm` | Certificate Manager |

### API Gateway

| Repository | Description |
|------------|-------------|
| `redmatter/aws-terraform-api-gateway` | API Gateway |
| `redmatter/aws-terraform-api-licence` | API Licence |
| `redmatter/terraform-api-gateway-rest` | REST API Gateway |
| `redmatter/terraform-api-gateway-websocket` | WebSocket API Gateway |
| `redmatter/aws-terraform-user-websocket` | User WebSocket |

### Services

| Repository | Description |
|------------|-------------|
| `redmatter/aws-terraform-events` | External Events service |
| `redmatter/aws-terraform-events-territory-setup` | Events territory setup |
| `redmatter/aws-terraform-templates` | Message Templates service |
| `redmatter/aws-terraform-templates-territory-setup` | Templates territory setup |
| `redmatter/aws-terraform-eci` | ECI infrastructure |
| `redmatter/aws-terraform-transfer-family` | AWS Transfer Family |
| `redmatter/aws-terraform-sapien-proxy` | Auth0-aware Sapien proxy |
| `redmatter/aws-terraform-webphone` | WebPhone |
| `redmatter/aws-terraform-global-platform-workflow-engine` | Workflow engine ECS |
| `redmatter/aws-terraform-workflow-engine-territory-setup` | Workflow engine territory |
| `redmatter/aws-terraform-routing-state` | DynamoDB routing state |
| `redmatter/aws-terraform-routing-policy` | Routing Policy |
| `redmatter/aws-terraform-routing-policy-territory-setup` | Routing policy territory |
| `redmatter/aws-terraform-graphiql` | GraphiQL |
| `redmatter/aws-terraform-insight-search` | Insight search |
| `redmatter/aws-terraform-voices` | Voices modules |
| `redmatter/aws-terraform-voices-setup` | Voices setup |

### Archiving

| Repository | Description |
|------------|-------------|
| `redmatter/aws-terraform-archiving-db` | Archiving database |
| `redmatter/aws-terraform-archive-export` | Archive export |
| `redmatter/terraform-nexus-archiving-purge` | Archiving purge infrastructure |

### Other Infrastructure

| Repository | Description |
|------------|-------------|
| `redmatter/aws-terraform-salt-master` | Salt master |
| `redmatter/aws-terraform-build` | Build infrastructure |
| `redmatter/aws-terraform-mq` | Message Queue |
| `redmatter/aws-terraform-mvr` | MVR module |
| `redmatter/aws-terraform-minerva` | Minerva |
| `redmatter/aws-terraform-analysis-pipeline` | Recording analysis pipeline |
| `redmatter/aws-terraform-analysis-results-endpoint` | Analysis results endpoint |
| `redmatter/aws-terraform-customer-gateway` | Customer Gateway |
| `redmatter/aws-terraform-wallboards-cache-proxy` | Wallboards cache proxy |
| `redmatter/aws-terraform-slack-git-integration` | Slack Git integration |
| `redmatter/aws-terraform-observability` | Observability |
| `redmatter/aws-terraform-remote-state-s3` | Terraform remote state |
| `redmatter/aws-terraform-bootstrap` | Bootstrap |
| `redmatter/aws-terraform-boilerplate` | Boilerplate |
| `redmatter/aws-terraform-template` | Template |
| `redmatter/aws-terraform-tools` | Tools |
| `redmatter/aws-terraform-global-infrastructure` | Global infrastructure components |
| `redmatter/terraform-elastic` | Elastic Stack |
| `redmatter/terraform-sans` | System Availability Notification Service |
| `redmatter/terraform-sns-alerts-gateway` | SNS alerts gateway |
| `redmatter/terraform-terraform-modules` | Shared Terraform modules |

### CDC Pipeline

| Repository | Description |
|------------|-------------|
| `redmatter/terraform-cdc-pipeline` | CDC pipeline infrastructure |
| `redmatter/terraform-cdc-pipeline-setup` | CDC pipeline parameters |
| `redmatter/terraform-cdc-pipeline-settings` | CDC pipeline settings |
| `redmatter/terraform-cdc-pipeline-territory-setup` | CDC territory setup |
| `redmatter/cdc-pipeline` | CDC pipeline implementation | TypeScript |
| `redmatter/cdc-events` | CDC event structure and JSON schema | Go |

### Data Lake & Internal

| Repository | Description |
|------------|-------------|
| `redmatter/nbinternal-terraform-data-lake` | Internal data lake infrastructure |
| `redmatter/nbinternal-terraform-ucar` | UCAR system infrastructure |

---

## 11. Infrastructure - Configuration Management

Salt Stack and configuration management.

| Repository | Description | Language |
|------------|-------------|----------|
| `redmatter/infrastructure-salt-stack` | Salt Stack configuration | SaltStack |
| `redmatter/infrastructure-versions` | Version management | SaltStack |
| `redmatter/infrastructure-guardian` | Guardian system | HTML |
| `redmatter/infrastructure-hcore` | HCore infrastructure | PHP |
| `redmatter/infrastructure-rm-repo` | RM repository management | Shell |
| `redmatter/infrastructure-rm-factory` | RM factory | PHP |
| `redmatter/infrastructure-rm-firewall` | Firewall management | Shell |
| `redmatter/infrastructure-rm-dbbackup` | Database backup | Shell |
| `redmatter/infrastructure-coredump` | Coredump utility | Shell |
| `redmatter/infrastructure-rm-ek-service` | EK service | HCL |
| `redmatter/infrastructure-rm-k8s-services` | K8s services | - |
| `redmatter/infrastructure-cacti` | Cacti monitoring | - |
| `redmatter/infrastructure-toolkit` | Debugging toolkit Docker image | Shell |
| `redmatter/terraform-salt-versions` | Salt versions | Python |
| `redmatter/third-party-salt` | Salt third-party | Python |
| `redmatter/third-party-saltstack-formula-*` | Salt formulas (docker, ntp, resolver, salt, collectd) | SaltStack |

---

## 12. Infrastructure - Containers & Images

Docker images, container definitions, and base images.

### Container Stats

| Repository | Description |
|------------|-------------|
| `redmatter/infrastructure-container-stats-apache` | Apache stats |
| `redmatter/infrastructure-container-stats-tts` | TTS stats |
| `redmatter/infrastructure-container-stats-webphoned` | Webphoned stats |
| `redmatter/infrastructure-container-stats-transcribed` | Transcribed stats |
| `redmatter/infrastructure-container-turndetect-transcribed` | Turn detection |
| `redmatter/infrastructure-container-noisereduction-transcribed` | Noise reduction |

### Base Images

| Repository | Description |
|------------|-------------|
| `redmatter/base-images-ssh` | SSH base image |
| `redmatter/base-images-apache-httpd` | Apache httpd base |
| `redmatter/base-images-apache-httpd-mod_security` | Apache with mod_security |

### Docker Images

| Repository | Description |
|------------|-------------|
| `redmatter/docker-bamboo` | Bamboo server |
| `redmatter/docker-bamboo-backup` | Bamboo backup |
| `redmatter/docker-bitbucket-backup` | Bitbucket backup |
| `redmatter/docker-crowd` | Crowd |
| `redmatter/docker-vixie-cron` | Vixie cron |
| `redmatter/docker-rsyslog` | Rsyslog |
| `redmatter/docker-collectd-elk` | Collectd ELK monitoring |
| `redmatter/docker-gpg-s3sync` | GPG S3 sync |
| `redmatter/docker-dockerize` | Dockerize |
| `redmatter/docker-rpmdiff` | RPM diff |
| `redmatter/docker-svn2git-workspace` | SVN to Git migration |
| `redmatter/docker-symfony-nginx` | Symfony Nginx |
| `redmatter/plantuml` | PlantUML |

---

## 13. Libraries & SDKs

Shared libraries, SDKs, and utility packages.

### PHP Libraries

| Repository | Description | Language |
|------------|-------------|----------|
| `redmatter/libraries-fscallmanagement` | Call management PHP classes | PHP |
| `redmatter/libraries-fscallmanagement-php8` | PHP 8 version | PHP |
| `redmatter/libraries-kohana` | Kohana 2.3.4 + RM modifications | PHP |
| `redmatter/libraries-kohana-common` | Kohana common utilities | PHP |
| `redmatter/libraries-restclient` | REST client | PHP |
| `redmatter/libraries-restclient-php8` | REST client PHP 8 | PHP |
| `redmatter/libraries-php-esl-lib` | ESL library | PHP |
| `redmatter/libraries-php-esl-lib-async` | Async ESL library | PHP |
| `redmatter/libraries-php-snow-client` | Snow client | PHP |
| `redmatter/libraries-php-snow-block` | Snow block | PHP |
| `redmatter/libraries-php-snow-generator-guzzle5` | Snow generator | PHP |
| `redmatter/libraries-syslogger-php8` | Syslogger | PHP |
| `redmatter/libraries-branding-php8` | Branding | PHP |

### Go Libraries

| Repository | Description | Language |
|------------|-------------|----------|
| `redmatter/go-skyconf` | Cloud parameter store config loader | Go |
| `redmatter/go-log` | Standardised logging wrapper | Go |
| `redmatter/go-retry` | Retry utilities | Go |
| `redmatter/go-monitoring` | Monitoring and Nagios integration | Go |
| `redmatter/go-trie` | Trie data structure | Go |
| `redmatter/go-globre` | Glob to regexp conversion | Go |
| `redmatter/go-builder` | Makefile-based Go build formula | Makefile |
| `redmatter/goesl` | FreeSWITCH ESL wrapper | Go |
| `redmatter/go-esl-client` | ESL client | Go |

### C++ Libraries

| Repository | Description | Language |
|------------|-------------|----------|
| `redmatter/libraries-rml-snow-client` | Snow client | C++ |

### JavaScript/TypeScript Libraries

| Repository | Description | Language |
|------------|-------------|----------|
| `redmatter/frontend-library` | React/TS utility library | TypeScript |
| `redmatter/libraries-jssiplib` | JsSIP library | JavaScript |
| `redmatter/libraries-numberrules` | Number normalisation rules | - |

---

## 14. CI/CD & DevOps

CI/CD pipelines, GitHub Actions, and deployment tooling.

### GitHub Actions

| Repository | Description |
|------------|-------------|
| `redmatter/github-workflows` | Reusable GitHub workflows |
| `redmatter/github-action-gitman` | Git management |
| `redmatter/github-action-rpm-build` | RPM builder (CentOS 7) |
| `redmatter/github-action-go-build` | Go binary builder |
| `redmatter/github-action-go-lambda-build` | Go Lambda builder |
| `redmatter/github-action-apex-build` | Apex package builder |
| `redmatter/github-action-version-calculator` | Version calculator |
| `redmatter/github-action-update-infra-version` | Infrastructure version updater |
| `redmatter/github-action-environment-parser` | Environment parser |
| `redmatter/github-action-guardian-request` | Guardian request |
| `redmatter/github-action-run-salt-ssm` | Salt SSM runner |

### GitHub Integrations

| Repository | Description |
|------------|-------------|
| `redmatter/github-integrations` | GitHub integrations collection |
| `redmatter/github-add-default-rulesets` | Default ruleset Lambda |
| `redmatter/github-add-repository-to-snyk` | Snyk integration |
| `redmatter/github-migration` | Migration scripts |

### Build & Deploy

| Repository | Description |
|------------|-------------|
| `redmatter/aws-ami-builder` | AMI builder |
| `redmatter/aws-docker-terraform` | Terraform Docker wrapper (`tf`) |
| `redmatter/terraform-hosted-runners-build` | GitHub CodeBuild runners |
| `redmatter/terraform-aws-codebuild-github-runners` | CodeBuild runners module |
| `redmatter/cicd-codepipeline-codebuild-integration` | CodePipeline integration |
| `redmatter/aws-terraform-cicd-apply-integration` | CICD apply integration |
| `redmatter/codepipeline-slack-integration` | CodePipeline Slack |
| `redmatter/terraform-codepipeline-s3-deployment` | S3 deployment |

### Release Management

| Repository | Description |
|------------|-------------|
| `redmatter/operations-rmht` | Release Management Helper Toolkit |

---

## 15. Operations & Tools

Operational tools, scripts, and utilities.

| Repository | Description | Language |
|------------|-------------|----------|
| `redmatter/operations-ops-scripts` | Ops scripts | Python |
| `redmatter/operations-rm-maintenancemode` | Maintenance mode | Shell |
| `redmatter/operations-cbchecker` | CB checker | PHP |
| `redmatter/operations-hops` | Hops | Vim Script |
| `redmatter/operations-swapmonitor` | Swap monitor | Go |
| `redmatter/operations-crdt` | CRDT | Python |
| `redmatter/operations-failover-test-kit` | Failover test kit | Shell |
| `redmatter/ops-tools` | Local ops tools | Shell |
| `redmatter/qa-utils` | QA utilities | Shell |
| `redmatter/tools-jwt-generator` | JWT generator | Go |
| `redmatter/tools-private-key-jwt-generator` | Private key JWT generator | Go |
| `redmatter/tools-rm-kpis` | RM KPIs | Go |
| `redmatter/aws-rm-rt-maintenance-agent` | RT maintenance agent | Python |
| `redmatter/platform-rmbackupconf` | Backup config | Shell |

---

## 16. Testing

Testing frameworks, E2E tests, and test utilities.

| Repository | Description | Language |
|------------|-------------|----------|
| `redmatter/tests-e2e-ui` | E2E UI automation tests | Java |
| `redmatter/terraform-ui-e2e-app` | E2E test app infrastructure | HCL |
| `redmatter/aws-terraform-e2e` | E2E infrastructure | HCL |
| `redmatter/aws-terraform-e2e-base` | E2E base infrastructure | HCL |
| `redmatter/OmniTestScripts` | Omni tester utilities | JavaScript |
| `redmatter/omnichannel-omnitestscripts` | Omnichannel test scripts | JavaScript |
| `redmatter/end-to-end-tester-e2et-admin` | E2E test admin | PHP |

---

## 17. Documentation

Documentation repositories.

| Repository | Description | Language |
|------------|-------------|----------|
| `redmatter/aws-docs` | AWS documentation | Shell |
| `redmatter/architecture-docs` | Architecture documentation | Makefile |
| `redmatter/dino-docs` | Dino docs | Shell |
| `redmatter/documentation-lumina` | Lumina documentation | - |
| `redmatter/nbinternal-ucar-docs` | UCAR documentation | - |
| `SemiConscious/platform-documents` | **This repository** | Markdown |

---

## 18. Internal Tools & Projects

Internal productivity tools, automation, and projects.

### UCAR (Usage & Cost Analysis/Reporting)

| Repository | Description |
|------------|-------------|
| `redmatter/nbinternal-ucar-data-ingest` | Data ingestion |
| `redmatter/nbinternal-ucar-event-ingest` | Event ingestion |
| `redmatter/nbinternal-ucar-event-calculation` | Event calculation |
| `redmatter/nbinternal-ucar-report-generation` | Report generation |
| `redmatter/nbinternal-ucar-notifications` | Notifications |

### Internal Automation

| Repository | Description |
|------------|-------------|
| `redmatter/nbx-workspace-analytics` | Workspace analytics hub |
| `redmatter/nbx-it-device-audit` | IT device audit |
| `redmatter/nbx-onboarding-hub` | Onboarding Hub |
| `redmatter/nbx-internal-toolkit` | Internal toolkit |
| `redmatter/google-calendar-access` | Google Calendar automation |
| `redmatter/gsuite-gcp` | GSuite GCP integration |
| `redmatter/automat-it-onboarding-automation` | IT onboarding automation |
| `redmatter/nbinternal-statistical-analysis` | Statistical analysis |
| `redmatter/nbinternal-internal-domains` | Internal domains management |

### Innovation & Hackathons

| Repository | Description |
|------------|-------------|
| `redmatter/summit_2026_team1` through `team8` | Summit 2026 hackathon |
| `redmatter/innovation-day-nbdirect` | Innovation day - NBDirect |
| `redmatter/innovation-day-rust-compiler` | Innovation day - Rust |
| `redmatter/innovation-days-error-collector-utility` | Error collector |
| `redmatter/tech-inno-sherlock` | Innovation - Sherlock |

---

## 19. Legacy & Archived

Older or deprecated repositories retained for reference.

### Legacy Applications

| Repository | Description | Status |
|------------|-------------|--------|
| `redmatter/flexportal` | Flex portal (Adobe Flex) | Legacy |
| `redmatter/platform-flexportal-app` | Flex portal app | Legacy |
| `redmatter/legacy-projects-flexportal` | Legacy Flex portal | Legacy |
| `redmatter/flexportal-installer-windows` | Windows installer | Legacy |
| `redmatter/natterbox-securepayapp` | Secure Pay app | Legacy |
| `redmatter/natterbox-green-box` | Green Box | Legacy |

### Archived Terraform

| Repository | Description | Status |
|------------|-------------|--------|
| `redmatter/aws-terraform-pcipal` | PCIPal (decommissioned) | Archived |
| `redmatter/aws-terraform-transit-gateway` | Transit Gateway (decommissioned) | Archived |
| `redmatter/terraform-transcribed` | Legacy transcribed (see terraform-rt-transcribed) | Legacy |

---

## Statistics Summary

| Category | Count |
|----------|-------|
| Core Platform | ~15 |
| Voice Routing & Telephony | ~35 |
| Omnichannel | ~10 |
| Salesforce Integration | ~10 |
| AI/CAI | ~10 |
| Observability & Analytics | ~20 |
| Auth & Permissions | ~10 |
| Frontend Applications | ~15 |
| Mobile Applications | ~5 |
| Terraform Modules | ~120 |
| Infrastructure Config | ~20 |
| Containers & Images | ~25 |
| Libraries & SDKs | ~30 |
| CI/CD & DevOps | ~25 |
| Operations & Tools | ~20 |
| Testing | ~10 |
| Documentation | ~6 |
| Internal Tools | ~25 |
| Legacy/Archived | ~20 |
| **Total** | **~450+** |

---

## Key Technology Stack

| Layer | Technologies |
|-------|--------------|
| **Languages** | PHP, TypeScript/JavaScript, Go, C/C++, Python, Lua, Swift, Kotlin, Apex |
| **Frameworks** | React, Svelte, Kohana (PHP), Node.js |
| **Voice** | FreeSWITCH, OpenSIPS, WebRTC |
| **Cloud** | AWS (primary), with hybrid cloud support |
| **IaC** | Terraform (extensive), Salt Stack |
| **CI/CD** | GitHub Actions, AWS CodePipeline/CodeBuild |
| **Databases** | MariaDB/MySQL, DynamoDB, Redis, Elasticsearch |
| **AI** | AWS Bedrock, Google Vertex AI, Deepgram |

---

*Document generated: 2026-01-19*
