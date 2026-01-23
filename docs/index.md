# Natterbox Platform Documentation

[![Services](https://img.shields.io/badge/Services-20-blue.svg)](services/)
[![Documents](https://img.shields.io/badge/Documents-251-green.svg)](#statistics)
[![Words](https://img.shields.io/badge/Words-564K+-orange.svg)](#statistics)

> Comprehensive documentation for the Natterbox telecommunications platform, auto-generated using AI-powered code analysis.

---

## Quick Navigation

| Category | Services | Description |
|----------|----------|-------------|
| [Core APIs](#core-apis) | 4 | Central platform APIs and gateways |
| [Frontend Applications](#frontend-applications) | 4 | Web applications and UIs |
| [Infrastructure (Terraform)](#infrastructure-terraform) | 4 | Infrastructure as Code modules |
| [Microservices](#microservices) | 5 | Backend services and pipelines |
| [Schema & Data](#schema--data) | 3 | Database schemas and telemetry |

---

## Core APIs

The central APIs powering the Natterbox platform.

### [Platform API](services/platform-api/README.md)
**PHP/Kohana** | 18 docs | 54,109 words

The core REST API service for the telecommunications platform, handling user management, billing, dial plans, SIP trunks, call routing, and device provisioning.

- [API Reference](services/platform-api/docs/api/README.md) - Complete endpoint documentation
- [Data Models](services/platform-api/docs/models/README.md) - Schema definitions
- [Configuration](services/platform-api/docs/configuration.md) - Environment setup

---

### [Platform Service Gateway](services/platform-service-gateway/README.md)
**PHP/Kohana** | 23 docs | 64,481 words

Central gateway service for routing and orchestrating requests across platform services.

- [API Reference](services/platform-service-gateway/docs/api/README.md)
- [Architecture](services/platform-service-gateway/docs/architecture.md)

---

### [Disposition Gateway API](services/platform-dgapi/README.md)
**PHP/Kohana** | 14 docs | 30,493 words

REST API service orchestrating task disposition workflows across SMS, email, voicemail, CDR, and callback channels.

- [API Reference](services/platform-dgapi/docs/api/README.md)
- [Configuration](services/platform-dgapi/docs/configuration.md)

---

### [Insight Category API](services/aws-insight-category-api/README.md)
**AWS Lambda/TypeScript** | 9 docs | 12,844 words

Serverless API for managing voice analytics categorization, enabling customers to create and apply call analysis categories.

- [Categories API](services/aws-insight-category-api/docs/api/categories.md)
- [Templates API](services/aws-insight-category-api/docs/api/templates.md)

---

## Frontend Applications

Web applications and user interfaces.

### [Freedom Web](services/freedom-freedom-web/README.md)
**React/TypeScript** | 9 docs | 26,879 words

Web application for the Freedom telephony platform.

- [Architecture](services/freedom-freedom-web/docs/architecture.md)
- [Components](services/freedom-freedom-web/docs/components.md)

---

### [FreedomCTI Client](services/platform-cti-client/README.md)
**Salesforce Lightning** | 17 docs | 38,747 words

Browser-based Computer Telephony Integration (CTI) client for seamless Salesforce integration.

- [Architecture](services/platform-cti-client/docs/architecture.md)
- [WebSocket Integration](services/platform-cti-client/docs/websocket.md)

---

### [Insight Categorisation UI](services/insight-insight-category-ui/README.md)
**React/TypeScript/Redux** | 15 docs | 26,339 words

React frontend for Insight voice analytics categorization, built with Feature-Sliced Design architecture.

- [Architecture](services/insight-insight-category-ui/docs/architecture.md)
- [State Management](services/insight-insight-category-ui/docs/state.md)

---

### [Natterbox Wallboards](services/natterbox-wallboards/README.md)
**React/Auth0** | 14 docs | 32,141 words

Real-time call center dashboard for displaying metrics, agent statuses, and queue information within Salesforce.

- [Architecture](services/natterbox-wallboards/docs/architecture.md)
- [Configuration](services/natterbox-wallboards/docs/configuration.md)

---

## Infrastructure (Terraform)

Infrastructure as Code modules for AWS deployments.

### [AWS Bedrock Module](services/aws-terraform-bedrock/README.md)
**Terraform** | 8 docs | 19,560 words

Terraform module for deploying AWS Bedrock generative AI services with multi-region support and safety guardrails.

- [Architecture](services/aws-terraform-bedrock/docs/architecture.md)
- [Guardrails](services/aws-terraform-bedrock/docs/guardrails.md)
- [Variables](services/aws-terraform-bedrock/docs/variables.md)

---

### [API Gateway Module](services/aws-terraform-api-gateway/README.md)
**Terraform** | 4 docs | 6,533 words

Terraform module for provisioning AWS API Gateway with multi-region support.

- [Architecture](services/aws-terraform-api-gateway/docs/architecture.md)

---

### [ECS Module](services/aws-terraform-ecs/README.md)
**Terraform** | 6 docs | 10,637 words

Terraform module for deploying containerized services on Amazon ECS.

- [Architecture](services/aws-terraform-ecs/docs/architecture.md)
- [Variables](services/aws-terraform-ecs/docs/variables.md)

---

### [Callflow Service Module](services/aws-terraform-callflow-service/README.md)
**Terraform** | 6 docs | 13,399 words

Serverless architecture for storing and retrieving call flow events using API Gateway, Lambda, and S3.

- [Architecture](services/aws-terraform-callflow-service/docs/architecture.md)

---

## Microservices

Backend services, pipelines, and processors.

### [Omnichannel Service](services/omnichannel-omniservice/README.md)
**TypeScript/Node.js/Lambda** | 23 docs | 53,188 words

TypeScript monorepo implementing an omnichannel messaging pipeline for inbound/outbound message routing across multiple carriers.

- [Architecture](services/omnichannel-omniservice/docs/architecture.md)
- [Lambdas](services/omnichannel-omniservice/docs/lambdas/README.md)
- [Models](services/omnichannel-omniservice/docs/models/README.md)

---

### [CDC Pipeline](services/cdc-pipeline/README.md)
**TypeScript/Lambda/EventBridge** | 13 docs | 37,252 words

Change Data Capture pipeline capturing real-time database changes and distributing events through AWS EventBridge.

- [Architecture](services/cdc-pipeline/docs/architecture.md)
- [Lambda Functions](services/cdc-pipeline/docs/lambdas/README.md)
- [Event Models](services/cdc-pipeline/docs/models/events.md)

---

### [CAI Service](services/cai-service/README.md)
**TypeScript/Node.js** | 16 docs | 34,389 words

Conversational AI service for voice analytics and natural language processing.

- [Architecture](services/cai-service/docs/architecture.md)
- [API Reference](services/cai-service/docs/api/README.md)

---

### [Bedrock Metrics Aggregator](services/bedrock-metrics-aggregator/README.md)
**AWS Lambda** | 7 docs | 14,520 words

Lambda service for aggregating and processing Amazon Bedrock usage metrics and CloudWatch data.

- [Architecture](services/bedrock-metrics-aggregator/docs/architecture.md)
- [Configuration](services/bedrock-metrics-aggregator/docs/configuration.md)

---

### [Natterbox Routing Policies](services/natterbox-routing-policies/README.md)
**React/TypeScript** | 10 docs | 20,203 words

Call routing policy management application.

- [Architecture](services/natterbox-routing-policies/docs/architecture.md)

---

## Schema & Data

Database schemas, telemetry, and data services.

### [Sapien](services/sapien/README.md)
**PHP** | 18 docs | 31,249 words

Core business logic and data processing service.

- [Architecture](services/sapien/docs/architecture.md)
- [Models](services/sapien/docs/models/README.md)

---

### [Schema API](services/schema-api/README.md)
**PostgreSQL** | 9 docs | 16,532 words

Database migration repository defining all data models and schema structures for the VoIP/telecom platform.

- [Migration Guide](services/schema-api/docs/migration-guide.md)
- [Models](services/schema-api/docs/models/README.md)

---

### [NBTelemetry](services/nbtelemetry/README.md)
**PHP/Multi-Language** | 12 docs | 20,571 words

Enterprise telemetry service for transcription and call analysis, integrating with NLE providers.

- [Architecture](services/nbtelemetry/docs/architecture.md)
- [Configuration](services/nbtelemetry/docs/configuration.md)

---

## Statistics

| Metric | Value |
|--------|-------|
| **Total Services** | 20 |
| **Total Documents** | 251 |
| **Total Words** | 564,047 |
| **Generation Method** | AI-powered code analysis |
| **Model** | Claude Opus 4.5 (Premium) |

### Documents by Category

| Category | Services | Documents | Words |
|----------|----------|-----------|-------|
| Core APIs | 4 | 64 | 161,927 |
| Frontend Applications | 4 | 55 | 124,106 |
| Infrastructure | 4 | 24 | 50,129 |
| Microservices | 5 | 69 | 159,552 |
| Schema & Data | 3 | 39 | 68,352 |

---

## About This Documentation

This documentation was auto-generated using an AI-powered documentation agent that:

1. **Analyzes source code** using Claude to semantically understand APIs, models, and configurations
2. **Generates intelligent structure** by letting AI decide how to organize documents based on content
3. **Writes comprehensive docs** with detailed API references, architecture diagrams, and examples
4. **Creates topic-specific files** instead of monolithic documents for better navigation

### Technology Stack

- **Analysis**: Claude Opus 4.5 for deep code understanding
- **Writing**: Claude Opus 4.5 for comprehensive documentation
- **Languages Supported**: PHP, TypeScript, Python, Go, Terraform
- **Frameworks**: Kohana, React, Node.js, AWS Lambda

---

*Generated on January 22, 2026*
