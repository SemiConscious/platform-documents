# Freedom Web - Overview

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Node.js](https://img.shields.io/badge/node-%3E%3D18.0.0-brightgreen)](https://nodejs.org/)
[![npm](https://img.shields.io/badge/npm-%3E%3D9.0.0-red)](https://www.npmjs.com/)

A standalone web application for call center and telephony operations, providing comprehensive features for active calls management, voicemail handling, address book management, team collaboration, and call logging with CTI (Computer Telephony Integration) bridge capabilities.

---

## Table of Contents

- [Introduction](#introduction)
- [Features Overview](#features-overview)
- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Development Setup](#development-setup)
- [Build & Deployment](#build--deployment)
- [Architecture Overview](#architecture-overview)
- [API Endpoints](#api-endpoints)
- [Documentation Index](#documentation-index)
- [Contributing](#contributing)
- [Support](#support)

---

## Introduction

Freedom Web is a modern, feature-rich web application designed to streamline call center operations and enhance telephony workflows. Built with a focus on user experience and operational efficiency, it serves as the primary interface for agents, supervisors, and administrators managing high-volume communication environments.

The application integrates seamlessly with existing telephony infrastructure through its CTI bridge capabilities, allowing real-time call control, presence management, and comprehensive activity tracking. Whether you're managing a small team or a large-scale contact center, Freedom Web provides the tools necessary to optimize communication workflows.

### Why Freedom Web?

- **Unified Interface**: Single pane of glass for all telephony operations
- **Real-time Updates**: Live call status, presence, and activity tracking
- **Flexible Integration**: CTI bridge support for various telephony systems
- **Secure by Design**: JWT-based authentication with role-based access control
- **Scalable Architecture**: Containerized deployment for easy scaling

---

## Features Overview

### Core Functionality

| Feature | Description |
|---------|-------------|
| **Active Calls Management** | Real-time monitoring and control of ongoing calls with transfer, hold, and conference capabilities |
| **Voicemail Handling** | Listen, manage, and respond to voicemails with voicemail drop functionality |
| **Call Logging & Wrap-ups** | Comprehensive call history with customizable wrap-up codes and notes |
| **Address Book** | Centralized contact management with search and quick-dial features |
| **Team Collaboration** | Real-time presence, internal messaging, and call transfer between team members |
| **Activity Tracking** | Detailed analytics and reporting on agent activities and call metrics |
| **CTI Bridge Integration** | Seamless integration with telephony systems via Computer Telephony Integration |
| **JWT Authentication** | Secure, token-based authentication with session management |

### Key Capabilities

```
┌─────────────────────────────────────────────────────────────────┐
│                        Freedom Web                               │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Call Control  │  Communication  │      Administration         │
├─────────────────┼─────────────────┼─────────────────────────────┤
│ • Make calls    │ • Voicemail     │ • User management           │
│ • Answer calls  │ • Address book  │ • Activity reports          │
│ • Transfer      │ • Team chat     │ • Call analytics            │
│ • Conference    │ • Presence      │ • System configuration      │
│ • Hold/Resume   │ • Notifications │ • Audit logging             │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

---

## Quick Start

Get Freedom Web running in under 5 minutes with Docker:

```bash
# Clone the repository
git clone https://github.com/your-org/freedom-freedom-web.git
cd freedom-freedom-web

# Copy environment configuration
cp .env.example .env

# Start with Docker Compose
docker-compose up -d

# Access the application
open http://localhost:3000
```

For development without Docker, see the [Development Setup](#development-setup) section below.

---

## Prerequisites

Before installing Freedom Web, ensure you have the following dependencies:

### Required Software

| Software | Minimum Version | Recommended Version | Purpose |
|----------|-----------------|---------------------|---------|
| Node.js | 18.0.0 | 20.x LTS | JavaScript runtime |
| npm | 9.0.0 | 10.x | Package management |
| Docker | 20.10.0 | 24.x | Containerization |
| Docker Compose | 2.0.0 | 2.20.x | Multi-container orchestration |

### System Requirements

- **Memory**: Minimum 2GB RAM (4GB recommended for development)
- **Storage**: 1GB available disk space
- **OS**: Linux, macOS, or Windows with WSL2

### Verify Prerequisites

```bash
# Check Node.js version
node --version
# Expected: v18.0.0 or higher

# Check npm version
npm --version
# Expected: 9.0.0 or higher

# Check Docker version
docker --version
# Expected: Docker version 20.10.0 or higher

# Check Docker Compose version
docker-compose --version
# Expected: Docker Compose version v2.0.0 or higher
```

---

## Installation

### Option 1: Docker Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/freedom-freedom-web.git
cd freedom-freedom-web

# Create environment file from template
cp .env.example .env

# Edit environment variables as needed
nano .env

# Build and start containers
docker-compose up -d --build

# Verify containers are running
docker-compose ps

# View logs
docker-compose logs -f freedom-web
```

### Option 2: Manual Installation

```bash
# Clone the repository
git clone https://github.com/your-org/freedom-freedom-web.git
cd freedom-freedom-web

# Install dependencies
npm install

# Create environment configuration
cp .env.example .env

# Build the application
npm run build

# Start the application
npm start
```

### Post-Installation Verification

After installation, verify the application is running correctly:

```bash
# Check application health
curl http://localhost:3000/health

# Expected response:
# {"status":"healthy","version":"1.0.0","timestamp":"..."}
```

---

## Development Setup

### Setting Up Your Development Environment

1. **Clone and Install Dependencies**

```bash
git clone https://github.com/your-org/freedom-freedom-web.git
cd freedom-freedom-web

# Install all dependencies including dev dependencies
npm install

# Install additional development tools globally (optional)
npm install -g nodemon eslint prettier
```

2. **Configure Environment Variables**

```bash
# Copy the example environment file
cp .env.example .env.development

# Edit with your development settings
nano .env.development
```

Example `.env.development` configuration:

```env
# Application Settings
NODE_ENV=development
PORT=3000
HOST=localhost

# API Configuration
API_BASE_URL=http://localhost:8080/api
CTI_BRIDGE_URL=ws://localhost:8081/cti

# Authentication
JWT_SECRET=your-development-secret-key
JWT_EXPIRY=24h

# Feature Flags
ENABLE_DEBUG_MODE=true
ENABLE_HOT_RELOAD=true

# Logging
LOG_LEVEL=debug
```

3. **Start Development Server**

```bash
# Start with hot-reload enabled
npm run dev

# Or start with specific environment
NODE_ENV=development npm run dev

# Start with debugging enabled
npm run dev:debug
```

4. **Run Tests**

```bash
# Run all tests
npm test

# Run tests with coverage report
npm run test:coverage

# Run tests in watch mode
npm run test:watch

# Run specific test file
npm test -- --testPathPattern="auth.test"
```

5. **Code Quality Tools**

```bash
# Run linter
npm run lint

# Fix linting issues automatically
npm run lint:fix

# Format code with Prettier
npm run format

# Type checking (if TypeScript)
npm run type-check
```

### Development Scripts Reference

| Script | Command | Description |
|--------|---------|-------------|
| `dev` | `npm run dev` | Start development server with hot-reload |
| `build` | `npm run build` | Create production build |
| `start` | `npm start` | Start production server |
| `test` | `npm test` | Run test suite |
| `lint` | `npm run lint` | Check code style |
| `format` | `npm run format` | Format code |

---

## Build & Deployment

### Production Build

```bash
# Create optimized production build
npm run build

# The build output will be in the ./dist directory
ls -la dist/
```

### Docker Deployment

#### Building the Docker Image

```bash
# Build production image
docker build -t freedom-web:latest .

# Build with specific tag
docker build -t freedom-web:v1.0.0 .

# Build with build arguments
docker build \
  --build-arg NODE_ENV=production \
  --build-arg API_URL=https://api.example.com \
  -t freedom-web:latest .
```

#### Docker Compose Production Configuration

Create a `docker-compose.prod.yml` file:

```yaml
version: '3.8'

services:
  freedom-web:
    image: freedom-web:latest
    container_name: freedom-web-prod
    restart: unless-stopped
    ports:
      - "80:3000"
    environment:
      - NODE_ENV=production
      - API_BASE_URL=${API_BASE_URL}
      - JWT_SECRET=${JWT_SECRET}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  default:
    name: freedom-network
```

Deploy with:

```bash
# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d

# Scale horizontally (if using load balancer)
docker-compose -f docker-compose.prod.yml up -d --scale freedom-web=3
```

### Kubernetes Deployment

Example Kubernetes deployment manifest:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: freedom-web
  labels:
    app: freedom-web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: freedom-web
  template:
    metadata:
      labels:
        app: freedom-web
    spec:
      containers:
      - name: freedom-web
        image: freedom-web:latest
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "production"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## Architecture Overview

Freedom Web follows a modern frontend architecture designed for scalability and maintainability:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Client Browser                              │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Freedom Web Frontend                           │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │    Views    │  │ Components  │  │   Services  │  │    Store    │    │
│  │             │  │             │  │             │  │             │    │
│  │ • Calls     │  │ • CallCard  │  │ • AuthSvc   │  │ • CallState │    │
│  │ • Voicemail │  │ • Dialpad   │  │ • CallSvc   │  │ • UserState │    │
│  │ • Contacts  │  │ • UserList  │  │ • CTISvc    │  │ • AppState  │    │
│  │ • Settings  │  │ • NavBar    │  │ • APISvc    │  │             │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
┌─────────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│     REST API        │ │   CTI Bridge    │ │   WebSocket         │
│                     │ │                 │ │   Server            │
│ • Authentication    │ │ • Call Control  │ │ • Real-time Events  │
│ • User Management   │ │ • Presence      │ │ • Notifications     │
│ • Call Logs         │ │ • Events        │ │ • Activity Updates  │
└─────────────────────┘ └─────────────────┘ └─────────────────────┘
```

### Key Architectural Components

| Component | Responsibility |
|-----------|----------------|
| **Views** | Page-level components representing different sections of the application |
| **Components** | Reusable UI components following atomic design principles |
| **Services** | Business logic and API communication layer |
| **Store** | Centralized state management for application data |
| **CTI Bridge** | WebSocket-based connection to telephony infrastructure |

For detailed architecture information, see the [Application Architecture](docs/architecture.md) documentation.

---

## API Endpoints

Freedom Web interacts with 10 API endpoints for various functionalities:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | User authentication |
| `/api/auth/refresh` | POST | Token refresh |
| `/api/calls/active` | GET | Retrieve active calls |
| `/api/calls/{id}` | GET | Get call details |
| `/api/voicemail` | GET | List voicemails |
| `/api/voicemail/{id}` | GET | Get voicemail details |
| `/api/contacts` | GET | List contacts |
| `/api/contacts/{id}` | GET | Get contact details |
| `/api/team/presence` | GET | Team presence status |
| `/api/activity` | GET | Activity log |

For complete API documentation and usage examples, refer to the [Application Routes](docs/routes.md) documentation.

---

## Documentation Index

Comprehensive documentation is available for all aspects of Freedom Web:

| Document | Description |
|----------|-------------|
| [Application Architecture](docs/architecture.md) | Detailed system architecture, component diagrams, and design patterns |
| [Configuration Guide](docs/configuration.md) | Environment variables, feature flags, and configuration options |
| [Application Routes](docs/routes.md) | Complete API endpoint documentation with request/response examples |
| [State Management](docs/state-management.md) | Store structure, actions, mutations, and state flow |
| [Authentication Guide](docs/authentication.md) | JWT implementation, token management, and security best practices |

### Additional Resources

- **API Reference**: Swagger/OpenAPI documentation available at `/api/docs`
- **Changelog**: See [CHANGELOG.md](CHANGELOG.md) for version history
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines

---

## Troubleshooting

### Common Issues

<details>
<summary><strong>Application won't start</strong></summary>

```bash
# Check if ports are in use
lsof -i :3000

# Check Docker logs
docker-compose logs freedom-web

# Verify environment variables
npm run env:check
```
</details>

<details>
<summary><strong>Authentication failures</strong></summary>

1. Verify JWT_SECRET is set correctly in environment
2. Check token expiration settings
3. Ensure API_BASE_URL is accessible
4. Review [Authentication Guide](docs/authentication.md) for detailed troubleshooting
</details>

<details>
<summary><strong>CTI Bridge connection issues</strong></summary>

```bash
# Test WebSocket connectivity
wscat -c ws://localhost:8081/cti

# Check CTI bridge logs
docker-compose logs cti-bridge
```
</details>

---

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/freedom-freedom-web/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/freedom-freedom-web/discussions)
- **Email**: support@example.com

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <sub>Built with ❤️ for better call center operations</sub>
</p>