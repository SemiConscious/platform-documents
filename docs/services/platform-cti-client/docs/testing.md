# Testing Guide

## Overview

This guide provides comprehensive documentation for setting up and running end-to-end (E2E) tests for the FreedomCTI platform-cti-client service using Cypress. As a browser-based CTI application embedded within Salesforce, thorough testing is essential to ensure reliable call management, WebSocket communication, and seamless integration with Salesforce Lightning.

The testing strategy covers real-time call events, voicemail handling, call logging functionality, and multi-environment configurations across dev, QA, stage, and production environments.

## Test Setup

### Prerequisites

Before setting up the test environment, ensure you have the following installed:

- **Node.js** (v16.x or higher)
- **npm** (v8.x or higher) or **yarn** (v1.22.x or higher)
- **Git** for version control
- **Chrome**, **Firefox**, or **Edge** browser for test execution

### Installation

1. **Clone the repository and navigate to the project directory:**

```bash
git clone https://github.com/your-org/platform-cti-client.git
cd platform-cti-client
```

2. **Install project dependencies:**

```bash
npm install
# or
yarn install
```

3. **Install Cypress as a dev dependency (if not already included):**

```bash
npm install --save-dev cypress
# or
yarn add -D cypress
```

4. **Open Cypress for initial setup:**

```bash
npx cypress open
```

This command initializes the Cypress folder structure and creates necessary configuration files.

### Project Structure

After setup, your test directory should follow this structure:

```
platform-cti-client/
├── cypress/
│   ├── e2e/
│   │   ├── call-management/
│   │   │   ├── inbound-calls.cy.js
│   │   │   ├── outbound-calls.cy.js
│   │   │   └── call-transfer.cy.js
│   │   ├── voicemail/
│   │   │   ├── voicemail-playback.cy.js
│   │   │   └── voicemail-management.cy.js
│   │   ├── call-logging/
│   │   │   ├── call-history.cy.js
│   │   │   └── call-notes.cy.js
│   │   └── integration/
│   │       ├── salesforce-iframe.cy.js
│   │       └── websocket-events.cy.js
│   ├── fixtures/
│   │   ├── calls.json
│   │   ├── voicemails.json
│   │   ├── users.json
│   │   └── websocket-events.json
│   ├── support/
│   │   ├── commands.js
│   │   ├── e2e.js
│   │   └── websocket-utils.js
│   └── downloads/
├── cypress.config.js
└── package.json
```

### Environment Configuration

Create environment-specific configuration files for each deployment environment:

```javascript
// cypress.env.json
{
  "DEV_BASE_URL": "https://dev-cti.freedomcti.com",
  "QA_BASE_URL": "https://qa-cti.freedomcti.com",
  "STAGE_BASE_URL": "https://stage-cti.freedomcti.com",
  "PROD_BASE_URL": "https://cti.freedomcti.com",
  "SALESFORCE_INSTANCE_URL": "https://your-instance.salesforce.com",
  "API_KEY": "your-test-api-key",
  "WEBSOCKET_URL": "wss://ws.freedomcti.com",
  "TEST_USER_EMAIL": "testuser@example.com",
  "TEST_USER_PASSWORD": "securepassword123"
}
```

> **Security Note:** Never commit `cypress.env.json` with real credentials to version control. Add it to `.gitignore` and use CI/CD environment variables for sensitive data.

## Cypress Configuration

### Main Configuration File

Create or update `cypress.config.js` with the following configuration:

