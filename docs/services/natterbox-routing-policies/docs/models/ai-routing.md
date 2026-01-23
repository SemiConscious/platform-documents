# AI Routing Models

This document covers AI-related data models for intelligent routing configurations in the Natterbox Routing Policies service. These models enable sophisticated AI-powered call handling, information collection, and intelligent routing decisions.

## Overview

The AI routing system provides several key capabilities:
- **AI Agents**: Configure and manage AI-powered agents for call handling
- **Intelligent Routing**: Route calls based on AI-determined intent
- **Information Collection**: Gather structured data from callers using AI
- **AI Responses**: Generate contextual responses using AI
- **AI Personas**: Define personality and voice characteristics for AI interactions
- **Knowledge Bases**: Integrate AI with knowledge repositories

## Entity Relationship Diagram

```
┌─────────────────────┐
│   AgentInstanceName │
└──────────┬──────────┘
           │ referenced by
           ▼
┌──────────────────────────────────────────────────────────────┐
│                    AI Components                              │
├──────────────┬──────────────┬─────────────┬─────────────────┤
│   AIAgent    │  AIGetInfo   │  AIRouting  │   AIResponse    │
│              │              │             │                  │
│              │              │             │                  │
└──────────────┴──────────────┴─────────────┴─────────────────┘
           │              │           │
           │              │           │
           ▼              ▼           ▼
┌──────────────────────────────────────────────────────────────┐
│                    Variable Types                             │
├────────────┬────────────┬──────────────┬────────────────────┤
│StringVar   │ NumberVar  │ DateVariable │ SelectionVariable  │
│BooleanVar  │            │              │ MultiSelectionVar  │
└────────────┴────────────┴──────────────┴────────────────────┘
           │
           │ extends
           ▼
    ┌──────────────┐
    │ BaseVariable │
    └──────────────┘

┌─────────────────────┐     ┌─────────────────────┐
│ HumanEscalationLink │◄────│ Multiple AI Models  │
└─────────────────────┘     └─────────────────────┘

┌─────────────────────┐
│   AiPersonaSchema   │
├─────────────────────┤
│  ┌───────────────┐  │
│  │  NudgePrompt  │  │
│  └───────────────┘  │
│  ┌───────────────┐  │
│  │BackgroundNoise│  │
│  └───────────────┘  │
│  ┌───────────────┐  │
│  │    VoiceId    │  │
│  └───────────────┘  │
└─────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐
│  AiKnowledgeSchema  │────►│ MetaPropertyFilter  │
└─────────────────────┘     └─────────────────────┘
```

---

## Core AI Components

### AgentInstanceName

A schema for validating and storing AI agent instance name references used across multiple AI components.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| value | string | Yes | Instance name value used to reference the AI agent |

**Validation Rules:**
- Must match the agent instance naming pattern
- Used as a reference key across AI components

**Example:**
```json
{
  "value": "sales_support_agent_v1"
}
```

---

### AIAgent

Configuration schema for AI Agent components that handle intelligent call interactions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| agentInstanceName | AGENT_INSTANCE_NAME | Yes | Agent instance name reference |
| agentId | string | Yes | Agent ID matching agentIdRegex pattern |
| agentVersion | string | Yes | Agent version matching agentVersionRegex pattern |
| toolResultSetName | string | No | Tool result set name matching agentKeyRegex pattern |
| userGreetingPrompt | string | No | Welcome message (max 4096 chars) |
| componentVersion | number | Yes | Component version (1 or 2, preprocessed from 'V1'/'V2') |
| tokens | array | No | Array of key-value token pairs |

**Validation Rules:**
- `agentId` must match the defined agent ID regex pattern
- `agentVersion` must match the defined version regex pattern
- `userGreetingPrompt` maximum length: 4096 characters
- `componentVersion` accepts values 1 or 2 (preprocessed from string 'V1' or 'V2')
- `tokens` array contains objects with `key` and `value` string properties

**Example:**
```json
{
  "agentInstanceName": "customer_service_agent",
  "agentId": "agt_abc123def456",
  "agentVersion": "2.1.0",
  "toolResultSetName": "customer_tools",
  "userGreetingPrompt": "Hello! I'm your virtual assistant. How can I help you today?",
  "componentVersion": 2,
  "tokens": [
    {
      "key": "company_name",
      "value": "Acme Corporation"
    },
    {
      "key": "support_hours",
      "value": "9 AM to 5 PM EST"
    }
  ]
}
```

