# Development Workflow

This guide provides comprehensive documentation for contributing to the Sapien service, including Git branching strategy, issue workflow, peer review processes, and essential CLI commands. Following these workflows ensures consistent, high-quality contributions and smooth collaboration across the development team.

## Overview

Sapien is a PHP-based REST API service built on Symfony that provides CRUD operations for entities like Person, Pet, and Toy. The service utilizes a Docker-based development environment with Xdebug integration, ESL event system for real-time updates, and OAuth2 authentication. Understanding the development workflow is essential for maintaining code quality and ensuring seamless integration of new features and bug fixes.

---

## Git Workflow

### Branching Strategy

Sapien follows a modified GitFlow branching strategy optimized for continuous delivery. Understanding this strategy is crucial for all contributors.

#### Main Branches

| Branch | Purpose | Protection Level |
|--------|---------|------------------|
| `main` | Production-ready code | Fully protected, requires PR |
| `develop` | Integration branch for features | Protected, requires PR |
| `staging` | Pre-production testing | Protected, requires PR |

#### Supporting Branches

```
Feature branches:    feature/SAPIEN-{ticket-number}-{brief-description}
Bugfix branches:     bugfix/SAPIEN-{ticket-number}-{brief-description}
Hotfix branches:     hotfix/SAPIEN-{ticket-number}-{brief-description}
Release branches:    release/v{major}.{minor}.{patch}
```

### Branch Naming Conventions

Always use the following format for branch names:

```bash
# Feature branch example
git checkout -b feature/SAPIEN-1234-add-pet-vaccination-endpoint

# Bugfix branch example
git checkout -b bugfix/SAPIEN-5678-fix-person-null-reference

# Hotfix branch example (for production issues)
git checkout -b hotfix/SAPIEN-9012-oauth-token-expiry-fix
```

### Creating a New Branch

```bash
# Ensure you're on the latest develop branch
git checkout develop
git pull origin develop

# Create and checkout your new feature branch
git checkout -b feature/SAPIEN-1234-add-pet-vaccination-endpoint

# Push the branch to remote to establish tracking
git push -u origin feature/SAPIEN-1234-add-pet-vaccination-endpoint
```

### Commit Message Standards

Sapien enforces conventional commit messages for automated changelog generation and semantic versioning:

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Commit Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `style` | Code style changes (formatting, etc.) |
| `refactor` | Code refactoring |
| `perf` | Performance improvements |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks |

#### Example Commit Messages

```bash
# Feature commit
git commit -m "feat(api): add vaccination history endpoint for Pet entity

- Added GET /api/pets/{id}/vaccinations endpoint
- Implemented VaccinationController with proper validation
- Added unit and integration tests

Resolves: SAPIEN-1234"

# Bug fix commit
git commit -m "fix(auth): resolve token refresh race condition

- Added mutex lock for concurrent refresh requests
- Implemented token refresh queue mechanism
- Updated OAuth2 service tests

Fixes: SAPIEN-5678"
```

### Merge Strategy

```bash
# Before merging, always rebase on the latest develop
git checkout develop
git pull origin develop
git checkout feature/SAPIEN-1234-add-pet-vaccination-endpoint
git rebase develop

# Resolve any conflicts, then force push (only on feature branches)
git push --force-with-lease origin feature/SAPIEN-1234-add-pet-vaccination-endpoint
```

---

## Working on Issues

### Issue Lifecycle

Issues in Sapien follow a structured lifecycle to ensure proper tracking and accountability:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Backlog   │───▶│  Ready for  │───▶│ In Progress │───▶│  In Review  │
│             │    │ Development │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                │
                   ┌─────────────┐    ┌─────────────┐           │
                   │    Done     │◀───│   Testing   │◀──────────┘
                   │             │    │             │
                   └─────────────┘    └─────────────┘