```javascript
// cypress.config.js
const { defineConfig } = require('cypress');

module.exports = defineConfig({
  e2e: {
    // Base URL for the application
    baseUrl: process.env.CYPRESS_BASE_URL || 'http://localhost:3000',
    
    // Spec file pattern
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    
    // Support file location
    supportFile: 'cypress/support/e2e.js',
    
    // Viewport settings for Salesforce iframe
    viewportWidth: 400,
    viewportHeight: 700,
    
    // Timeouts
    defaultCommandTimeout: 10000,
    requestTimeout: 15000,
    responseTimeout: 30000,
    pageLoadTimeout: 60000,
    
    // Video and screenshot settings
    video: true,
    videoCompression: 32,
    screenshotOnRunFailure: true,
    screenshotsFolder: 'cypress/screenshots',
    videosFolder: 'cypress/videos',
    
    // Retry configuration for flaky test mitigation
    retries: {
      runMode: 2,
      openMode: 0
    },
    
    // Environment-specific settings
    env: {
      environment: 'dev',
      apiUrl: 'https://api.freedomcti.com',
      wsUrl: 'wss://ws.freedomcti.com'
    },
    
    // Setup node events for custom tasks
    setupNodeEvents(on, config) {
      // Load environment-specific configuration
      const environment = config.env.environment || 'dev';
      
      // Custom task for WebSocket testing
      on('task', {
        log(message) {
          console.log(message);
          return null;
        },
        
        // Task to simulate WebSocket events
        sendWebSocketEvent({ eventType, payload }) {
          // Implementation for WebSocket event simulation
          return { sent: true, eventType, payload };
        },
        
        // Task to seed test data
        seedTestData({ dataType, data }) {
          // Implementation for test data seeding
          return { seeded: true, dataType };
        }
      });
      
      // Modify config based on environment
      if (environment === 'qa') {
        config.baseUrl = process.env.QA_BASE_URL;
      } else if (environment === 'stage') {
        config.baseUrl = process.env.STAGE_BASE_URL;
      }
      
      return config;
    }
  },
  
  // Component testing configuration (if applicable)
  component: {
    devServer: {
      framework: 'react',
      bundler: 'webpack'
    }
  }
});
```

### Multi-Environment Support

Create separate configuration files for different environments:

```javascript
// cypress.config.dev.js
const { defineConfig } = require('cypress');
const baseConfig = require('./cypress.config');

module.exports = defineConfig({
  ...baseConfig.e2e,
  e2e: {
    ...baseConfig.e2e,
    baseUrl: 'https://dev-cti.freedomcti.com',
    env: {
      ...baseConfig.e2e.env,
      environment: 'dev',
      apiUrl: 'https://dev-api.freedomcti.com'
    }
  }
});
```

## Custom Commands

### Command Registration

Define custom commands in `cypress/support/commands.js`:

```javascript
// cypress/support/commands.js

// ============================================
// Authentication Commands
// ============================================

/**
 * Login to FreedomCTI application
 * @param {string} email - User email
 * @param {string} password - User password
 */
Cypress.Commands.add('login', (email, password) => {
  cy.session([email, password], () => {
    cy.visit('/login');
    cy.get('[data-testid="email-input"]').type(email);
    cy.get('[data-testid="password-input"]').type(password);
    cy.get('[data-testid="login-button"]').click();
    cy.url().should('include', '/dashboard');
  });
});

/**
 * Login via Salesforce OAuth
 * @param {Object} credentials - Salesforce credentials
 */
Cypress.Commands.add('loginViaSalesforce', (credentials) => {
  const { instanceUrl, accessToken } = credentials;
  
  cy.window().then((win) => {
    win.localStorage.setItem('sf_access_token', accessToken);
    win.localStorage.setItem('sf_instance_url', instanceUrl);
  });
  
  cy.visit('/');
  cy.get('[data-testid="cti-container"]').should('be.visible');
});

// ============================================
// Call Management Commands
// ============================================

/**
 * Initiate an outbound call
 * @param {string} phoneNumber - Phone number to call
 */
Cypress.Commands.add('makeOutboundCall', (phoneNumber) => {
  cy.get('[data-testid="dialpad-input"]').clear().type(phoneNumber);
  cy.get('[data-testid="call-button"]').click();
  cy.get('[data-testid="call-status"]').should('contain', 'Dialing');
});

/**
 * Answer an incoming call
 */
Cypress.Commands.add('answerIncomingCall', () => {
  cy.get('[data-testid="incoming-call-modal"]').should('be.visible');
  cy.get('[data-testid="answer-call-button"]').click();
  cy.get('[data-testid="call-status"]').should('contain', 'Connected');
});

/**
 * End the current active call
 */
Cypress.Commands.add('endCall', () => {
  cy.get('[data-testid="end-call-button"]').click();
  cy.get('[data-testid="call-status"]').should('contain', 'Call Ended');
});

/**
 * Transfer call to another agent
 * @param {string} targetAgent - Agent extension or ID
 */
Cypress.Commands.add('transferCall', (targetAgent) => {
  cy.get('[data-testid="transfer-button"]').click();
  cy.get('[data-testid="transfer-target-input"]').type(targetAgent);
  cy.get('[data-testid="confirm-transfer-button"]').click();
  cy.get('[data-testid="transfer-status"]').should('contain', 'Transfer Complete');
});

/**
 * Place call on hold
 */
Cypress.Commands.add('holdCall', () => {
  cy.get('[data-testid="hold-button"]').click();
  cy.get('[data-testid="call-status"]').should('contain', 'On Hold');
});

// ============================================
// Voicemail Commands
// ============================================

/**
 * Navigate to voicemail section
 */
Cypress.Commands.add('openVoicemail', () => {
  cy.get('[data-testid="voicemail-tab"]').click();
  cy.get('[data-testid="voicemail-list"]').should('be.visible');
});

/**
 * Play a voicemail by index
 * @param {number} index - Voicemail index in the list
 */
Cypress.Commands.add('playVoicemail', (index) => {
  cy.get('[data-testid="voicemail-item"]').eq(index).click();
  cy.get('[data-testid="voicemail-player"]').should('be.visible');
  cy.get('[data-testid="play-button"]').click();
  cy.get('[data-testid="player-status"]').should('contain', 'Playing');
});

/**
 * Delete a voicemail
 * @param {number} index - Voicemail index
 */
Cypress.Commands.add('deleteVoicemail', (index) => {
  cy.get('[data-testid="voicemail-item"]').eq(index)
    .find('[data-testid="delete-voicemail-button"]').click();
  cy.get('[data-testid="confirm-delete-modal"]').should('be.visible');
  cy.get('[data-testid="confirm-delete-button"]').click();
});

// ============================================
// WebSocket Commands
// ============================================

/**
 * Wait for WebSocket connection to be established
 */
Cypress.Commands.add('waitForWebSocketConnection', () => {
  cy.window().should('have.property', 'wsConnected', true);
});

/**
 * Simulate a WebSocket event
 * @param {string} eventType - Type of event
 * @param {Object} payload - Event payload
 */
Cypress.Commands.add('simulateWebSocketEvent', (eventType, payload) => {
  cy.window().then((win) => {
    const event = new CustomEvent('ws-message', {
      detail: { type: eventType, payload }
    });
    win.dispatchEvent(event);
  });
});

// ============================================
// Redux State Commands
// ============================================

/**
 * Get current Redux state
 * @param {string} slice - State slice name
 */
Cypress.Commands.add('getReduxState', (slice) => {
  cy.window()
    .its('store')
    .invoke('getState')
    .then((state) => {
      return slice ? state[slice] : state;
    });
});

/**
 * Dispatch a Redux action
 * @param {Object} action - Redux action object
 */
Cypress.Commands.add('dispatchReduxAction', (action) => {
  cy.window().its('store').invoke('dispatch', action);
});

// ============================================
// API Intercept Commands
// ============================================

/**
 * Intercept and mock call history API
 * @param {Array} calls - Mock call data
 */
Cypress.Commands.add('mockCallHistory', (calls) => {
  cy.intercept('GET', '**/api/calls/history*', {
    statusCode: 200,
    body: { calls, totalCount: calls.length }
  }).as('getCallHistory');
});

/**
 * Intercept and mock voicemail API
 * @param {Array} voicemails - Mock voicemail data
 */
Cypress.Commands.add('mockVoicemails', (voicemails) => {
  cy.intercept('GET', '**/api/voicemails*', {
    statusCode: 200,
    body: { voicemails, totalCount: voicemails.length }
  }).as('getVoicemails');
});
```