**Relationships:**
- References `AgentInstanceName` for instance identification
- Used by routing policies to invoke AI-powered call handling

---

### AIRouting

Intelligent call routing component that uses AI to determine the best route for incoming calls based on caller intent.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| userGreetingPrompt | string | No | Welcome message (max 4096 chars) |
| goalPrompt | string | No | Goal prompt message (max 4096 chars) |
| systemPrompt | string | No | System prompt (max 12288 chars) |
| humanEscalationLink | HumanEscalationLink | No | Human escalation configuration |
| routeIdentifiedConfirmPrompt | string | No | Route identification confirmation prompt (max 4096 chars) |
| domainSpecificKnowledge | string | No | Domain specific knowledge (max 8192 chars) |
| variables | array | Yes | Array of route variables (AIRoutingVariable) |
| agentInstanceName | AGENT_INSTANCE_NAME | Yes | Agent instance name reference |
| userPromptPrefix | string | No | User prompt prefix (max 4096 chars) |

**Validation Rules:**
- `userGreetingPrompt`: max 4096 characters
- `goalPrompt`: max 4096 characters
- `systemPrompt`: max 12288 characters
- `routeIdentifiedConfirmPrompt`: max 4096 characters
- `domainSpecificKnowledge`: max 8192 characters
- `userPromptPrefix`: max 4096 characters
- `variables` must contain at least one routing variable

**Example:**
```json
{
  "agentInstanceName": "routing_agent",
  "userGreetingPrompt": "Welcome to Acme Support. Please describe what you need help with.",
  "goalPrompt": "Determine the caller's intent and route them to the appropriate department.",
  "systemPrompt": "You are a routing assistant for Acme Corporation. Analyze the caller's request and determine which department can best assist them. Available departments include Sales, Technical Support, Billing, and General Inquiries.",
  "routeIdentifiedConfirmPrompt": "I understand you need help with {department}. Let me connect you to the right team.",
  "domainSpecificKnowledge": "Sales handles new purchases and upgrades. Technical Support handles product issues and troubleshooting. Billing handles invoices, payments, and account changes.",
  "userPromptPrefix": "Customer said: ",
  "humanEscalationLink": {
    "confirmPrompt": "I'll connect you with a human representative right away.",
    "targetNode": "human_operator_queue"
  },
  "variables": [
    {
      "name": "sales_department",
      "description": "Route for sales inquiries, new purchases, and upgrades",
      "targetNode": "sales_queue"
    },
    {
      "name": "technical_support",
      "description": "Route for technical issues and troubleshooting",
      "targetNode": "tech_support_queue"
    },
    {
      "name": "billing_department",
      "description": "Route for billing, payments, and account inquiries",
      "targetNode": "billing_queue"
    }
  ]
}
```

**Relationships:**
- Contains `AIRoutingVariable` array for route definitions
- References `HumanEscalationLink` for fallback to human agents
- Uses `AgentInstanceName` for agent identification

**Use Cases:**
- Intelligent IVR replacement
- Intent-based call routing
- Multi-department call centers
- Customer service automation

---

### AIRoutingVariable

Variable schema defining individual routes for the AI Routing component.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Route name (starts with letter, max 257 chars) |
| description | string | Yes | Route description for AI understanding |
| targetNode | string | Yes | Target node matching targetNameRegex pattern |

**Validation Rules:**
- `name` must start with a letter
- `name` maximum length: 257 characters
- `targetNode` must match the target name regex pattern

**Example:**
```json
{
  "name": "emergency_support",
  "description": "Route for urgent issues requiring immediate attention, system outages, or critical problems",
  "targetNode": "priority_queue_emergency"
}
```

**Relationships:**
- Used exclusively within `AIRouting.variables` array
- `targetNode` references routing policy nodes

---

### AIGetInfo

Component for collecting structured information from callers using AI-powered conversation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| agentInstanceName | AGENT_INSTANCE_NAME | Yes | Agent instance name reference |
| goalPrompt | string | No | Scope/goal prompt (max 4096 chars) |
| systemPrompt | string | No | System prompt (max 12288 chars) |
| userGreetingPrompt | string | No | User greeting prompt (max 4096 chars) |
| infoCollectedConfirmPrompt | string | No | Info collected confirmation prompt (max 4096 chars) |
| humanEscalationLink | HumanEscalationLink | No | Human escalation configuration |
| userPromptPrefix | string | No | User prompt prefix (max 4096 chars) |
| variables | array | Yes | Array of variables to collect (min 1) |

