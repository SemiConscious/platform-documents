# Development Guide

This comprehensive guide provides developers with everything needed to work effectively on the cai-service monorepo. Whether you're setting up your local environment for the first time, developing new packages, or contributing features, this guide covers the essential workflows, conventions, and best practices.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Setup](#local-setup)
3. [Running Tests](#running-tests)
4. [Package Development](#package-development)
5. [Code Conventions](#code-conventions)
6. [Contributing](#contributing)

---

## Prerequisites

Before you begin working on the cai-service monorepo, ensure your development environment meets the following requirements.

### Required Software

| Software | Minimum Version | Recommended Version | Purpose |
|----------|----------------|---------------------|---------|
| Node.js | 18.x | 20.x LTS | Runtime environment |
| npm | 9.x | 10.x | Package management |
| Git | 2.30+ | Latest | Version control |
| Docker | 20.10+ | Latest | Container services |
| Docker Compose | 2.0+ | Latest | Multi-container orchestration |

### System Requirements

- **Operating System**: Linux, macOS, or Windows with WSL2
- **RAM**: Minimum 8GB, recommended 16GB (AI model loading can be memory-intensive)
- **Disk Space**: At least 10GB free for dependencies, Docker images, and vector embeddings
- **CPU**: Multi-core processor recommended for parallel test execution

### Required Accounts and API Keys

The cai-service integrates with multiple external AI providers and services. You'll need access credentials for:

```bash
# AI Model Providers (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...

# Database Services
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379

# Vector Database
VECTOR_DB_HOST=localhost
VECTOR_DB_PORT=6333

# Optional: External Services
SENTRY_DSN=https://...
```

### Development Tools (Recommended)

- **IDE**: VS Code with the following extensions:
  - ESLint
  - Prettier
  - TypeScript and JavaScript Language Features
  - Thunder Client or REST Client (for API testing)
- **Database Client**: DBeaver, pgAdmin, or TablePlus
- **API Testing**: Postman or Insomnia

---

## Local Setup

Follow these steps to get the cai-service monorepo running on your local machine.

### Step 1: Clone the Repository

```bash
# Clone via SSH (recommended)
git clone git@github.com:your-org/cai-service.git

# Or clone via HTTPS
git clone https://github.com/your-org/cai-service.git

cd cai-service
```

### Step 2: Install Dependencies

The monorepo uses npm workspaces to manage multiple packages:

```bash
# Install all dependencies across the monorepo
npm install

# This will install dependencies for:
# - Root package
# - packages/api (REST API service)
# - packages/websocket (WebSocket service)
# - packages/pipeline (Data ingestion pipeline)
# - packages/shared (Shared utilities and types)
```

### Step 3: Environment Configuration

Create your local environment configuration:

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your local configuration
nano .env  # or use your preferred editor
```

Your `.env` file should include:

```bash
# Application Settings
NODE_ENV=development
LOG_LEVEL=debug
PORT=3000
WEBSOCKET_PORT=3001

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cai_service
DATABASE_POOL_SIZE=10

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=

# Vector Database (Qdrant)
VECTOR_DB_HOST=localhost
VECTOR_DB_PORT=6333
VECTOR_DB_COLLECTION=knowledge_base

# AI Provider Configuration
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4
ANTHROPIC_API_KEY=your-anthropic-key
ANTHROPIC_MODEL=claude-3-sonnet

# Rate Limiting
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100

# Feature Flags
ENABLE_WEB_CRAWLING=true
ENABLE_DOCUMENT_PROCESSING=true
MAX_CRAWL_DEPTH=3
```

### Step 4: Start Infrastructure Services

Use Docker Compose to spin up required services:

```bash
# Start all infrastructure services
docker-compose up -d

# This starts:
# - PostgreSQL (port 5432)
# - Redis (port 6379)
# - Qdrant vector database (port 6333)
# - Optional: Elasticsearch for logging
```

Verify services are running:

```bash
# Check container status
docker-compose ps

# Expected output:
# NAME                STATUS              PORTS
# cai-postgres        running             0.0.0.0:5432->5432/tcp
# cai-redis           running             0.0.0.0:6379->6379/tcp
# cai-qdrant          running             0.0.0.0:6333->6333/tcp
```

### Step 5: Database Setup

Run database migrations and seed initial data:

```bash
# Run all pending migrations
npm run db:migrate

# Seed development data (optional but recommended)
npm run db:seed

# Verify database connection
npm run db:status
```

### Step 6: Build and Start Services

```bash
# Build all packages
npm run build

# Start all services in development mode
npm run dev

# Or start specific services:
npm run dev:api        # REST API only
npm run dev:websocket  # WebSocket service only
npm run dev:pipeline   # Pipeline workers only
```

### Step 7: Verify Installation

```bash
# Health check endpoint
curl http://localhost:3000/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "vectorDb": "connected"
  }
}

# Test WebSocket connection
wscat -c ws://localhost:3001
```

### Troubleshooting Common Setup Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `ECONNREFUSED` on database | PostgreSQL not running | Run `docker-compose up -d postgres` |
| `npm install` fails | Node version mismatch | Use `nvm use` to switch to correct version |
| Port already in use | Conflicting service | Change port in `.env` or stop conflicting process |
| Vector DB connection fails | Qdrant not initialized | Wait 30s for Qdrant startup, then retry |

---

## Running Tests

The cai-service monorepo includes comprehensive test suites for ensuring code quality and reliability.

### Test Structure

```
cai-service/
├── packages/
│   ├── api/
│   │   └── __tests__/
│   │       ├── unit/           # Unit tests
│   │       ├── integration/    # Integration tests
│   │       └── e2e/           # End-to-end tests
│   ├── websocket/
│   │   └── __tests__/
│   ├── pipeline/
│   │   └── __tests__/
│   └── shared/
│       └── __tests__/
└── test/
    ├── fixtures/              # Shared test fixtures
    ├── mocks/                 # Mock implementations
    └── utils/                 # Test utilities
```

### Running All Tests

```bash
# Run entire test suite
npm test

# Run tests with coverage report
npm run test:coverage

# Run tests in watch mode (development)
npm run test:watch
```

### Running Package-Specific Tests

```bash
# Test specific package
npm run test --workspace=packages/api
npm run test --workspace=packages/websocket
npm run test --workspace=packages/pipeline
npm run test --workspace=packages/shared

# Or use the shorthand scripts
npm run test:api
npm run test:websocket
npm run test:pipeline
```

### Running Test Categories

```bash
# Unit tests only (fast, no external dependencies)
npm run test:unit

# Integration tests (requires Docker services)
npm run test:integration

# End-to-end tests (full system test)
npm run test:e2e

# Performance tests
npm run test:perf
```

### Test Configuration

Tests use Jest with the following configuration:

```typescript
// jest.config.ts
export default {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/packages'],
  testMatch: ['**/__tests__/**/*.test.ts'],
  collectCoverageFrom: [
    'packages/*/src/**/*.ts',
    '!packages/*/src/**/*.d.ts',
    '!packages/*/src/**/index.ts'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  setupFilesAfterEnv: ['<rootDir>/test/setup.ts'],
  moduleNameMapper: {
    '@cai-service/shared': '<rootDir>/packages/shared/src',
    '@cai-service/(.*)': '<rootDir>/packages/$1/src'
  }
};
```

### Writing Tests

Example unit test:

```typescript
// packages/api/__tests__/unit/services/prompt-executor.test.ts
import { PromptExecutor } from '../../../src/services/prompt-executor';
import { mockOpenAIClient } from '../../../../test/mocks/openai';

describe('PromptExecutor', () => {
  let executor: PromptExecutor;

  beforeEach(() => {
    executor = new PromptExecutor({
      client: mockOpenAIClient,
      defaultModel: 'gpt-4'
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('execute()', () => {
    it('should execute a prompt and return response', async () => {
      const result = await executor.execute({
        prompt: 'Hello, world!',
        maxTokens: 100
      });

      expect(result).toMatchObject({
        content: expect.any(String),
        tokensUsed: expect.any(Number),
        model: 'gpt-4'
      });
    });

    it('should handle rate limit errors with retry', async () => {
      mockOpenAIClient.chat.completions.create
        .mockRejectedValueOnce(new RateLimitError())
        .mockResolvedValueOnce({ choices: [{ message: { content: 'Success' } }] });

      const result = await executor.execute({ prompt: 'Test' });
      
      expect(result.content).toBe('Success');
      expect(mockOpenAIClient.chat.completions.create).toHaveBeenCalledTimes(2);
    });
  });
});
```

Example integration test:

```typescript
// packages/api/__tests__/integration/routes/prompts.test.ts
import supertest from 'supertest';
import { createApp } from '../../../src/app';
import { setupTestDatabase, teardownTestDatabase } from '../../../../test/utils/database';

describe('POST /api/v1/prompts/execute', () => {
  let app: Express.Application;
  let request: supertest.SuperTest<supertest.Test>;

  beforeAll(async () => {
    await setupTestDatabase();
    app = await createApp();
    request = supertest(app);
  });

  afterAll(async () => {
    await teardownTestDatabase();
  });

  it('should execute a prompt successfully', async () => {
    const response = await request
      .post('/api/v1/prompts/execute')
      .set('Authorization', 'Bearer test-api-key')
      .send({
        prompt: 'What is 2+2?',
        model: 'gpt-4',
        maxTokens: 50
      });

    expect(response.status).toBe(200);
    expect(response.body).toMatchObject({
      success: true,
      data: {
        content: expect.any(String),
        model: 'gpt-4'
      }
    });
  });
});
```

### Test Utilities

The monorepo provides several test utilities:

```typescript
// test/utils/factories.ts
import { Factory } from 'fishery';
import { User, Prompt, KnowledgeDocument } from '@cai-service/shared';

export const userFactory = Factory.define<User>(({ sequence }) => ({
  id: `user-${sequence}`,
  email: `user${sequence}@test.com`,
  apiKey: `test-key-${sequence}`,
  createdAt: new Date()
}));

export const promptFactory = Factory.define<Prompt>(({ sequence }) => ({
  id: `prompt-${sequence}`,
  content: 'Test prompt content',
  model: 'gpt-4',
  maxTokens: 100
}));

// Usage in tests
const user = userFactory.build();
const users = userFactory.buildList(5);
```

---

## Package Development

The cai-service is organized as a monorepo with multiple packages, each serving a specific purpose.

### Monorepo Structure

```
cai-service/
├── package.json              # Root package.json with workspaces
├── tsconfig.json             # Base TypeScript config
├── packages/
│   ├── api/                  # REST API service
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── src/
│   │       ├── routes/       # API route handlers
│   │       ├── services/     # Business logic
│   │       ├── middleware/   # Express middleware
│   │       └── index.ts
│   ├── websocket/            # WebSocket service
│   │   ├── package.json
│   │   └── src/
│   │       ├── handlers/     # WebSocket event handlers
│   │       ├── rooms/        # Room management
│   │       └── index.ts
│   ├── pipeline/             # Data ingestion pipeline
│   │   ├── package.json
│   │   └── src/
│   │       ├── workers/      # Background workers
│   │       ├── processors/   # Document processors
│   │       ├── crawlers/     # Web crawlers
│   │       └── index.ts
│   └── shared/               # Shared utilities and types
│       ├── package.json
│       └── src/
│           ├── types/        # TypeScript interfaces
│           ├── utils/        # Shared utilities
│           ├── constants/    # Shared constants
│           └── index.ts
└── tools/                    # Development tools and scripts
```

### Creating a New Package

```bash
# Create package directory
mkdir -p packages/new-package/src

# Initialize package
cd packages/new-package
npm init -y
```

Configure the new package's `package.json`:

```json
{
  "name": "@cai-service/new-package",
  "version": "1.0.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch",
    "test": "jest",
    "lint": "eslint src/"
  },
  "dependencies": {
    "@cai-service/shared": "*"
  },
  "devDependencies": {
    "typescript": "^5.0.0"
  }
}
```

Create TypeScript configuration:

```json
// packages/new-package/tsconfig.json
{
  "extends": "../../tsconfig.json",
  "compilerOptions": {
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src/**/*"],
  "references": [
    { "path": "../shared" }
  ]
}
```

### Package Dependencies

When adding dependencies between packages:

```bash
# Add shared package as dependency
cd packages/api
npm install @cai-service/shared@*

# Or from root
npm install @cai-service/shared --workspace=packages/api
```

### Building Packages

```bash
# Build all packages (respects dependency order)
npm run build

# Build specific package
npm run build --workspace=packages/api

# Build with watch mode
npm run build:watch

# Clean build artifacts
npm run clean
```

### Adding New Functionality

When adding new features, follow this workflow:

1. **Define types in shared package**:

```typescript
// packages/shared/src/types/knowledge.ts
export interface KnowledgeDocument {
  id: string;
  title: string;
  content: string;
  embeddings: number[];
  metadata: DocumentMetadata;
  createdAt: Date;
  updatedAt: Date;
}

export interface DocumentMetadata {
  source: 'web' | 'upload' | 'api';
  sourceUrl?: string;
  contentType: 'pdf' | 'csv' | 'json' | 'txt' | 'html';
  pageCount?: number;
  wordCount: number;
}
```

2. **Implement service logic**:

```typescript
// packages/api/src/services/knowledge-service.ts
import { KnowledgeDocument, DocumentMetadata } from '@cai-service/shared';
import { VectorDBClient } from '../clients/vector-db';
import { EmbeddingService } from './embedding-service';

export class KnowledgeService {
  constructor(
    private vectorDb: VectorDBClient,
    private embeddingService: EmbeddingService
  ) {}

  async ingestDocument(
    content: string,
    metadata: Partial<DocumentMetadata>
  ): Promise<KnowledgeDocument> {
    // Generate embeddings
    const embeddings = await this.embeddingService.generateEmbeddings(content);
    
    // Store in vector database
    const document = await this.vectorDb.insert({
      content,
      embeddings,
      metadata: {
        ...metadata,
        wordCount: content.split(/\s+/).length
      }
    });

    return document;
  }

  async searchKnowledge(query: string, limit = 10): Promise<KnowledgeDocument[]> {
    const queryEmbeddings = await this.embeddingService.generateEmbeddings(query);
    return this.vectorDb.similaritySearch(queryEmbeddings, limit);
  }
}
```

3. **Create API routes**:

```typescript
// packages/api/src/routes/knowledge.ts
import { Router } from 'express';
import { KnowledgeService } from '../services/knowledge-service';
import { validateRequest } from '../middleware/validation';
import { ingestDocumentSchema, searchKnowledgeSchema } from '../schemas/knowledge';

export function createKnowledgeRouter(knowledgeService: KnowledgeService): Router {
  const router = Router();

  router.post(
    '/ingest',
    validateRequest(ingestDocumentSchema),
    async (req, res, next) => {
      try {
        const document = await knowledgeService.ingestDocument(
          req.body.content,
          req.body.metadata
        );
        res.status(201).json({ success: true, data: document });
      } catch (error) {
        next(error);
      }
    }
  );

  router.get(
    '/search',
    validateRequest(searchKnowledgeSchema),
    async (req, res, next) => {
      try {
        const results = await knowledgeService.searchKnowledge(
          req.query.q as string,
          Number(req.query.limit) || 10
        );
        res.json({ success: true, data: results });
      } catch (error) {
        next(error);
      }
    }
  );

  return router;
}
```

---

## Code Conventions

Maintaining consistent code style across the monorepo ensures readability and reduces cognitive load for all contributors.

### TypeScript Standards

**Use strict TypeScript configuration**:

```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true
  }
}
```

**Type definitions**:

```typescript
// ✅ Good: Explicit types for function parameters and returns
export async function executePrompt(
  prompt: string,
  options: PromptOptions
): Promise<PromptResult> {
  // implementation
}

// ✅ Good: Use interfaces for object shapes
interface PromptOptions {
  model: AIModel;
  maxTokens: number;
  temperature?: number;
}

// ❌ Bad: Avoid 'any' type
function processData(data: any): any {
  // implementation
}

// ✅ Good: Use generics for flexible typing
function processData<T extends BaseDocument>(data: T): ProcessedResult<T> {
  // implementation
}
```

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Files | kebab-case | `prompt-executor.ts` |
| Classes | PascalCase | `PromptExecutor` |
| Interfaces | PascalCase with 'I' prefix (optional) | `PromptOptions` or `IPromptOptions` |
| Functions | camelCase | `executePrompt` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_RETRY_ATTEMPTS` |
| Variables | camelCase | `promptResult` |
| Type aliases | PascalCase | `AIModelType` |

### Code Organization

**Service classes**:

```typescript
// packages/api/src/services/prompt-executor.ts

import { Logger } from '@cai-service/shared';
import { AIClient } from '../clients/ai-client';
import { PromptOptions, PromptResult } from '../types';

export class PromptExecutor {
  private readonly logger: Logger;
  private readonly client: AIClient;

  constructor(
    private readonly config: PromptExecutorConfig
  ) {
    this.logger = new Logger('PromptExecutor');
    this.client = new AIClient(config.aiConfig);
  }

  /**
   * Executes a prompt against the configured AI model.
   * 
   * @param prompt - The prompt text to execute
   * @param options - Execution options
   * @returns The prompt result including generated content
   * @throws {RateLimitError} When rate limit is exceeded
   * @throws {ModelUnavailableError} When the requested model is unavailable
   */
  async execute(
    prompt: string,
    options: PromptOptions
  ): Promise<PromptResult> {
    this.logger.info('Executing prompt', { model: options.model });
    
    const startTime = Date.now();
    
    try {
      const result = await this.client.complete(prompt, options);
      
      this.logger.info('Prompt executed successfully', {
        model: options.model,
        duration: Date.now() - startTime,
        tokensUsed: result.tokensUsed
      });
      
      return result;
    } catch (error) {
      this.logger.error('Prompt execution failed', { error });
      throw this.handleError(error);
    }
  }

  private handleError(error: unknown): Error {
    if (error instanceof RateLimitError) {
      return error;
    }
    return new PromptExecutionError('Failed to execute prompt', { cause: error });
  }
}
```

### Error Handling

**Define custom error classes**:

```typescript
// packages/shared/src/errors/index.ts

export class BaseError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = 500,
    public readonly context?: Record<string, unknown>
  ) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace(this, this.constructor);
  }
}

export class ValidationError extends BaseError {
  constructor(message: string, context?: Record<string, unknown>) {
    super(message, 'VALIDATION_ERROR', 400, context);
  }
}

export class NotFoundError extends BaseError {
  constructor(resource: string, id: string) {
    super(`${resource} not found: ${id}`, 'NOT_FOUND', 404, { resource, id });
  }
}

export class RateLimitError extends BaseError {
  constructor(retryAfter?: number) {
    super('Rate limit exceeded', 'RATE_LIMIT', 429, { retryAfter });
  }
}
```

**Error handling middleware**:

```typescript
// packages/api/src/middleware/error-handler.ts

import { Request, Response, NextFunction } from 'express';
import { BaseError } from '@cai-service/shared';
import { Logger } from '../utils/logger';

const logger = new Logger('ErrorHandler');

export function errorHandler(
  error: Error,
  req: Request,
  res: Response,
  next: NextFunction
): void {
  if (error instanceof BaseError) {
    logger.warn('Handled error', {
      code: error.code,
      message: error.message,
      context: error.context
    });
    
    res.status(error.statusCode).json({
      success: false,
      error: {
        code: error.code,
        message: error.message,
        ...(process.env.NODE_ENV === 'development' && { context: error.context })
      }
    });
    return;
  }

  logger.error('Unhandled error', { error });
  
  res.status(500).json({
    success: false,
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred'
    }
  });
}
```

### Linting and Formatting

The project uses ESLint and Prettier for code quality:

```bash
# Run linter
npm run lint

# Fix auto-fixable issues
npm run lint:fix

# Format code with Prettier
npm run format

# Check formatting
npm run format:check
```

ESLint configuration highlights:

```javascript
// .eslintrc.js
module.exports = {
  parser: '@typescript-eslint/parser',
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:@typescript-eslint/recommended-requiring-type-checking',
    'prettier'
  ],
  rules: {
    '@typescript-eslint/explicit-function-return-type': 'error',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/no-floating-promises': 'error',
    'no-console': ['error', { allow: ['warn', 'error'] }]
  }
};
```

---

## Contributing

We welcome contributions from the community! This section outlines the process for contributing to cai-service.

### Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch** from `main`
4. **Make your changes** following our code conventions
5. **Submit a pull request**

### Branch Naming

Use descriptive branch names following this pattern:

```
<type>/<ticket-number>-<short-description>

Examples:
feature/CAI-123-add-claude-support
bugfix/CAI-456-fix-websocket-reconnect
docs/CAI-789-update-api-documentation
refactor/CAI-101-extract-embedding-service
```

### Commit Messages

Follow the Conventional Commits specification:

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:

```bash
feat(api): add support for Claude 3 model

- Add Anthropic client integration
- Update prompt executor to support Claude
- Add configuration for Anthropic API

Closes #123

---

fix(websocket): resolve connection timeout issue

The WebSocket connection was timing out after 30 seconds
of inactivity. Extended timeout to 5 minutes and added
heartbeat mechanism.

Fixes #456
```

### Pull Request Process

1. **Ensure all tests pass**:
   ```bash
   npm run test
   npm run lint
   npm run build
   ```

2. **Update documentation** if needed

3. **Add tests** for new functionality

4. **Fill out the PR template** completely

5. **Request review** from at least one maintainer

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project conventions
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
- [ ] Tests pass locally
```

### Code Review Guidelines

**For reviewers**:
- Check for correctness and edge cases
- Verify tests are adequate
- Ensure code follows conventions
- Look for potential performance issues
- Validate error handling

**For contributors**:
- Respond to feedback promptly
- Explain your reasoning for decisions
- Be open to suggestions
- Update PR based on feedback

### Release Process

The project follows semantic versioning (semver):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Releases are automated through CI/CD when tags are pushed:

```bash
# Create release tag
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin v1.2.0
```

---

## Additional Resources

- **API Documentation**: See `/docs/api` for full API reference
- **Architecture Guide**: See `/docs/architecture.md` for system design
- **Troubleshooting**: See `/docs/troubleshooting.md` for common issues
- **Changelog**: See `CHANGELOG.md` for version history

For questions or support, reach out via:
- GitHub Issues for bug reports and feature requests
- GitHub Discussions for questions and community support
- Slack channel `#cai-service-dev` for real-time discussion