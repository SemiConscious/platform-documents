# Conversational AI Service Overview

[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![API](https://img.shields.io/badge/API-REST%20%7C%20WebSocket-orange.svg)](#api-interfaces)

A comprehensive TypeScript Node.js monorepo providing enterprise-grade Conversational AI services with REST API, WebSocket, and data pipeline capabilities for executing AI prompts across multiple models and services.

---

## Table of Contents

- [Introduction](#introduction)
- [Key Features](#key-features)
- [Architecture Overview](#architecture-overview)
- [Package Structure](#package-structure)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [API Overview](#api-overview)
- [Configuration](#configuration)
- [Documentation Index](#documentation-index)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Introduction

The **cai-service** (Conversational AI Service) is a production-ready monorepo designed to streamline AI-powered conversational experiences. It provides a unified platform for executing prompts across multiple AI models (OpenAI, Anthropic, Google, and more), managing knowledge bases through intelligent document processing, and delivering real-time interactions via WebSocket connections.

Whether you're building a customer support chatbot, an intelligent document Q&A system, or a complex AI-driven application, cai-service provides the foundational infrastructure to accelerate your development.

### Who Is This For?

This service is designed for **developers** who need to:

- Integrate multiple AI models into their applications without vendor lock-in
- Build knowledge-augmented AI systems with document ingestion capabilities
- Create real-time conversational interfaces with WebSocket support
- Deploy scalable AI services in containerized environments

---

## Key Features

| Feature | Description |
|---------|-------------|
| 🤖 **Multi-Model AI Execution** | Execute prompts across OpenAI, Anthropic, Google Gemini, and other providers with a unified API |
| 🌐 **REST & WebSocket APIs** | Full-featured REST endpoints (3 documented) plus real-time WebSocket connections |
| 📄 **Document Processing** | Ingest PDFs, CSV, JSON, and TXT files with automatic parsing and chunking |
| 🕷️ **Web Crawling Pipeline** | Automated sitemap scraping and content extraction for knowledge base building |
| 🔍 **Vector Embeddings** | Generate and store embeddings for semantic search and knowledge indexing |
| 📊 **90+ Data Models** | Comprehensive type-safe data models for robust application development |

---

## Architecture Overview

The cai-service follows a modular monorepo architecture, separating concerns into distinct packages while maintaining shared utilities and type definitions.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Applications                       │
└─────────────────────┬───────────────────┬───────────────────────┘
                      │                   │
                      ▼                   ▼
              ┌───────────────┐   ┌───────────────┐
              │   REST API    │   │   WebSocket   │
              │   (Express)   │   │   (Socket.io) │
              └───────┬───────┘   └───────┬───────┘
                      │                   │
                      ▼                   ▼
              ┌─────────────────────────────────────┐
              │           Core Services              │
              │  ┌─────────┐  ┌─────────────────┐   │
              │  │ Prompt  │  │    Knowledge    │   │
              │  │ Engine  │  │    Manager      │   │
              │  └────┬────┘  └────────┬────────┘   │
              │       │                │            │
              │       ▼                ▼            │
              │  ┌─────────────────────────────┐   │
              │  │     Model Adapters          │   │
              │  │ (OpenAI, Anthropic, etc.)   │   │
              │  └─────────────────────────────┘   │
              └─────────────────────────────────────┘
                              │
                              ▼
              ┌─────────────────────────────────────┐
              │          Data Pipeline              │
              │  ┌─────────┐  ┌─────────────────┐   │
              │  │ Crawler │  │ Doc Processor   │   │
              │  └─────────┘  └─────────────────┘   │
              │       │                │            │
              │       ▼                ▼            │
              │  ┌─────────────────────────────┐   │
              │  │    Vector Store (Embeddings) │   │
              │  └─────────────────────────────┘   │
              └─────────────────────────────────────┘
```

For detailed architecture documentation, see [System Architecture](docs/architecture.md).

---

## Package Structure

The monorepo is organized into the following packages:

```
cai-service/
├── packages/
│   ├── api/                 # REST API service (Express.js)
│   ├── websocket/           # WebSocket service (Socket.io)
│   ├── pipeline/            # Data ingestion pipeline
│   ├── core/                # Shared business logic
│   ├── models/              # TypeScript data models (90+)
│   └── utils/               # Common utilities
├── docker/                  # Docker configurations
├── docs/                    # Documentation
├── scripts/                 # Build and deployment scripts
├── package.json             # Root package.json (workspaces)
├── tsconfig.json            # Base TypeScript configuration
└── docker-compose.yml       # Local development orchestration
```

| Package | Description | Entry Point |
|---------|-------------|-------------|
| `@cai/api` | REST API endpoints and middleware | `packages/api/src/index.ts` |
| `@cai/websocket` | Real-time WebSocket connections | `packages/websocket/src/index.ts` |
| `@cai/pipeline` | Document processing and crawling | `packages/pipeline/src/index.ts` |
| `@cai/core` | AI model adapters and prompt engine | `packages/core/src/index.ts` |
| `@cai/models` | TypeScript interfaces and types | `packages/models/src/index.ts` |
| `@cai/utils` | Shared helper functions | `packages/utils/src/index.ts` |

---

## Quick Start

### Prerequisites

- **Node.js** 18.x or higher
- **npm** 9.x or higher
- **Docker** and **Docker Compose** (for containerized deployment)
- API keys for your chosen AI providers

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd cai-service

# Install dependencies (all packages)
npm install

# Copy environment configuration
cp .env.example .env

# Configure your environment variables
# Edit .env with your API keys and settings
```

### Running with Docker (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Running Locally

```bash
# Build all packages
npm run build

# Start the API service
npm run start:api

# In a separate terminal, start the WebSocket service
npm run start:websocket

# Run the pipeline (for document ingestion)
npm run pipeline:start
```

### Verify Installation

```bash
# Health check endpoint
curl http://localhost:3000/health

# Expected response:
# {"status":"healthy","version":"1.0.0","timestamp":"2024-..."}
```

---

## Development Setup

### Setting Up Your Development Environment

```bash
# Install dependencies
npm install

# Run in development mode with hot reload
npm run dev

# Run tests
npm run test

# Run tests with coverage
npm run test:coverage

# Lint and format code
npm run lint
npm run format

# Type checking
npm run typecheck
```

### Workspace Commands

Since this is a monorepo using npm workspaces, you can run commands in specific packages:

```bash
# Run a command in a specific package
npm run build --workspace=@cai/api
npm run test --workspace=@cai/core

# Install a dependency in a specific package
npm install lodash --workspace=@cai/utils

# Install a dev dependency in a specific package
npm install -D jest --workspace=@cai/api
```

### Development Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start all services in development mode |
| `npm run build` | Build all packages |
| `npm run test` | Run test suite |
| `npm run lint` | Run ESLint |
| `npm run format` | Format code with Prettier |
| `npm run typecheck` | Run TypeScript type checking |
| `npm run clean` | Clean build artifacts |

---

## API Overview

The cai-service exposes 3 primary API endpoints:

### REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/prompt` | Execute an AI prompt |
| `POST` | `/api/v1/knowledge/ingest` | Ingest documents into knowledge base |
| `GET` | `/api/v1/health` | Service health check |

### Example: Execute a Prompt

```typescript
// Using fetch
const response = await fetch('http://localhost:3000/api/v1/prompt', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_API_KEY'
  },
  body: JSON.stringify({
    model: 'gpt-4',
    messages: [
      { role: 'system', content: 'You are a helpful assistant.' },
      { role: 'user', content: 'What is the capital of France?' }
    ],
    temperature: 0.7
  })
});

const data = await response.json();
console.log(data.response);
```

### WebSocket Connection

```typescript
import { io } from 'socket.io-client';

const socket = io('ws://localhost:3001', {
  auth: { token: 'YOUR_API_KEY' }
});

socket.on('connect', () => {
  console.log('Connected to CAI WebSocket');
  
  // Send a streaming prompt request
  socket.emit('prompt:stream', {
    model: 'gpt-4',
    messages: [{ role: 'user', content: 'Tell me a story' }]
  });
});

socket.on('prompt:chunk', (chunk) => {
  process.stdout.write(chunk.content);
});

socket.on('prompt:complete', (response) => {
  console.log('\n\nGeneration complete:', response.usage);
});
```

For complete API documentation, see [API Overview](docs/api/README.md).

---

## Configuration

The service uses 22 configuration variables managed through environment variables. Key configurations include:

```bash
# .env file

# Server Configuration
PORT=3000
WS_PORT=3001
NODE_ENV=development

# AI Provider Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_AI_API_KEY=...

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/cai
REDIS_URL=redis://localhost:6379

# Vector Store
VECTOR_STORE_TYPE=pinecone
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1

# Pipeline Configuration
CRAWLER_MAX_DEPTH=3
CRAWLER_RATE_LIMIT=100
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Security
JWT_SECRET=your-secret-key
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100
```

For complete configuration documentation, see [Configuration Reference](docs/configuration.md).

---

## Documentation Index

Comprehensive documentation is available in the `/docs` directory:

| Document | Description |
|----------|-------------|
| [System Architecture](docs/architecture.md) | Detailed system design, component interactions, and deployment patterns |
| [API Overview](docs/api/README.md) | Complete REST API reference with request/response examples |
| [Pipeline Package Overview](docs/pipeline/README.md) | Document processing, web crawling, and ingestion pipelines |
| [Data Models Overview](docs/models/README.md) | TypeScript interfaces and type definitions (90+ models) |
| [Configuration Reference](docs/configuration.md) | All 22 configuration variables with descriptions |

---

## Troubleshooting

### Common Issues

**Issue: `npm install` fails with workspace errors**
```bash
# Clear npm cache and reinstall
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**Issue: Docker build fails**
```bash
# Ensure Docker daemon is running
docker info

# Rebuild without cache
docker-compose build --no-cache
```

**Issue: API returns 401 Unauthorized**
- Verify your API key is correctly set in the `.env` file
- Ensure the `Authorization` header is properly formatted: `Bearer YOUR_API_KEY`

**Issue: WebSocket connection drops**
- Check that `WS_PORT` is not blocked by firewall
- Verify CORS settings in production environments

### Getting Help

- Check the [documentation](#documentation-index) for detailed guides
- Open an issue on GitHub for bugs or feature requests
- Review closed issues for common solutions

---

## Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Code Standards

- Write TypeScript with strict type checking
- Follow ESLint and Prettier configurations
- Include tests for new features
- Update documentation as needed

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ for the AI developer community
</p>