**Validation Rules:**
- `goalPrompt`: max 4096 characters
- `systemPrompt`: max 12288 characters
- `userGreetingPrompt`: max 4096 characters
- `infoCollectedConfirmPrompt`: max 4096 characters
- `userPromptPrefix`: max 4096 characters
- `variables` array must contain at least one variable

**Example:**
```json
{
  "agentInstanceName": "info_collector_agent",
  "goalPrompt": "Collect the caller's contact information and appointment preferences",
  "systemPrompt": "You are a scheduling assistant. Collect the required information naturally through conversation. Be polite and confirm details when collected.",
  "userGreetingPrompt": "Hello! I can help you schedule an appointment. Let me get some information from you.",
  "infoCollectedConfirmPrompt": "Great! I have all the information I need. Your appointment is scheduled for {appointment_date}.",
  "userPromptPrefix": "Caller: ",
  "humanEscalationLink": {
    "confirmPrompt": "Let me transfer you to a scheduling specialist.",
    "targetNode": "scheduling_team"
  },
  "variables": [
    {
      "name": "customer_name",
      "description": "Full name of the customer",
      "type": "STRING",
      "pattern": "^[A-Za-z\\s]{2,100}$"
    },
    {
      "name": "appointment_date",
      "description": "Preferred appointment date",
      "type": "DATE",
      "outputFormat": "YYYY-MM-DD"
    },
    {
      "name": "appointment_type",
      "description": "Type of appointment",
      "type": "SELECTION",
      "enum": "[\"Consultation\", \"Follow-up\", \"New Patient\"]"
    }
  ]
}
```

**Relationships:**
- Contains various variable types (BaseVariable derivatives)
- References `HumanEscalationLink` for escalation
- Uses `AgentInstanceName` for agent identification

---

### AIResponse

Component for generating AI-powered responses based on prompts and context.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| systemPrompt | string | No | System prompt (max 4096 chars) |
| userPrompt | string | Yes | User prompt (1-4096 chars) |
| treatUserPromptAsLiteral | boolean | No | Whether to treat user prompt as literal |
| allowLiteralLanguageTranslation | boolean | No | Allow literal language translation |
| agentInstanceName | AGENT_INSTANCE_NAME | Yes | Agent instance name reference |
| disableInterruptDetection | boolean | No | Disable interrupt detection |

**Validation Rules:**
- `systemPrompt`: max 4096 characters
- `userPrompt`: min 1, max 4096 characters (required)

**Example:**
```json
{
  "agentInstanceName": "response_generator",
  "systemPrompt": "You are a helpful customer service assistant. Provide clear, concise, and professional responses.",
  "userPrompt": "Generate a response confirming the customer's order number {order_id} has shipped.",
  "treatUserPromptAsLiteral": false,
  "allowLiteralLanguageTranslation": true,
  "disableInterruptDetection": false
}
```

**Use Cases:**
- Dynamic response generation
- Contextual message creation
- Personalized call scripts

---

### AIInstruction

Component for processing AI instructions and storing results in macros.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| agentInstanceName | AGENT_INSTANCE_NAME | Yes | Agent instance name reference |
| userPrompt | string | Yes | Instruction prompt (1-49512 chars) |
| outputMacroName | string | Yes | Output macro name matching macroNameRegex pattern |
| systemPrompt | string | No | System prompt (max 49512 chars) |

**Validation Rules:**
- `userPrompt`: min 1, max 49512 characters
- `systemPrompt`: max 49512 characters
- `outputMacroName` must match the macro name regex pattern

**Example:**
```json
{
  "agentInstanceName": "instruction_processor",
  "systemPrompt": "You are an expert at extracting and summarizing key information from conversations.",
  "userPrompt": "Analyze the following conversation transcript and extract: 1) Main topic, 2) Customer sentiment, 3) Action items. Transcript: {conversation_transcript}",
  "outputMacroName": "analysis_result"
}
```

**Use Cases:**
- Conversation analysis
- Data extraction from transcripts
- Sentiment analysis
- Automated note generation

