# Terraform Module Catalog

> ⚠️ **Status:** Draft - Inventory in progress

Catalog of all Terraform modules used for Natterbox infrastructure.

## Overview

Natterbox uses Terraform extensively for infrastructure as code. Modules are primarily in the `redmatter` GitHub organization with `aws-terraform-*` naming convention.

---

## Module Categories

### Networking
| Module | Description | Repository |
|--------|-------------|------------|
| aws-terraform-network-rt | RT platform networking | `redmatter/aws-terraform-network-rt` |
| aws-terraform-dns | DNS management | `redmatter/aws-terraform-dns` |

### Core Platform
| Module | Description | Repository |
|--------|-------------|------------|
| aws-terraform-omnichannel | Omnichannel infrastructure | `redmatter/aws-terraform-omnichannel` |
| aws-terraform-omnichannel-territory-setup | Territory configuration | `redmatter/aws-terraform-omnichannel-territory-setup` |
| aws-terraform-fsx8 | FSXINETD PHP 8 deployment | `redmatter/aws-terraform-fsx8` |
| aws-terraform-rt-tts | RT TTS deployment | `redmatter/aws-terraform-rt-tts` |
| aws-terraform-rt-sipgwping | SIP gateway ping | `redmatter/aws-terraform-rt-sipgwping` |
| aws-terraform-global-platform-workflow-engine | Workflow engine ECS | `redmatter/aws-terraform-global-platform-workflow-engine` |

### AI/CAI
| Module | Description | Repository |
|--------|-------------|------------|
| aws-terraform-cai | CAI infrastructure | `redmatter/aws-terraform-cai` |
| aws-terraform-bedrock | Bedrock GenAI configuration | `redmatter/aws-terraform-bedrock` |
| aws-terraform-rt-cai-websocket | CAI WebSocket deployment | `redmatter/aws-terraform-rt-cai-websocket` |

### Observability (Lumina)
| Module | Description | Repository |
|--------|-------------|------------|
| aws-terraform-lumina-pipeline | Lumina metrics pipeline | `redmatter/aws-terraform-lumina-pipeline` |
| aws-terraform-lumina-region-distributor | Cross-region event distribution | `redmatter/aws-terraform-lumina-region-distributor` |
| aws-terraform-nexus-lumina-pipeline | Athena metrics pipeline | `redmatter/aws-terraform-nexus-lumina-pipeline` |
| terraform-elastic | Elastic Stack infrastructure | `redmatter/terraform-elastic` |

### Security
| Module | Description | Repository |
|--------|-------------|------------|
| aws-terraform-security-tools | Security Hub, Config, Inspector | `redmatter/aws-terraform-security-tools` |
| aws-terraform-security-configs | Regional security configs | `redmatter/aws-terraform-security-configs` |
| aws-terraform-waf | WAFv2 Web ACLs | `redmatter/aws-terraform-waf` |
| aws-terraform-sapien-waf | Sapien WAF | `redmatter/aws-terraform-sapien-waf` |

### IAM & Identity
| Module | Description | Repository |
|--------|-------------|------------|
| aws-terraform-iam | IAM configuration | `redmatter/aws-terraform-iam` |
| aws-terraform-iam-identity-center | IAM Identity Center | `redmatter/aws-terraform-iam-identity-center` |
| nbinternal-terraform-iam | Internal project IAM | `redmatter/nbinternal-terraform-iam` |

### Services
| Module | Description | Repository |
|--------|-------------|------------|
| aws-terraform-events | External Events service | `redmatter/aws-terraform-events` |
| aws-terraform-templates | Message Templates service | `redmatter/aws-terraform-templates` |
| aws-terraform-eci | ECI infrastructure | `redmatter/aws-terraform-eci` |
| aws-terraform-transfer-family | AWS Transfer Family | `redmatter/aws-terraform-transfer-family` |
| aws-terraform-sapien-proxy | Auth0-aware Sapien proxy | `redmatter/aws-terraform-sapien-proxy` |
| aws-terraform-graphiql | GraphiQL deployment | `redmatter/aws-terraform-graphiql` |

### Archiving
| Module | Description | Repository |
|--------|-------------|------------|
| terraform-nexus-archiving-purge | Archiving purge infrastructure | `redmatter/terraform-nexus-archiving-purge` |

### Data & Analytics
| Module | Description | Repository |
|--------|-------------|------------|
| nbinternal-terraform-data-lake | Internal data lake | `redmatter/nbinternal-terraform-data-lake` |
| terraform-rt-deepgram | Deepgram integration | `redmatter/terraform-rt-deepgram` |

### Other
| Module | Description | Repository |
|--------|-------------|------------|
| aws-terraform-tools | Utility tools | `redmatter/aws-terraform-tools` |
| aws-terraform-workshop | Workshop/training | `redmatter/aws-terraform-workshop` |
| terraform-omni-chat-widget | Chat widget | `redmatter/terraform-omni-chat-widget` |
| terraform-orca-security | Orca Security | `redmatter/terraform-orca-security` |

---

## Module Standards

*TODO: Document module standards and conventions*

### Required Files
- `README.md` - Module documentation
- `main.tf` - Primary configuration
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `versions.tf` - Provider version constraints

### Naming Conventions
- Repository: `aws-terraform-{service-name}`
- Variables: `snake_case`
- Resources: `{type}_{name}`

---

## Dependencies

*TODO: Create dependency graph between modules*

---

*Last updated: 2026-01-19*
