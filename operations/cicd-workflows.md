# CI/CD and Release Management Documentation

## Overview

Natterbox uses a comprehensive CI/CD pipeline built on GitHub Actions with reusable workflows, integrated with custom tooling (RMHT - Release Management Helper Toolkit) and Guardian for package management. The system supports multiple deployment targets including Docker containers, RPM packages, NPM applications, and Terraform infrastructure.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CI/CD Pipeline Architecture                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────┐    ┌────────────────┐    ┌──────────────┐                   │
│  │  Developer │───▶│  GitHub Repo   │───▶│ GitHub       │                   │
│  │  Push/PR   │    │  (feature/     │    │ Actions      │                   │
│  └────────────┘    │   release)     │    │ Workflows    │                   │
│                    └────────────────┘    └──────┬───────┘                   │
│                                                  │                           │
│                    ┌─────────────────────────────┴────────────────┐         │
│                    │                                              │         │
│              ┌─────▼─────┐  ┌─────────────┐  ┌─────────────────┐ │         │
│              │  Docker   │  │    RPM      │  │       NPM       │ │         │
│              │  Build    │  │   Build     │  │      Build      │ │         │
│              └─────┬─────┘  └──────┬──────┘  └────────┬────────┘ │         │
│                    │               │                  │          │         │
│              ┌─────▼─────┐  ┌──────▼──────┐  ┌───────▼───────┐  │         │
│              │   ECR     │  │  Guardian   │  │   S3 Bucket   │  │         │
│              │  Registry │  │  (RPM Repo) │  │  (Artifacts)  │  │         │
│              └─────┬─────┘  └──────┬──────┘  └───────┬───────┘  │         │
│                    │               │                  │          │         │
│              ┌─────┴───────────────┴──────────────────┴─────┐   │         │
│              │                                              │   │         │
│              │       infrastructure-versions Repository     │   │         │
│              │         (Version State Management)           │   │         │
│              │                                              │   │         │
│              └──────────────────────┬───────────────────────┘   │         │
│                                     │                           │         │
│                    ┌────────────────┴─────────────────┐         │         │
│                    │                                  │         │         │
│              ┌─────▼─────┐                   ┌────────▼───────┐ │         │
│              │   RMHT    │                   │  Salt Stack    │ │         │
│              │  (Manual  │                   │  Deployment    │ │         │
│              │  Deploy)  │                   │                │ │         │
│              └───────────┘                   └────────────────┘ │         │
│                                                                 │         │
└─────────────────────────────────────────────────────────────────┴─────────┘
```

## Reusable Workflows Repository

The centralized workflows are maintained in `redmatter/github-workflows` and include:

| Workflow | Purpose |
|----------|---------|
| `docker-build-push.yml` | Build and push Docker images to ECR |
| `rpm-packages.yml` | Build and sync RPM packages to Guardian |
| `npm.yml` | Build NPM applications and copy to S3 |
| `secrets-check.yml` | Scan for secrets using Gitleaks |
| `finish-gitflow-release.yml` | Automate GitFlow release completion |
| `get-versions.yml` | Retrieve versions from infrastructure-versions |
| `release-notes.yml` | Generate release notes from commits |

## GitHub Actions Workflow Patterns

### Docker Build and Push Workflow

The `docker-build-push` workflow builds Docker images and pushes them to AWS ECR. It supports multi-platform builds and automatic tagging based on Git references.

**Key Features:**
- Automatic tag detection from Git tags
- Multi-platform builds (amd64/arm64)
- ECR repository management
- Build caching
- Security scanning with Gitleaks
- Automatic CD deployment via labels

**Example Usage:**
```yaml
name: Build Docker Image

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    uses: redmatter/github-workflows/.github/workflows/docker-build-push.yml@v3
    with:
      dockerfile: Dockerfile
      ecr-repository: my-service
      image-platforms: linux/amd64,linux/arm64
      detect-secrets: true
    secrets:
      AWS_OIDC_ROLE_ARN: ${{ secrets.AWS_OIDC_ROLE_ARN }}
      GH_SSH_KEY: ${{ secrets.GH_SSH_KEY }}
      GH_TOKEN: ${{ secrets.GH_TOKEN }}
```

**Important Inputs:**
| Input | Description | Default |
|-------|-------------|---------|
| `dockerfile` | Path to Dockerfile | `Dockerfile` |
| `ecr-repository` | ECR repository name | Required |
| `image-platforms` | Target platforms | `linux/amd64` |
| `tag-format` | Tag format (`internal`/`external`) | `internal` |
| `cd-label-prefix` | Label prefix for CD deployments | `deploy:` |
| `artifact-version-alias` | Alias for version updates | |

**Tag Formats:**
- **Internal**: `[TYPE/]NAME-MAJOR.MINOR.PATCH-vcsid[-rcN]` (e.g., `myapp-1.2.3-abc123-rc1`)
- **External**: Standard semver (e.g., `v1.2.3`)

### RPM Packages Workflow

Builds RPM packages and syncs them to the RPM repository (Guardian) for distribution.

**Key Features:**
- Automatic spec file detection
- SSH-based sync to build server
- Support for build artifacts
- Automatic versioning from tags
- Integration with infrastructure-versions

**Example Usage:**
```yaml
name: Build RPM