---

### AISettings

Configuration schema for AI guard rails and safety settings.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| guardRails | GuardRails \| null | No | Guard rails configuration object or null |

**Example:**
```json
{
  "guardRails": {
    "guardRailPolicyId": "policy_content_filter_v2",
    "streamingMode": "buffered"
  }
}
```

**Relationships:**
- Contains `GuardRails` configuration

---

### GuardRails

Guard rails configuration for AI safety and content filtering.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| guardRailPolicyId | string | No | Guard rail policy ID (transforms 'NONE' to null) |
| streamingMode | string | No | Streaming mode (transforms 'NONE' to null) |

**Validation Rules:**
- Setting `guardRailPolicyId` to 'NONE' transforms to null
- Setting `streamingMode` to 'NONE' transforms to null

**Example:**
```json
{
  "guardRailPolicyId": "content_safety_strict",
  "streamingMode": "real_time"
}
```

---

## Variable Types

### BaseVariable

Base schema for AI Get Info variables that all specific variable types extend.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Variable name matching variableNameRegex pattern |
| description | string | Yes | Variable description (min 1 char) |
| type | enum | Yes | Variable type from AI_GET_INFO.TYPE_SELECT values |

**Validation Rules:**
- `name` must match the variable name regex pattern
- `description` minimum length: 1 character
- `type` must be one of the allowed AI_GET_INFO type values

---

### StringVariable

String type variable with regex pattern validation for text data collection.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Variable name matching variableNameRegex pattern |
| description | string | Yes | Variable description (min 1 char) |
| type | literal | Yes | Type discriminator: 'STRING' |
| pattern | string | No | Regex pattern for validation (must be valid regex) |

**Validation Rules:**
- `type` must be exactly 'STRING'
- `pattern` must be a valid regular expression if provided

**Example:**
```json
{
  "name": "email_address",
  "description": "Customer's email address for confirmation",
  "type": "STRING",
  "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
}
```

---

### NumberVariable

Number type variable with min/max range validation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Variable name matching variableNameRegex pattern |
| description | string | Yes | Variable description (min 1 char) |
| type | literal | Yes | Type discriminator: 'NUMBER' |
| minimum | number | No | Minimum value (must be <= maximum) |
| maximum | number | No | Maximum value |

**Validation Rules:**
- `type` must be exactly 'NUMBER'
- `minimum` must be less than or equal to `maximum` when both are provided

**Example:**
```json
{
  "name": "age",
  "description": "Customer's age for eligibility verification",
  "type": "NUMBER",
  "minimum": 18,
  "maximum": 120
}
```

---

### DateVariable

Date type variable with configurable output format.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Variable name matching variableNameRegex pattern |
| description | string | Yes | Variable description (min 1 char) |
| type | literal | Yes | Type discriminator: 'DATE' |
| outputFormat | string | No | Date output format |

**Validation Rules:**
- `type` must be exactly 'DATE'

**Example:**
```json
{
  "name": "birth_date",
  "description": "Customer's date of birth",
  "type": "DATE",
  "outputFormat": "MM/DD/YYYY"
}
```

---

### BooleanVariable

Boolean type variable for yes/no or true/false responses.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Variable name matching variableNameRegex pattern |
| description | string | Yes | Variable description (min 1 char) |
| type | literal | Yes | Type discriminator: 'BOOLEAN' |
| outputFormat | string | No | Boolean output format |

**Validation Rules:**
- `type` must be exactly 'BOOLEAN'

**Example:**
```json
{
  "name": "consent_given",
  "description": "Whether the customer consents to marketing communications",
  "type": "BOOLEAN",
  "outputFormat": "yes/no"
}
```

---

### SelectionVariable

Single selection variable for choosing from predefined options.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Variable name matching variableNameRegex pattern |
| description | string | Yes | Variable description (min 1 char) |
| type | literal | Yes | Type discriminator: 'SELECTION' |
| enum | string | Yes | Selection array as string |

**Validation Rules:**
- `type` must be exactly 'SELECTION'
- `enum` should be a stringified JSON array of options

**Example:**
```json
{
  "name": "preferred_language",
  "description": "Customer's preferred language for communication",
  "type": "SELECTION",
  "enum": "[\"English\", \"Spanish\", \"French\", \"German\"]"
}
```

---

### MultiSelectionVariable