```

### Picking Up an Issue

1. **Select an Issue**: Choose from the "Ready for Development" column in your project board

2. **Assign Yourself**: Update the issue assignment in your tracking system

3. **Move to In Progress**: Transition the issue status

4. **Create Your Branch**:

```bash
# Clone if you haven't already
git clone git@github.com:organization/sapien.git
cd sapien

# Create your working branch
git checkout develop
git pull origin develop
git checkout -b feature/SAPIEN-1234-add-pet-vaccination-endpoint
```

### Development Checklist

Before marking any issue as complete, ensure you've addressed:

- [ ] Implementation matches acceptance criteria
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] API documentation updated (if applicable)
- [ ] Database migrations created (if applicable)
- [ ] ESL events documented (if applicable)
- [ ] No PHP linting errors
- [ ] Code coverage maintained or improved
- [ ] Local Docker environment tested

### Writing Tests

Sapien uses PHPUnit for testing. Follow this structure:

```php
<?php
// tests/Unit/Service/PetServiceTest.php

namespace App\Tests\Unit\Service;

use App\Service\PetService;
use App\Repository\PetRepository;
use PHPUnit\Framework\TestCase;

class PetServiceTest extends TestCase
{
    private PetService $petService;
    private PetRepository $petRepository;

    protected function setUp(): void
    {
        $this->petRepository = $this->createMock(PetRepository::class);
        $this->petService = new PetService($this->petRepository);
    }

    public function testGetPetByIdReturnsCorrectPet(): void
    {
        // Arrange
        $expectedPet = new Pet();
        $expectedPet->setId(1);
        $expectedPet->setName('Buddy');

        $this->petRepository
            ->expects($this->once())
            ->method('find')
            ->with(1)
            ->willReturn($expectedPet);

        // Act
        $result = $this->petService->getPetById(1);

        // Assert
        $this->assertSame($expectedPet, $result);
        $this->assertEquals('Buddy', $result->getName());
    }

    public function testGetPetByIdThrowsExceptionWhenNotFound(): void
    {
        // Arrange
        $this->petRepository
            ->method('find')
            ->willReturn(null);

        // Assert
        $this->expectException(PetNotFoundException::class);

        // Act
        $this->petService->getPetById(999);
    }
}
```

### Integration Test Example

```php
<?php
// tests/Integration/Controller/PetControllerTest.php

namespace App\Tests\Integration\Controller;

use Symfony\Bundle\FrameworkBundle\Test\WebTestCase;
use Symfony\Component\HttpFoundation\Response;

class PetControllerTest extends WebTestCase
{
    private $client;

    protected function setUp(): void
    {
        $this->client = static::createClient();
        $this->authenticateClient();
    }

    public function testCreatePetEndpoint(): void
    {
        $this->client->request(
            'POST',
            '/api/pets',
            [],
            [],
            ['CONTENT_TYPE' => 'application/json'],
            json_encode([
                'name' => 'Buddy',
                'species' => 'dog',
                'ownerId' => 1
            ])
        );

        $this->assertResponseStatusCodeSame(Response::HTTP_CREATED);
        
        $responseData = json_decode(
            $this->client->getResponse()->getContent(),
            true
        );
        
        $this->assertEquals('Buddy', $responseData['name']);
        $this->assertArrayHasKey('id', $responseData);
    }

    private function authenticateClient(): void
    {
        // OAuth2 authentication setup
        $token = $this->getTestAccessToken();
        $this->client->setServerParameter(
            'HTTP_AUTHORIZATION',
            'Bearer ' . $token
        );
    }
}
```

---

## Peer Review Process

### Creating a Pull Request

When your feature is complete, create a pull request with the following template:

```markdown
## Description
Brief description of changes made

## Related Issue
SAPIEN-1234

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing Performed
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed
- [ ] All existing tests pass

## Database Changes
- [ ] No database changes
- [ ] Migration included
- [ ] Migration tested (up and down)

## API Changes
- [ ] No API changes
- [ ] OpenAPI spec updated
- [ ] Backward compatible
- [ ] Breaking change documented

## ESL Events
- [ ] No ESL changes
- [ ] New events documented
- [ ] Event schema validated

