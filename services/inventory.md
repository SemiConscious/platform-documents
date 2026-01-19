# Service Inventory

> ⚠️ **Status:** Draft - Inventory in progress

Master list of all services in the Natterbox platform.

## Overview

This document catalogs all services, their purposes, repositories, and ownership.

---

## Core Platform Services

| Service | Description | Repository | Language | Status |
|---------|-------------|------------|----------|--------|
| platform-api | Core API for machine and human interfacing | `redmatter/platform-api` | PHP | Active |
| platform-freeswitch | Telephony switch with RM modules | `redmatter/platform-freeswitch` | C | Active |
| platform-sapien | Platform Sapien | `redmatter/platform-sapien` | PHP | Active |
| platform-fscore | JS, PHP, Lua scripts for FreeSWITCH | `redmatter/platform-fscore` | Lua/PHP/JS | Active |
| platform-dialplan | FreeSWITCH dialplan configuration | `redmatter/platform-dialplan` | PHP/XML | Active |
| platform-dialplanscripts | Scripts run by FreeSWITCH | `redmatter/platform-dialplanscripts` | JavaScript | Active |
| platform-fsxinetdsocket | FreeSWITCH task offloading | `redmatter/platform-fsxinetdsocket` | PHP | Active |
| platform-fsxinetdsocket-php8 | PHP 8 version | `redmatter/platform-fsxinetdsocket-php8` | PHP | Active |
| platform-workflow-engine | REST interface for workflow payloads | `redmatter/platform-workflow-engine` | PHP | Active |
| platform-cdrmunch | CDR processing components | `redmatter/platform-cdrmunch` | C++ | Active |
| platform-archiving | Policy-based archiving | `redmatter/platform-archiving` | C++ | Active |
| platform-opensips | OpenSIPS with RM module | `redmatter/platform-opensips` | C | Active |
| platform-transcribed | BYOT Transcribe Service | `redmatter/platform-transcribed` | C | Active |
| platform-toolbox | Platform utilities | `redmatter/platform-toolbox` | PHP | Active |
| platform-sgfs | S3 FUSE driver | `redmatter/platform-sgfs` | C++ | Active |
| platform-call-api | REST API for FreeSWITCH interaction | `redmatter/platform-call-api` | TBD | Active |

---

## Omnichannel Services

| Service | Description | Repository | Language | Status |
|---------|-------------|------------|----------|--------|
| omnichannel-omniservice | Omni Channel Pipeline and REST API | `redmatter/omnichannel-omniservice` | TypeScript | Active |
| omnichannel-omnisettings | Omnichannel settings | `redmatter/omnichannel-omnisettings` | TypeScript | Active |
| chat-widget | Chat widget component | `redmatter/chat-widget` | TypeScript | Active |
| omniclient-v2 | Omni-channel React components | `redmatter/omniclient-v2` | TypeScript | Active |

---

## Salesforce Integration

| Service | Description | Repository | Language | Status |
|---------|-------------|------------|----------|--------|
| natterbox-avs-sfdx | AVS Salesforce package | `redmatter/natterbox-avs-sfdx` | Apex | Active |
| natterbox-avsapp-scripts | Lua scripts for AVS | `redmatter/natterbox-avsapp-scripts` | Lua | Active |
| platform-scv-byot-connector | SCV BYOT integration | `redmatter/platform-scv-byot-connector` | JavaScript | Active |
| nbinternal-salesforce | Internal Salesforce | `redmatter/nbinternal-salesforce` | Apex | Active |

---

## AI/CAI Services

| Service | Description | Repository | Language | Status |
|---------|-------------|------------|----------|--------|
| cai-service | Conversational AI service | `redmatter/cai-service` | TypeScript | Active |
| aws-ai-prompt-pipeline | AI prompt pipeline | `redmatter/aws-ai-prompt-pipeline` | JavaScript | Active |
| test-rig | AI testing batch processor | `redmatter/test-rig` | TypeScript | Active |