on:
  push:
    tags:
      - 'RM-*'

jobs:
  build:
    uses: redmatter/github-workflows/.github/workflows/rpm-packages.yml@v3
    with:
      rpm-spec-filename: mypackage.spec
      tag-format: internal
      detect-secrets: true
    secrets:
      RPM_SYNC_SSH_KEY: ${{ secrets.RPM_SYNC_SSH_KEY }}
      GH_TOKEN: ${{ secrets.GH_TOKEN }}
```

**Important Inputs:**
| Input | Description | Default |
|-------|-------------|---------|
| `rpm-spec-filename` | RPM spec file name | Auto-detect |
| `rpm-sync-user-server` | Sync server | `builduser@lonbld01.redmatter.com` |
| `tag-format` | Tag format | `internal` |
| `submodules` | Checkout submodules | `false` |

### NPM Workflow

Builds NPM applications and copies artifacts to S3 for deployment.

**Key Features:**
- Linting and testing integration
- Test results published as job summaries
- S3 artifact storage
- Support for static sites and Lambda functions

**Example Usage:**
```yaml
name: Build NPM App

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    uses: redmatter/github-workflows/.github/workflows/npm.yml@v3
    with:
      artifact-name: my-app
      aws-s3-bucket: redmatter-build
      aws-s3-object-prefix: artifacts/sites/my-app/
      publish-tests-results: true
    secrets:
      AWS_OIDC_ROLE_ARN: ${{ secrets.AWS_OIDC_ROLE_ARN }}
```

**S3 Object Key Patterns:**
- Static web pages: `artifacts/sites/<project-name>/<tag>/<artifact-name>-<tag>.zip`
- Lambda functions: `artifacts/lambda-packages/<project-name>/<tag>/<artifact-name>-<tag>.zip`

### Finish GitFlow Release Workflow

Automates the completion of GitFlow releases, including merging to master and tagging.

**Example Usage:**
```yaml
name: Finish Release

on:
  workflow_dispatch:
    inputs:
      branch:
        description: 'Release branch to finish'
        required: true

jobs:
  finish:
    uses: redmatter/github-workflows/.github/workflows/finish-gitflow-release.yml@v3
    with:
      release-branch: ${{ github.event.inputs.branch }}
    secrets:
      GH_TOKEN: ${{ secrets.GH_TOKEN }}
```

### Get Versions Workflow

Retrieves component versions from the infrastructure-versions repository.

**Example Usage:**
```yaml
jobs:
  get-versions:
    uses: redmatter/github-workflows/.github/workflows/get-versions.yml@v3
    with:
      environment: qa01
      component: myservice
    secrets:
      GH_TOKEN: ${{ secrets.GH_TOKEN }}
```

## RMHT - Release Management Helper Toolkit

RMHT is a command-line tool used by the Release Management team to verify deployments, manage versions, and automate deployment tasks.

### Installation

RMHT is installed from the `redmatter/operations-rmht` repository:

```bash
# Clone the repository
git clone git@github.com:redmatter/operations-rmht.git
cd operations-rmht

# Install using pipx (recommended)
pipx install .
```

### RMHT Commands

```
Usage: rmht [global options] tool [tool options] {tool arguments}

Global options:
    --help [tool]         Show help for the specified tool
    -q, --quiet           Suppress verbose output
    -v, --verbose         Enable verbose output

Tools:
    cs, check-setup       Check if RMHT is configured correctly
    vu, verify-runbook    Verify runbook exists and is parseable
    ve, verify-env        Verify component versions in an environment
    vk, verify-k8s        Verify Kubernetes component versions
    vi, verify-iv         Verify infrastructure-versions entries
    ge, get-env           Get current versions from an environment
    gk, get-k8s           Get Kubernetes component versions
    gi, get-iv            Get infrastructure-versions entries
    ue, update-env        Update component versions in an environment
    ui, update-iv         Update infrastructure-versions entries
```

### Key RMHT Operations

#### Verify Environment (`ve`)
Verifies that deployed versions match expected versions:
```bash
rmht ve qa01 core-api
rmht -v ve production dialplanscripts
```

#### Get Environment Versions (`ge`)
Retrieves currently deployed versions:
```bash
rmht ge qa01 core-api
rmht ge production RM-dialplanscripts
```

#### Update Infrastructure Versions (`ui`)
Updates version entries in the infrastructure-versions repository:
```bash
rmht ui qa01 core-api 1.2.3
```

#### Verify Runbook (`vu`)
Validates that a runbook exists and can be parsed:
```bash
rmht vu core-api
rmht vu RM-notifier
```

## Guardian - RPM Package Management

Guardian is the internal RPM repository manager accessible at `https://guardian.redmatter.com/`. It manages the distribution of RPM packages across environments.