### Support File Configuration

Configure the support file to load commands and set up global hooks:

```javascript
// cypress/support/e2e.js

// Import custom commands
import './commands';

// Import WebSocket utilities
import './websocket-utils';

// Global before hook
beforeEach(() => {
  // Clear local storage before each test
  cy.clearLocalStorage();
  
  // Reset API mocks
  cy.intercept('**/api/**', { log: false });
});

// Global after hook for cleanup
afterEach(function() {
  // Capture screenshot on failure
  if (this.currentTest?.state === 'failed') {
    const testName = this.currentTest.title.replace(/\s+/g, '_');
    cy.screenshot(`failure_${testName}`);
  }
});

// Handle uncaught exceptions
Cypress.on('uncaught:exception', (err, runnable) => {
  // Log the error but don't fail the test for known issues
  if (err.message.includes('ResizeObserver loop')) {
    return false;
  }
  return true;
});
```

## Test Patterns

### Testing Call Management

```javascript
// cypress/e2e/call-management/inbound-calls.cy.js

describe('Inbound Call Management', () => {
  beforeEach(() => {
    cy.login(Cypress.env('TEST_USER_EMAIL'), Cypress.env('TEST_USER_PASSWORD'));
    cy.waitForWebSocketConnection();
  });

  it('should display incoming call notification', () => {
    // Simulate incoming call WebSocket event
    cy.simulateWebSocketEvent('INCOMING_CALL', {
      callId: 'call-123',
      callerId: '+1234567890',
      callerName: 'John Doe',
      queueName: 'Sales'
    });

    // Verify notification appears
    cy.get('[data-testid="incoming-call-modal"]')
      .should('be.visible')
      .within(() => {
        cy.contains('John Doe').should('be.visible');
        cy.contains('+1234567890').should('be.visible');
        cy.contains('Sales').should('be.visible');
      });
  });

  it('should answer incoming call successfully', () => {
    // Setup: Simulate incoming call
    cy.simulateWebSocketEvent('INCOMING_CALL', {
      callId: 'call-456',
      callerId: '+1987654321',
      callerName: 'Jane Smith'
    });

    // Action: Answer the call
    cy.answerIncomingCall();

    // Assert: Verify call is connected
    cy.get('[data-testid="active-call-panel"]').should('be.visible');
    cy.get('[data-testid="call-timer"]').should('be.visible');
    cy.getReduxState('calls').should('have.property', 'activeCall');
  });

  it('should handle missed call correctly', () => {
    // Simulate incoming call
    cy.simulateWebSocketEvent('INCOMING_CALL', {
      callId: 'call-789',
      callerId: '+1555555555',
      callerName: 'Missed Caller'
    });

    // Wait for timeout (simulate missed call)
    cy.simulateWebSocketEvent('CALL_MISSED', {
      callId: 'call-789'
    });

    // Verify missed call notification
    cy.get('[data-testid="missed-call-badge"]').should('be.visible');
    cy.get('[data-testid="call-history-tab"]').click();
    cy.contains('Missed Caller').should('be.visible');
    cy.get('[data-testid="call-status-missed"]').should('be.visible');
  });
});
```

### Testing Voicemail Functionality