## Screenshots (if applicable)
Add screenshots for UI changes or API response examples

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings introduced
```

### Review Guidelines

#### For Reviewers

When reviewing pull requests, evaluate the following:

1. **Code Quality**
   - Follows PSR-12 coding standards
   - Methods are appropriately sized (< 20 lines preferred)
   - Clear variable and method naming
   - No code duplication

2. **Architecture**
   - Follows SOLID principles
   - Appropriate use of Symfony services
   - Proper dependency injection
   - Correct use of repositories and entities

3. **Testing**
   - Adequate test coverage (minimum 80%)
   - Edge cases covered
   - Tests are readable and maintainable

4. **Security**
   - No SQL injection vulnerabilities
   - Proper input validation
   - OAuth2 scopes correctly applied
   - Rate limiting considerations

5. **Performance**
   - Efficient database queries
   - Proper use of caching
   - No N+1 query problems

#### Review Response Times

| Priority | Initial Review | Follow-up Review |
|----------|---------------|------------------|
| Critical (Hotfix) | 2 hours | 1 hour |
| High | 4 hours | 2 hours |
| Normal | 24 hours | 12 hours |
| Low | 48 hours | 24 hours |

### Approval Requirements

- Minimum 2 approving reviews required
- All CI checks must pass
- No unresolved conversations
- Branch must be up-to-date with `develop`

### Handling Review Feedback

```bash
# Address review comments with additional commits
git add .
git commit -m "fix(api): address review feedback

- Renamed variable for clarity
- Added null check for optional parameter
- Expanded test coverage for edge case"

git push origin feature/SAPIEN-1234-add-pet-vaccination-endpoint
```

---

## CLI Commands

### Docker Environment Commands

```bash
# Start the development environment
docker-compose up -d

# View logs
docker-compose logs -f sapien-api

# Access the PHP container shell
docker-compose exec sapien-api bash

# Stop the environment
docker-compose down

# Rebuild containers (after Dockerfile changes)
docker-compose build --no-cache
docker-compose up -d
```

### Symfony Console Commands

```bash
# Run inside the Docker container or with docker-compose exec

# Clear cache
docker-compose exec sapien-api php bin/console cache:clear

# Run database migrations
docker-compose exec sapien-api php bin/console doctrine:migrations:migrate

# Create a new migration
docker-compose exec sapien-api php bin/console doctrine:migrations:diff

# Validate database schema
docker-compose exec sapien-api php bin/console doctrine:schema:validate

# List all available commands
docker-compose exec sapien-api php bin/console list
```

### Testing Commands

```bash
# Run all tests
docker-compose exec sapien-api php bin/phpunit

# Run specific test file
docker-compose exec sapien-api php bin/phpunit tests/Unit/Service/PetServiceTest.php

# Run tests with coverage report
docker-compose exec sapien-api php bin/phpunit --coverage-html coverage/

# Run only unit tests
docker-compose exec sapien-api php bin/phpunit --testsuite=unit

# Run only integration tests
docker-compose exec sapien-api php bin/phpunit --testsuite=integration
```

### Code Quality Commands

```bash
# PHP CS Fixer - check code style
docker-compose exec sapien-api php vendor/bin/php-cs-fixer fix --dry-run --diff

# PHP CS Fixer - fix code style automatically
docker-compose exec sapien-api php vendor/bin/php-cs-fixer fix

# PHPStan - static analysis
docker-compose exec sapien-api php vendor/bin/phpstan analyse src tests

# Run all quality checks
docker-compose exec sapien-api composer run-script quality-checks
```

### Xdebug Commands

```bash
# Enable Xdebug
docker-compose exec sapien-api bash -c "echo 'xdebug.mode=debug' >> /usr/local/etc/php/conf.d/docker-php-ext-xdebug.ini"

# Disable Xdebug (for better performance)
docker-compose exec sapien-api bash -c "sed -i 's/xdebug.mode=debug/xdebug.mode=off/' /usr/local/etc/php/conf.d/docker-php-ext-xdebug.ini"