### Package Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Guardian Package Flow                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐                                               │
│  │ RPM Build    │──────▶ lonbld01 (Build Server)                │
│  │ (GitHub CI)  │              │                                │
│  └──────────────┘              │                                │
│                                ▼                                │
│                    ┌─────────────────────┐                      │
│                    │     Guardian        │                      │
│                    │   (RPM Repository)  │                      │
│                    └─────────┬───────────┘                      │
│                              │                                  │
│           ┌──────────────────┼──────────────────┐               │
│           │                  │                  │               │
│           ▼                  ▼                  ▼               │
│    ┌────────────┐    ┌────────────┐    ┌────────────┐          │
│    │    QA      │    │  Staging   │    │ Production │          │
│    │ Repository │    │ Repository │    │ Repository │          │
│    └────────────┘    └────────────┘    └────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Pushing Packages to Guardian

1. **Access Guardian**: Navigate to `https://guardian.redmatter.com/`
2. **Select Repository**: Choose the target environment repository (qa01, qa02, production)
3. **Push Package**: Select the package version to push to the target repository
4. **Verify**: Use RMHT to verify the package is available:
   ```bash
   rmht ve qa01 RM-dialplanscripts
   ```

### Package Naming Convention

RPM packages follow the naming convention:
- `RM-<component>-<version>-<release>.x86_64.rpm`

Example: `RM-dialplanscripts-1.2.3-1.x86_64.rpm`

## Infrastructure Versions Repository

The `infrastructure-versions` repository (previously hosted in Bitbucket, now on GitHub) manages the desired state of component versions across all environments.

### Repository Structure

```
infrastructure-versions/
├── qa01/
│   ├── versions.sls
│   └── docker-versions.sls
├── qa02/
│   ├── versions.sls
│   └── docker-versions.sls
├── staging/
│   ├── versions.sls
│   └── docker-versions.sls
├── production/
│   ├── versions.sls
│   └── docker-versions.sls
└── README.md
```

### Version File Format (`versions.sls`)

```yaml
# SaltStack pillar format
packages:
  RM-dialplanscripts: 1.2.3-1
  RM-notifier: 2.0.1-1
  RM-schema-API: 3.1.0-1

containers:
  core-api: 1.5.0
  webphoned: 2.3.1
```

### Updating Versions

#### Manual Process:
1. Clone the repository and checkout the environment branch:
   ```bash
   git clone git@github.com:redmatter/infrastructure-versions.git
   cd infrastructure-versions
   git checkout qa01
   ```

2. Update the appropriate version file:
   ```bash
   vim versions.sls
   ```

3. Commit and push:
   ```bash
   git add versions.sls
   git commit -m "Update core-api to 1.5.0"
   git push
   ```

#### Automated Process (CD Labels):
When a PR or tag includes a `deploy:<environment>` label, the CI/CD pipeline automatically:
1. Builds the artifact
2. Pushes to the artifact repository (ECR/Guardian/S3)
3. Creates a PR in infrastructure-versions with the version update

## Environment Management

### Environments

| Environment | Purpose | Branch |
|-------------|---------|--------|
| `qa01` | Primary QA testing | `qa01` |
| `qa02` | Secondary QA testing | `qa02` |
| `staging` | Pre-production validation | `staging` |
| `production` | Live environment | `production` |

### Deployment Process

#### Docker Containers
1. Update version in `docker-versions.sls` for the target environment
2. On Salt master, pull the updated branch:
   ```bash
   cd /srv/pillar/infrastructure-versions
   git fetch && git pull
   ```
3. Run Salt state to deploy:
   ```bash
   salt 'qa01cnt*' state.apply docker
   ```

#### RPM Packages
1. Push package to Guardian for the target environment
2. Update version in `versions.sls` (if version pinned)
3. On Salt master, pull updated branch
4. Run Salt state to deploy:
   ```bash
   salt 'qa01pec*' state.apply packages
   ```
5. For schema packages, run migrations:
   ```bash
   dbmigrate <schema> latest
   ```

#### Terraform Deployments
1. Generate AWS session credentials locally:
   ```bash
   aws-vault exec redmatter-iam --json
   ```
2. SSH to deployment server (e.g., londev10)
3. Run Terraform deployment:
   ```bash
   tf deploy -e qa01 -m <module-name>
   ```
4. Paste credentials when prompted
5. Confirm with `yes`

## Versioning Strategy

### Semantic Versioning