```javascript
// cypress/e2e/voicemail/voicemail-playback.cy.js

describe('Voicemail Playback', () => {
  const mockVoicemails = [
    {
      id: 'vm-001',
      callerId: '+1234567890',
      callerName: 'John Doe',
      duration: 45,
      timestamp: '2024-01-15T10:30:00Z',
      transcription: 'Hello, this is John calling about...',
      isNew: true
    },
    {
      id: 'vm-002',
      callerId: '+1987654321',
      callerName: 'Jane Smith',
      duration: 120,
      timestamp: '2024-01-14T15:45:00Z',
      transcription: 'Hi, I wanted to follow up on...',
      isNew: false
    }
  ];

  beforeEach(() => {
    cy.login(Cypress.env('TEST_USER_EMAIL'), Cypress.env('TEST_USER_PASSWORD'));
    cy.mockVoicemails(mockVoicemails);
    cy.openVoicemail();
    cy.wait('@getVoicemails');
  });

  it('should display voicemail list correctly', () => {
    cy.get('[data-testid="voicemail-item"]').should('have.length', 2);
    
    // Verify first voicemail (new)
    cy.get('[data-testid="voicemail-item"]').first()
      .should('contain', 'John Doe')
      .and('have.class', 'voicemail-new');
    
    // Verify voicemail count badge
    cy.get('[data-testid="new-voicemail-count"]').should('contain', '1');
  });

  it('should play voicemail and update playback controls', () => {
    cy.playVoicemail(0);
    
    // Verify player controls
    cy.get('[data-testid="voicemail-player"]')
      .within(() => {
        cy.get('[data-testid="pause-button"]').should('be.visible');
        cy.get('[data-testid="progress-bar"]').should('be.visible');
        cy.get('[data-testid="duration-display"]').should('contain', '0:45');
      });
    
    // Verify transcription display
    cy.get('[data-testid="voicemail-transcription"]')
      .should('contain', 'Hello, this is John calling about...');
  });

  it('should mark voicemail as read after playback', () => {
    cy.playVoicemail(0);
    
    // Wait for playback to complete (simulated)
    cy.get('[data-testid="voicemail-item"]').first()
      .should('not.have.class', 'voicemail-new');
    
    cy.get('[data-testid="new-voicemail-count"]').should('contain', '0');
  });
});
```

### Testing WebSocket Communication

```javascript
// cypress/e2e/integration/websocket-events.cy.js

describe('WebSocket Communication', () => {
  beforeEach(() => {
    cy.login(Cypress.env('TEST_USER_EMAIL'), Cypress.env('TEST_USER_PASSWORD'));
  });

  it('should establish WebSocket connection on load', () => {
    cy.waitForWebSocketConnection();
    cy.get('[data-testid="connection-status"]')
      .should('have.class', 'connected')
      .and('contain', 'Connected');
  });

  it('should handle WebSocket reconnection', () => {
    cy.waitForWebSocketConnection();
    
    // Simulate connection loss
    cy.simulateWebSocketEvent('DISCONNECT', {});
    
    // Verify reconnection attempt
    cy.get('[data-testid="connection-status"]')
      .should('have.class', 'reconnecting');
    
    // Simulate successful reconnection
    cy.simulateWebSocketEvent('RECONNECTED', {});
    
    cy.get('[data-testid="connection-status"]')
      .should('have.class', 'connected');
  });

  it('should update Redux state on WebSocket events', () => {
    cy.waitForWebSocketConnection();
    
    // Simulate agent status change
    cy.simulateWebSocketEvent('AGENT_STATUS_CHANGED', {
      agentId: 'agent-001',
      status: 'available'
    });
    
    cy.getReduxState('agent').should((agentState) => {
      expect(agentState.status).to.equal('available');
    });
  });
});
```

### Testing Call Logging

