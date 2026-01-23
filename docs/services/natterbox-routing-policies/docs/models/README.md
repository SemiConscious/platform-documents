# Data Models Overview

This document provides a comprehensive index of all data models used in the Natterbox Routing Policies service. The service manages intelligent call routing, AI-powered interactions, and messaging configurations within the Natterbox telephony platform.

## Architecture Overview

The Natterbox Routing Policies service employs a modular data architecture organized around four primary domains:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Natterbox Routing Policies                          │
├─────────────────┬─────────────────┬──────────────────┬─────────────────┤
│   AI Components │  Routing Logic  │  Messaging       │  Configuration  │
│                 │                 │                  │                 │
│  • AI Agents    │  • Variables    │  • Send Message  │  • AI Settings  │
│  • AI Routing   │  • Routing      │  • Templates     │  • Guard Rails  │
│  • AI Personas  │    Variables    │  • Contacts      │  • Personas     │
│  • AI Skills    │  • Target Nodes │  • Placeholders  │  • Voice IDs    │
└─────────────────┴─────────────────┴──────────────────┴─────────────────┘
```

## Model Categories

### AI Components (18 Models)

The largest category encompasses all artificial intelligence and conversational components used for intelligent call handling.

| Category | Models | Purpose |
|----------|--------|---------|
| **Core AI Agents** | `AIAgent`, `AIGetInfo`, `AIResponse`, `AIInstruction` | Primary AI interaction components |
| **AI Routing** | `AIRouting`, `AIRoutingVariable`, `HumanEscalationLink` | Intelligent call routing decisions |
| **AI Configuration** | `AISettings`, `GuardRails`, `AiPersonaSchema`, `BaseAiPersonaSchema` | AI behavior and safety settings |
| **Specialized AI** | `AiSkillsSchema`, `AiSupportChatSchema`, `AiVoicemailSchema`, `AiKnowledgeSchema` | Domain-specific AI capabilities |
| **Voice Settings** | `VoiceId`, `BackgroundNoise`, `NudgePrompt`, `NormalizationPromptId` | Voice and audio configuration |

→ See [AI Routing Models](./ai-routing.md) for detailed documentation

### Variable Definitions (8 Models)

Type-discriminated union schemas for collecting and validating user information during AI interactions.

| Model | Type Discriminator | Purpose |
|-------|-------------------|---------|
| `BaseVariable` | Base schema | Common fields for all variables |
| `StringVariable` | `STRING` | Text with regex validation |
| `NumberVariable` | `NUMBER` | Numeric values with min/max bounds |
| `DateVariable` | `DATE` | Date values with output formatting |
| `BooleanVariable` | `BOOLEAN` | True/false values |
| `SelectionVariable` | `SELECTION` | Single-choice selection |
| `MultiSelectionVariable` | `MULTI_SELECTION` | Multiple-choice selection |
| `AIRoutingVariable` | N/A | Route-specific variables |

→ See [Routing Variables](./routing-variables.md) for detailed documentation

### Messaging Models (5 Models)

Components for outbound messaging functionality including SMS and template-based communications.

| Model | Purpose |
|-------|---------|
| `SendMessageSchema` | Free-text message configuration |
| `SendTemplateSchema` | Template-based message with placeholders |
| `Contact` | Contact wrapper object |
| `Identity` | Contact identity details |
| `Placeholder` | Template variable substitution |

→ See [Messaging Models](./messaging.md) for detailed documentation

### Configuration & UI Models (3 Models)

Supporting models for UI components and system configuration.

| Model | Purpose |
|-------|---------|
| `CreateRecordTypeProps` | React component props for record creation |
| `AgentInstanceName` | Agent instance identifier wrapper |
| `MetaPropertyFilter` | Key-value filter for knowledge base queries |

→ See [Policy Records](./policy-records.md) for detailed documentation

## Entity Relationships

```
┌──────────────────┐     references      ┌─────────────────────┐
│  AIAgent         │────────────────────▶│  AgentInstanceName  │
│  AIRouting       │                     └─────────────────────┘
│  AIGetInfo       │                              │
│  AIResponse      │                              │
│  AIInstruction   │                              ▼
└──────────────────┘                     ┌─────────────────────┐
        │                                │  AiPersonaSchema    │
        │ contains                       └─────────────────────┘
        ▼                                         │
┌──────────────────┐                              │ configures
│  Variable Types  │                              ▼
│  ────────────────│                     ┌─────────────────────┐
│  StringVariable  │                     │  VoiceId            │
│  NumberVariable  │                     │  BackgroundNoise    │
│  DateVariable    │                     │  NudgePrompt        │
│  BooleanVariable │                     └─────────────────────┘
│  SelectionVar... │
└──────────────────┘

┌──────────────────┐     contains        ┌─────────────────────┐
│  AIRouting       │────────────────────▶│  HumanEscalationLink│
│  AiSkillsSchema  │                     └─────────────────────┘
│  AiKnowledgeSchema│
└──────────────────┘

┌──────────────────┐     contains        ┌─────────────────────┐
│  SendTemplate    │────────────────────▶│  Placeholder        │
│  Schema          │                     └─────────────────────┘
└──────────────────┘
        │
        │ contains
        ▼
┌──────────────────┐     contains        ┌─────────────────────┐
│  Contact         │────────────────────▶│  Identity           │
└──────────────────┘                     └─────────────────────┘
```

## Model Statistics

| Category | Count | Percentage |
|----------|-------|------------|
| AI Components | 18 | 53% |
| Variable Definitions | 8 | 24% |
| Messaging | 5 | 15% |
| Configuration & UI | 3 | 9% |
| **Total** | **34** | **100%** |

## Validation Patterns

The models employ several common validation patterns:

### Regex Patterns
- **Variable Names**: Must match `variableNameRegex` pattern
- **Agent IDs**: Must match `agentIdRegex` pattern  
- **Target Nodes**: Must match `targetNameRegex` pattern
- **Macro Names**: Must match `macroNameRegex` pattern

### Length Constraints
| Field Type | Typical Limit |
|------------|---------------|
| User Prompts | 4,096 characters |
| System Prompts | 12,288 - 49,512 characters |
| Domain Knowledge | 8,192 characters |
| Confirmation Prompts | 4,096 - 8,192 characters |

### Type Discrimination
Variable types use a discriminated union pattern with the `type` field serving as the discriminator for proper schema validation.

## Detailed Documentation

For complete field definitions, validation rules, and usage examples, refer to the topic-specific documentation:

| Document | Coverage |
|----------|----------|
| [Routing Variables](./routing-variables.md) | Variable type schemas and validation |
| [AI Routing](./ai-routing.md) | AI components and routing configuration |
| [Policy Records](./policy-records.md) | Record management and configuration |
| [Messaging](./messaging.md) | Message and template schemas |