All components follow Semantic Versioning (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Tag Format

**Internal Format** (most repositories):
```
[TYPE/]NAME-MAJOR.MINOR.PATCH-vcsid[-rcN]
```
Examples:
- `core-api-1.2.3-abc123`
- `RM-dialplanscripts-1.0.0-def456-rc1`
- `feature/auth-1.0.0-ghi789`

**External Format** (public packages):
```
vMAJOR.MINOR.PATCH
```
Examples:
- `v1.2.3`
- `v2.0.0-rc1`

### Release Candidates

Release candidates are tagged with `-rcN` suffix:
- `v1.2.3-rc1` - First release candidate
- `v1.2.3-rc2` - Second release candidate
- `v1.2.3` - Final release

## CD Labels for Automatic Deployment

The CI/CD pipeline supports automatic deployment to environments using GitHub labels:

| Label | Action |
|-------|--------|
| `deploy:qa01` | Deploy to QA01 environment |
| `deploy:qa02` | Deploy to QA02 environment |
| `deploy:staging` | Deploy to Staging environment |
| `deploy:production` | Deploy to Production environment |

When these labels are applied to a PR or tag:
1. The workflow builds the artifact
2. Pushes to the appropriate repository
3. Creates a PR in `infrastructure-versions` to update the version

## Secrets Management

### Required Secrets

| Secret | Purpose | Scope |
|--------|---------|-------|
| `AWS_OIDC_ROLE_ARN` | AWS OIDC authentication for ECR/S3 | Organization |
| `GH_SSH_KEY` | SSH key for private repo access | Organization |
| `GH_TOKEN` | GitHub API token | Organization |
| `RPM_SYNC_SSH_KEY` | SSH key for RPM sync server | Organization |

### Secret Detection

All workflows include Gitleaks secret scanning:
```yaml
with:
  detect-secrets: true
  gitleaks-enable-comments: true
  gitleaks-enable-summary: true
```

## Handover Requirements

When handing over a release to Release Management:

### Required Information
1. **Jira Tickets**: List of included tickets
2. **Version/Tag**: The exact version being released
3. **Runbook**: Link to deployment runbook
4. **Dependencies**: Any dependent components that must be deployed first
5. **Database Changes**: Schema migrations required
6. **Configuration Changes**: Environment variables or config updates needed
7. **Rollback Plan**: Steps to rollback if issues occur

### Handover Checklist
- [ ] All automated tests pass
- [ ] Code review completed
- [ ] Runbook verified with `rmht vu <component>`
- [ ] Version tagged correctly
- [ ] Artifacts built and pushed
- [ ] Documentation updated
- [ ] Change Request created (for production)

## Monitoring and Verification

### Post-Deployment Verification

Use RMHT to verify deployments:

```bash
# Verify specific component
rmht ve qa01 core-api

# Verbose output showing all hosts
rmht -v ve qa01 core-api

# Verify against infrastructure-versions
rmht vi qa01 core-api
```

### Common Verification Commands

```bash
# Check Docker container version
docker ps --format "table {{.Image}}\t{{.Names}}"

# Check RPM package version
rpm -qa | grep RM-dialplanscripts

# Check service health
systemctl status <service-name>

# View service logs
journalctl -u <service-name> -f
```

## Troubleshooting

### Build Failures

1. **Check workflow logs** in GitHub Actions
2. **Verify secrets** are available and not expired
3. **Check tag format** matches expected pattern
4. **Verify dependencies** are accessible

### Deployment Failures

1. **Verify version exists** in artifact repository:
   ```bash
   rmht ge <env> <component>
   ```

2. **Check infrastructure-versions** is updated:
   ```bash
   rmht gi <env> <component>
   ```

3. **Verify Salt state** ran successfully:
   ```bash
   salt-call state.show_sls <state>
   ```

### RMHT Issues

1. **Check setup**:
   ```bash
   rmht cs
   ```

2. **Verify SSH access**:
   ```bash
   ssh <salt-master>
   ```

3. **Check runbook parsing**:
   ```bash
   rmht vu <component>
   ```

## Related Documentation

- [GitHub Workflows Repository](https://github.com/redmatter/github-workflows)
- [Infrastructure Versions Repository](https://github.com/redmatter/infrastructure-versions)
- [RMHT Repository](https://github.com/redmatter/operations-rmht)
- [Guardian](https://guardian.redmatter.com/)
- [QA Deployment Cheat-sheet](https://natterbox.atlassian.net/wiki/spaces/ENG/pages/999096321)
- [Handover Requirements and Guidelines](https://natterbox.atlassian.net/wiki/spaces/ReleaseManagement/pages/2021589005)
- [Updating RPM Packages on QA](https://natterbox.atlassian.net/wiki/spaces/ENG/pages/1097924653)

---

*Last updated: 2026-01-20*