```javascript
// cypress/e2e/call-logging/call-history.cy.js

describe('Call History and Logging', () => {
  const mockCallHistory = [
    {
      id: 'call-001',
      direction: 'inbound',
      phoneNumber: '+1234567890',
      contactName: 'John Doe',
      duration: 180,
      timestamp: '2024-01-15T10:30:00Z',
      disposition: 'completed',
      notes: 'Discussed product features'
    },
    {
      id: 'call-002',
      direction: 'outbound',
      phoneNumber: '+1987654321',
      contactName: 'Jane Smith',
      duration: 0,
      timestamp: '2024-01-15T09:15:00Z',
      disposition: 'no-answer',
      notes: ''
    }
  ];

  beforeEach(() => {
    cy.login(Cypress.env('TEST_USER_EMAIL'), Cypress.env('TEST_USER_PASSWORD'));
    cy.mockCallHistory(mockCallHistory);
  });

  it('should display call history with correct data', () => {
    cy.get('[data-testid="call-history-tab"]').click();
    cy.wait('@getCallHistory');
    
    cy.get('[data-testid="call-history-item"]').should('have.length', 2);
    
    // Verify first call entry
    cy.get('[data-testid="call-history-item"]').first()
      .within(() => {
        cy.get('[data-testid="call-direction-icon"]')
          .should('have.class', 'inbound');
        cy.contains('John Doe').should('be.visible');
        cy.contains('3:00').should('be.visible'); // 180 seconds
        cy.get('[data-testid="call-disposition"]')
          .should('contain', 'Completed');
      });
  });

  it('should filter call history by date range', () => {
    cy.get('[data-testid="call-history-tab"]').click();
    cy.wait('@getCallHistory');
    
    cy.get('[data-testid="date-filter-start"]').type('2024-01-15');
    cy.get('[data-testid="date-filter-end"]').type('2024-01-15');
    cy.get('[data-testid="apply-filter-button"]').click();
    
    cy.wait('@getCallHistory');
    cy.get('[data-testid="call-history-item"]').should('have.length.gte', 0);
  });

  it('should add notes to a completed call', () => {
    cy.get('[data-testid="call-history-tab"]').click();
    cy.wait('@getCallHistory');
    
    // Open call details
    cy.get('[data-testid="call-history-item"]').first().click();
    
    // Add notes
    cy.get('[data-testid="call-notes-input"]')
      .clear()
      .type('Follow-up scheduled for next week');
    
    cy.intercept('PUT', '**/api/calls/*/notes', {
      statusCode: 200,
      body: { success: true }
    }).as('updateNotes');
    
    cy.get('[data-testid="save-notes-button"]').click();
    cy.wait('@updateNotes');
    
    cy.get('[data-testid="notes-saved-indicator"]').should('be.visible');
  });
});
```

### Testing Salesforce Integration

```javascript
// cypress/e2e/integration/salesforce-iframe.cy.js

describe('Salesforce Lightning Integration', () => {
  beforeEach(() => {
    // Setup Salesforce context
    cy.window().then((win) => {
      win.sforce = {
        interaction: {
          cti: {
            enableClickToDial: cy.stub().as('enableClickToDial'),
            onClickToDial: cy.stub().as('onClickToDial'),
            screenPop: cy.stub().as('screenPop')
          }
        }
      };
    });
    
    cy.loginViaSalesforce({
      instanceUrl: Cypress.env('SALESFORCE_INSTANCE_URL'),
      accessToken: 'mock-access-token'
    });
  });

  it('should initialize CTI toolkit on load', () => {
    cy.get('@enableClickToDial').should('have.been.called');
  });

  it('should handle click-to-dial from Salesforce', () => {
    // Simulate click-to-dial event
    cy.window().then((win) => {
      const clickToDialCallback = win.sforce.interaction.cti.onClickToDial.args[0][0];
      clickToDialCallback({
        number: '+1234567890',
        objectType: 'Contact',
        recordId: '003XXXXXXXXXXXX',
        recordName: 'John Doe'
      });
    });
    
    // Verify call is initiated
    cy.get('[data-testid="dialpad-input"]').should('have.value', '+1234567890');
    cy.get('[data-testid="call-status"]').should('contain', 'Dialing');
  });

  it('should perform screen pop on incoming call', () => {
    // Simulate incoming call with Salesforce record match
    cy.simulateWebSocketEvent('INCOMING_CALL', {
      callId: 'call-123',
      callerId: '+1234567890',
      salesforceRecordId: '003XXXXXXXXXXXX'
    });
    
    cy.answerIncomingCall();
    
    // Verify screen pop was called
    cy.get('@screenPop').should('have.been.calledWith', {
      type: 'sobject/Contact',
      params: { recordId: '003XXXXXXXXXXXX' }
    });
  });
});
```