---

## Observability & Analytics

| Service | Description | Repository | Language | Status |
|---------|-------------|------------|----------|--------|
| lumina | Observability service | `redmatter/lumina` | TypeScript | Active |
| natterbox-lumina | Lumina frontend | `redmatter/natterbox-lumina` | TypeScript | Active |
| insight-player | Insight player | `redmatter/insight-player` | JavaScript | Active |
| insight-search-fe | Insight search frontend | `redmatter/insight-search-fe` | TypeScript | Active |
| insight-insight-category-ui | Category management UI | `redmatter/insight-insight-category-ui` | TypeScript | Active |

---

## Frontend Applications

| Service | Description | Repository | Language | Status |
|---------|-------------|------------|----------|--------|
| natterbox-routing-policies | Routing policies React app | `redmatter/natterbox-routing-policies` | JavaScript | Active |
| natterbox-wbapp | Wallboards app | `redmatter/natterbox-wbapp` | JavaScript | Active |
| unified-settings | Unified settings | `redmatter/unified-settings` | TypeScript | Active |
| freedom-mobile-ios | iOS mobile app | `redmatter/freedom-mobile-ios` | Swift | Active |
| freedom-mobile-android | Android mobile app | `redmatter/freedom-mobile-android` | Kotlin | Active |

---

## Auth & Permissions

| Service | Description | Repository | Language | Status |
|---------|-------------|------------|----------|--------|
| naps | Natterbox Permissions Service | `redmatter/naps` | HCL/TBD | Active |
| go-gatekeeper-authoriser | API Gateway authorizer | `redmatter/go-gatekeeper-authoriser` | Go | Active |
| go-auth-scopes | Scopes-based auth toolkit | `redmatter/go-auth-scopes` | Go | Active |
| openid-auth | OpenID authentication | `SemiConscious/openid-auth` | TypeScript | Active |

---

## Infrastructure Services

| Service | Description | Repository | Language | Status |
|---------|-------------|------------|----------|--------|
| infrastructure-salt-stack | Salt configuration | `redmatter/infrastructure-salt-stack` | SaltStack | Active |
| infrastructure-guardian | Guardian system | `redmatter/infrastructure-guardian` | HTML | Active |
| infrastructure-hcore | HCore infrastructure | `redmatter/infrastructure-hcore` | PHP | Active |
| infrastructure-versions | Version management | `redmatter/infrastructure-versions` | SaltStack | Active |

---

## Supporting Services

| Service | Description | Repository | Language | Status |
|---------|-------------|------------|----------|--------|
| delta | Delta API | `redmatter/delta` | TypeScript | Active |
| organization-management-api | Org management API | `redmatter/organization-management-api` | TypeScript | Active |
| graphiql | GraphiQL IDE tool | `redmatter/graphiql` | TBD | Active |
| operations-rmht | Release Management Helper Toolkit | `redmatter/operations-rmht` | Python | Active |
| archiving-purge | Archiving purge and monitoring | `redmatter/archiving-purge` | Go | Active |

---

## Libraries

| Library | Description | Repository | Language |
|---------|-------------|------------|----------|
| libraries-fscallmanagement | Call management PHP classes | `redmatter/libraries-fscallmanagement` | PHP |
| libraries-fscallmanagement-php8 | PHP 8 version | `redmatter/libraries-fscallmanagement-php8` | PHP |
| libraries-kohana | Kohana framework (modified) | `redmatter/libraries-kohana` | PHP |
| libraries-kohana-common | Kohana common utilities | `redmatter/libraries-kohana-common` | PHP |
| frontend-library | React/TS utility library | `redmatter/frontend-library` | TypeScript |

---

## Legend

**Status:**
- **Active** - Currently in use and maintained
- **Legacy** - In use but being phased out
- **Deprecated** - No longer in use
- **Development** - Under active development

---

*Last updated: 2026-01-19*  
*TODO: Complete inventory with remaining repositories*