# Check Xdebug status
docker-compose exec sapien-api php -m | grep xdebug
```

### Database Commands

```bash
# Access MySQL CLI
docker-compose exec sapien-db mysql -u sapien -p sapien_dev

# Create database backup
docker-compose exec sapien-db mysqldump -u sapien -p sapien_dev > backup.sql

# Restore database
docker-compose exec -T sapien-db mysql -u sapien -p sapien_dev < backup.sql

# Reset database (caution!)
docker-compose exec sapien-api php bin/console doctrine:database:drop --force
docker-compose exec sapien-api php bin/console doctrine:database:create
docker-compose exec sapien-api php bin/console doctrine:migrations:migrate --no-interaction
docker-compose exec sapien-api php bin/console doctrine:fixtures:load --no-interaction
```

---

## Dev Box Updates

### Keeping Your Environment Current

Regularly update your development environment to ensure compatibility:

```bash
# Pull latest changes
git checkout develop
git pull origin develop

# Update Docker images
docker-compose pull

# Rebuild containers if needed
docker-compose build

# Restart environment
docker-compose down
docker-compose up -d

# Run migrations
docker-compose exec sapien-api php bin/console doctrine:migrations:migrate --no-interaction

# Clear cache
docker-compose exec sapien-api php bin/console cache:clear
```

### Environment Configuration

Create a local environment file for development overrides:

```bash
# Copy the example environment file
cp .env.example .env.local
```

Configure your `.env.local`:

```ini
# Database Configuration
DATABASE_URL="mysql://sapien:secret@sapien-db:3306/sapien_dev"

# OAuth2 Configuration
OAUTH_CLIENT_ID=dev_client
OAUTH_CLIENT_SECRET=dev_secret

# Xdebug Configuration
XDEBUG_MODE=debug
XDEBUG_CLIENT_HOST=host.docker.internal
XDEBUG_CLIENT_PORT=9003

# ESL Configuration
ESL_BROKER_URL=amqp://guest:guest@sapien-rabbitmq:5672

# Blob Storage (local development)
BLOB_STORAGE_ADAPTER=local
BLOB_STORAGE_PATH=/var/www/storage

# Profiler
APP_DEBUG=true
PROFILER_ENABLED=true
```

### Troubleshooting Common Issues

#### Docker Container Won't Start

```bash
# Check for port conflicts
docker-compose ps
netstat -tulpn | grep :80

# Remove orphan containers
docker-compose down --remove-orphans

# Clean up Docker system
docker system prune -f
```

#### Database Connection Issues

```bash
# Verify database container is running
docker-compose ps sapien-db

# Check database logs
docker-compose logs sapien-db

# Test connection from API container
docker-compose exec sapien-api php bin/console doctrine:query:sql "SELECT 1"
```

#### Xdebug Not Connecting

1. Verify PhpStorm is listening on port 9003
2. Check `XDEBUG_CLIENT_HOST` matches your host IP
3. Ensure firewall allows incoming connections on port 9003

```bash
# Verify Xdebug configuration
docker-compose exec sapien-api php -i | grep xdebug
```

### Weekly Maintenance Checklist

- [ ] Pull latest `develop` branch
- [ ] Update Docker images (`docker-compose pull`)
- [ ] Run database migrations
- [ ] Clear all caches
- [ ] Run full test suite
- [ ] Update Composer dependencies (if notified)
- [ ] Review and close stale branches

---

## Best Practices Summary

1. **Always work from fresh branches** - Start from updated `develop`
2. **Keep commits atomic** - One logical change per commit
3. **Write tests first** - TDD when possible
4. **Request reviews early** - Don't wait for perfection
5. **Respond to feedback promptly** - Keep PRs moving
6. **Update documentation** - Code changes often need doc updates
7. **Clean up after merging** - Delete merged branches

Following these workflows ensures consistent, high-quality contributions to Sapien and maintains a healthy codebase for all team members.