## Running Tests

### Local Development

Run tests interactively during development:

```bash
# Open Cypress Test Runner (interactive mode)
npx cypress open

# Run specific test file
npx cypress run --spec "cypress/e2e/call-management/inbound-calls.cy.js"

# Run all tests headlessly
npx cypress run
```

### Running Tests by Environment

```bash
# Run tests against development environment
npx cypress run --env environment=dev

# Run tests against QA environment
npx cypress run --env environment=qa --config baseUrl=https://qa-cti.freedomcti.com

# Run tests against staging
CYPRESS_BASE_URL=https://stage-cti.freedomcti.com npx cypress run --env environment=stage
```

### Running Tests in CI/CD

#### GitHub Actions Configuration

```yaml
# .github/workflows/cypress.yml
name: Cypress E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  cypress-run:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        browser: [chrome, firefox]
        
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run Cypress tests
        uses: cypress-io/github-action@v5
        with:
          browser: ${{ matrix.browser }}
          headed: false
        env:
          CYPRESS_BASE_URL: ${{ secrets.CYPRESS_BASE_URL }}
          CYPRESS_TEST_USER_EMAIL: ${{ secrets.TEST_USER_EMAIL }}
          CYPRESS_TEST_USER_PASSWORD: ${{ secrets.TEST_USER_PASSWORD }}

      - name: Upload screenshots on failure
        uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: cypress-screenshots-${{ matrix.browser }}
          path: cypress/screenshots

      - name: Upload videos
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: cypress-videos-${{ matrix.browser }}
          path: cypress/videos
```

### Test Scripts in package.json

```json
{
  "scripts": {
    "cy:open": "cypress open",
    "cy:run": "cypress run",
    "cy:run:dev": "cypress run --env environment=dev",
    "cy:run:qa": "cypress run --env environment=qa --config baseUrl=https://qa-cti.freedomcti.com",
    "cy:run:stage": "cypress run --env environment=stage --config baseUrl=https://stage-cti.freedomcti.com",
    "cy:run:chrome": "cypress run --browser chrome",
    "cy:run:firefox": "cypress run --browser firefox",
    "cy:run:headed": "cypress run --headed",
    "cy:parallel": "cypress run --parallel --record --key $CYPRESS_RECORD_KEY"
  }
}
```

### Generating Test Reports

Install and configure Mochawesome for HTML reports:

```bash
npm install --save-dev mochawesome mochawesome-merge mochawesome-report-generator
```

```javascript
// cypress.config.js (add to e2e config)
{
  reporter: 'mochawesome',
  reporterOptions: {
    reportDir: 'cypress/reports',
    overwrite: false,
    html: true,
    json: true,
    charts: true
  }
}
```

Generate combined report:

```bash
# After running tests
npx mochawesome-merge "cypress/reports/*.json" > cypress/reports/combined.json
npx marge cypress/reports/combined.json -f report -o cypress/reports
```

## Best Practices and Common Pitfalls

### Best Practices

1. **Use data-testid attributes** for selecting elements instead of CSS classes or element hierarchies
2. **Implement proper waiting** using Cypress's built-in assertions rather than arbitrary `cy.wait()` calls
3. **Keep tests independent** - each test should be able to run in isolation
4. **Use fixtures** for mock data to keep tests maintainable
5. **Leverage custom commands** to reduce code duplication

### Common Pitfalls to Avoid

1. **Avoid flaky tests** by ensuring proper element visibility checks before interactions
2. **Don't rely on timing** - use Cypress's automatic retry mechanism
3. **Handle iframes carefully** - FreedomCTI runs in a Salesforce iframe, requiring special handling
4. **Mock external dependencies** to ensure test reliability
5. **Clean up test data** after each test run to prevent state pollution

---

For additional support or questions about the testing infrastructure, please contact the FreedomCTI development team or refer to the [Cypress documentation](https://docs.cypress.io).