Multi-selection variable for choosing multiple options from a predefined list.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Variable name matching variableNameRegex pattern |
| description | string | Yes | Variable description (min 1 char) |
| type | literal | Yes | Type discriminator: 'MULTI_SELECTION' |
| enum | string | Yes | Selection array as string |

**Validation Rules:**
- `type` must be exactly 'MULTI_SELECTION'
- `enum` should be a stringified JSON array of options

**Example:**
```json
{
  "name": "services_interested",
  "description": "Services the customer is interested in learning about",
  "type": "MULTI_SELECTION",
  "enum": "[\"Consulting\", \"Implementation\", \"Support\", \"Training\", \"Custom Development\"]"
}
```

---

## Support Models

### HumanEscalationLink

Configuration for escalating AI conversations to human agents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| confirmPrompt | string | No | Human escalation confirm prompt (max 8192 chars) |
| targetNode | string | Yes | Human escalation target node (min 1 char) |

**Validation Rules:**
- `confirmPrompt`: max 8192 characters
- `targetNode`: min 1 character

**Example:**
```json
{
  "confirmPrompt": "I understand you'd like to speak with a human representative. Let me transfer you now. Please hold for a moment.",
  "targetNode": "human_agent_queue_priority"
}
```

**Relationships:**
- Used by `AIRouting`, `AIGetInfo`, `AiSkillsSchema`, and `AiKnowledgeSchema`

---

## AI Persona Configuration

### AiPersonaSchema

Complete AI persona configuration including voice settings and behavioral parameters.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| assistantName | string | Yes | Name of the AI assistant |
| persona | string | No | Persona description |
| tone | string | No | Tone of conversation |
| humanEscalationPrompt | string | No | Human escalation prompt |
| clearMemory | boolean | No | Clear conversation memory |
| defaultLanguage | string | No | Default language code |
| autoDetectLanguage | boolean | No | Auto-detect language |
| nudgePrompt | NudgePrompt | No | Nudge prompt configuration |
| backgroundNoise | BackgroundNoise | No | Background noise settings |
| voiceIds | array | No | Array of voice configurations (VoiceId) |
| normalizationPromptIds | array | No | Normalization prompt configurations |
| enableNormalizationPrompts | boolean | No | Enable normalization prompts |
| defaultVoice | string | No | Default voice ID |

**Example:**
```json
{
  "assistantName": "Alex",
  "persona": "A friendly and professional customer service representative with expertise in telecommunications",
  "tone": "professional yet warm and approachable",
  "humanEscalationPrompt": "I'll connect you with a human specialist who can better assist you.",
  "clearMemory": false,
  "defaultLanguage": "en-US",
  "autoDetectLanguage": true,
  "defaultVoice": "voice_alex_en_us",
  "enableNormalizationPrompts": true,
  "nudgePrompt": {
    "timeout": 10,
    "prompt": "Are you still there? I'm happy to help if you have any questions."
  },
  "backgroundNoise": {
    "backgroundNoiseId": "office_ambient",
    "backgroundNoiseLevel": 15
  },
  "voiceIds": [
    {
      "voiceId": "voice_alex_en_us",
      "language": "en-US"
    },
    {
      "voiceId": "voice_alex_es_mx",
      "language": "es-MX"
    }
  ],
  "normalizationPromptIds": [
    {
      "language": "en-US",
      "promptId": "normalize_en_us_v2"
    }
  ]
}
```

**Relationships:**
- Contains `NudgePrompt`, `BackgroundNoise`, `VoiceId`, and `NormalizationPromptId`

---

### BaseAiPersonaSchema

Base configuration schema for AI persona without voice-specific settings.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| assistantName | string | Yes | Name of the AI assistant |
| persona | string | No | Persona description |
| tone | string | No | Tone of conversation |
| humanEscalationPrompt | string | No | Human escalation prompt |
| clearMemory | boolean | No | Clear conversation memory |
| defaultLanguage | string | No | Default language code |
| autoDetectLanguage | boolean | No | Auto-detect language |

**Example:**
```json
{
  "assistantName": "Jordan",
  "persona": "A knowledgeable technical support specialist",
  "tone": "patient and technical",
  "humanEscalationPrompt": "Let me transfer you to a senior technician.",
  "clearMemory": true,
  "defaultLanguage": "en-GB",
  "autoDetectLanguage": false
}
```

---

### NudgePrompt

Configuration for prompting inactive callers to continue the conversation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| timeout | integer | Yes | Timeout in seconds before nudge |
| prompt | string | Yes | Nudge prompt text to speak |

**Example:**
```json
{
  "timeout": 15,
  "prompt": "I'm still here if you need any help. Feel free to ask me anything."
}
```

---

### BackgroundNoise

Configuration for ambient background noise during AI conversations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| backgroundNoiseId | string | Yes | Background noise identifier |
| backgroundNoiseLevel | number | Yes | Noise level percentage (0-100) |

**Example:**
```json
{
  "backgroundNoiseId": "call_center_ambient",
  "backgroundNoiseLevel": 20
}
```

---

### VoiceId

Voice configuration with language association.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| voiceId | string | Yes | Voice identifier |
| language | string | Yes | Language code |

**Example:**
```json
{
  "voiceId": "voice_neural_sarah",
  "language": "en-US"
}
```

---

### NormalizationPromptId

Normalization prompt configuration per language for speech processing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| language | string | Yes | Language code |
| promptId | string | Yes | Prompt identifier |

**Example:**
```json
{
  "language": "en-US",
  "promptId": "normalization_default_en"
}
```

---

## Specialized AI Components

### AiSkillsSchema

AI skills collection configuration for capability-based interactions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| agentInstanceName | string | Yes | Agent instance name |
| domainSpecificKnowledge | string | No | Domain specific knowledge |
| skillsCollectedConfirmPrompt | string | No | Skills collected confirmation prompt |
| systemPrompt | string | No | System prompt for advanced mode |
| advanced | boolean | No | Enable advanced mode |
| userGreetingPrompt | string | No | User greeting prompt |
| humanEscalationLink | HumanEscalationLink | No | Human escalation link configuration |
| userPromptPrefix | string | No | User prompt prefix |

**Example:**
```json
{
  "agentInstanceName": "skills_agent",
  "domainSpecificKnowledge": "Product catalog includes: Widget A, Widget B, Service Package Standard, Service Package Premium",
  "skillsCollectedConfirmPrompt": "Based on what you've told me, I can help you with {identified_skills}.",
  "systemPrompt": "You are a product specialist. Identify customer needs and match them with appropriate products and services.",
  "advanced": true,
  "userGreetingPrompt": "Hello! I can help you find the right product or service for your needs.",
  "userPromptPrefix": "Customer inquiry: ",
  "humanEscalationLink": {
    "confirmPrompt": "I'll connect you with a product specialist.",
    "targetNode": "product_specialist_queue"
  }
}
```

---

### AiVoicemailSchema

AI voicemail configuration for intelligent voicemail handling.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| agentInstanceName | string | Yes | Agent instance name |
| systemPrompt | string | No | System prompt |
| vmBoxName | string | Yes | Voicemail box name |
| vmBoxEmailAddress | string | No | Email address for voicemail notifications |
| vmBoxSmsAddress | string | No | SMS address for voicemail notifications |
| vmBoxSmsSenderAddress | string | No | SMS sender address |
| callerName | string | No | Caller name |
| sendCallerSms | boolean | No | Send SMS notification to caller |
| userPromptPrefix | string | No | User prompt prefix |

**Example:**
```json
{
  "agentInstanceName": "voicemail_agent",
  "systemPrompt": "You are a voicemail assistant. Guide the caller to leave a clear and complete message.",
  "vmBoxName": "sales_voicemail",
  "vmBoxEmailAddress": "sales-voicemail@company.com",
  "vmBoxSmsAddress": "+14155551234",
  "vmBoxSmsSenderAddress": "+14155550000",
  "callerName": "{caller_name}",
  "sendCallerSms": true,
  "userPromptPrefix": "Message: "
}
```

---

### AiKnowledgeSchema

AI knowledge base configuration for intelligent information retrieval.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| domainSpecificKnowledge | string | No | Domain specific knowledge |
| goalPrompt | string | No | Goal prompt |
| knowledgeBaseId | string | Yes | Knowledge base identifier |
| knowledgeCompleteConfirmPrompt | string | No | Knowledge completion confirmation prompt |
| metaPropertyFilter | array | No | Meta property filters (MetaPropertyFilter) |
| queryThreshold | number | No | Query threshold for relevance |
| systemPrompt | string | No | System prompt |
| tagFilter | array | No | Tag filters (string[]) |
| userGreetingPrompt | string | No | User greeting prompt |
| humanEscalationLink | HumanEscalationLink | No | Human escalation link configuration |
| agentInstanceName | string | Yes | Agent instance name |
| userPromptPrefix | string | No | User prompt prefix |
| knowledgeBaseToolContextText | string | No | Knowledge base tool context text |
| intentCompletionActions | string | No | Intent completion actions |
| embeddingLanguageType | string | No | Embedding language type |

**Example:**
```json
{
  "agentInstanceName": "knowledge_agent",
  "knowledgeBaseId": "kb_product_documentation",
  "domainSpecificKnowledge": "Focus on consumer electronics including smartphones, tablets, and accessories.",
  "goalPrompt": "Help customers find answers to their product questions using the knowledge base.",
  "systemPrompt": "You are a knowledgeable product support specialist. Use the knowledge base to provide accurate, helpful answers.",
  "userGreetingPrompt": "Hello! I can help answer your product questions. What would you like to know?",
  "knowledgeCompleteConfirmPrompt": "I hope that answers your question. Is there anything else I can help you with?",
  "queryThreshold": 0.75,
  "embeddingLanguageType": "en",
  "userPromptPrefix": "Question: ",
  "knowledgeBaseToolContextText": "Search product documentation and FAQs",
  "tagFilter": ["consumer", "electronics", "support"],
  "metaPropertyFilter": [
    {
      "key": "product_line",
      "value": "smartphones"
    },
    {
      "key": "status",
      "value": "active"
    }
  ],
  "humanEscalationLink": {
    "confirmPrompt": "I'll connect you with a product specialist for more detailed assistance.",
    "targetNode": "product_support_queue"
  },
  "intentCompletionActions": "log_interaction"
}
```

**Relationships:**
- Contains `MetaPropertyFilter` array for knowledge filtering
- Uses `HumanEscalationLink` for escalation

---

### MetaPropertyFilter

Key-value filter for knowledge base queries.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| key | string | Yes | Filter key/property name |
| value | string | Yes | Filter value |

**Example:**
```json
{
  "key": "category",
  "value": "troubleshooting"
}
```

---

### AiSupportChatSchema

AI support chat configuration for chat-based support interactions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Support chat identifier |
| preFillMacros | array | No | Pre-fill macro configurations |

**Example:**
```json
{
  "id": "support_chat_main",
  "preFillMacros": [
    {
      "macro": "customer_name",
      "value": "{sf_contact_name}"
    },
    {
      "macro": "account_number",
      "value": "{sf_account_id}"
    }
  ]
}
```

---

## Common Patterns and Use Cases

### Intent-Based Call Routing

Use `AIRouting` to analyze caller intent and route to appropriate queues:

```json
{
  "agentInstanceName": "intent_router",
  "goalPrompt": "Understand caller needs and route appropriately",
  "variables": [
    {"name": "sales", "description": "New purchases", "targetNode": "sales_q"},
    {"name": "support", "description": "Technical help", "targetNode": "support_q"},
    {"name": "billing", "description": "Account/billing", "targetNode": "billing_q"}
  ]
}
```

### Data Collection Flow

Use `AIGetInfo` to collect structured data:

```json
{
  "agentInstanceName": "data_collector",
  "variables": [
    {"name": "name", "type": "STRING", "description": "Full name"},
    {"name": "dob", "type": "DATE", "description": "Birth date"},
    {"name": "consent", "type": "BOOLEAN", "description": "Marketing consent"}
  ]
}
```

### Multi-Language Support

Configure `AiPersonaSchema` for multi-language:

```json
{
  "assistantName": "Global Assistant",
  "autoDetectLanguage": true,
  "defaultLanguage": "en-US",
  "voiceIds": [
    {"voiceId": "en_voice", "language": "en-US"},
    {"voiceId": "es_voice", "language": "es-ES"},
    {"voiceId": "fr_voice", "language": "fr-FR"}
  ]
}
```

---

## Related Documentation

- [Routing Variables](./routing-variables.md) - Variable types used in routing policies
- [Policy Records](./policy-records.md) - Policy record structures
- [Messaging Models](./messaging.md) - Messaging-related data models
- [Models Overview](./README.md) - Complete model index