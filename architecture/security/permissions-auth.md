# Permissions and Authentication Architecture

## Overview

The Natterbox Platform implements a comprehensive permissions and authentication architecture built on industry-standard technologies. The system combines **Auth0** for identity management, **OpenFGA** for fine-grained authorization (FGA), and custom **Gatekeeper Lambda Authorizers** for API security.

This architecture provides:
- **Authentication**: Identity verification via Auth0 JWT tokens
- **Authorization**: Fine-grained access control via OpenFGA/NAPS
- **API Security**: Lambda-based JWT validation and IAM signature verification

---

## Architecture Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Client Applications                                │
│                    (Web Apps, Mobile Apps, Services)                         │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Auth0                                           │
│                    (Identity Provider / JWT Issuer)                          │
│              • User Authentication                                           │
│              • M2M Token Issuance                                           │
│              • Scope Management                                              │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │ JWT Tokens
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API Gateway                                          │
│                 (AWS API Gateway / AppSync)                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              Gatekeeper JWT Authorizer (Lambda)                      │   │
│  │  • JWT Validation & Verification                                     │   │
│  │  • Scope Extraction                                                  │   │
│  │  • OpenFGA Permission Check                                          │   │
│  │  • IAM Policy Generation                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NAPS (Natterbox Permissions Service)                      │
│                                                                              │
│  ┌─────────────────────────────┐   ┌─────────────────────────────────────┐ │
│  │        OpenFGA Service       │   │           API Gateway               │ │
│  │    (ECS Container Cluster)   │   │         (REST Endpoints)            │ │
│  │  • Authorization Model       │   │  • Permission Checks                │ │
│  │  • Relationship Storage      │   │  • Reverse Lookups                  │ │
│  │  • Permission Evaluation     │   │  • Model Management                 │ │
│  └─────────────────────────────┘   └─────────────────────────────────────┘ │
│                  │                                │                          │
│                  ▼                                ▼                          │
│  ┌─────────────────────────────┐   ┌─────────────────────────────────────┐ │
│  │    Aurora MySQL Serverless   │   │      DynamoDB FGA Cache            │ │
│  │    (OpenFGA Data Store)      │   │   (Reverse Lookup Cache)           │ │
│  └─────────────────────────────┘   └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. NAPS (Natterbox Permissions Service)

### Purpose

NAPS provides Fine-Grained Access Control (FGAC) across the Natterbox platform, implementing Relationship-Based Access Control (ReBAC) using OpenFGA. It enables granular permissions management at the object level, supporting complex hierarchical access patterns.

### Repository

- **GitHub**: `redmatter/naps`

### Key Features

| Feature | Description |
|---------|-------------|
| **Fine-Grained Access Control** | Control access at individual record, field, or operation level |
| **Context-Aware** | Access rules based on user role, location, time, device |
| **Dynamic Policies** | Rules that change based on conditions |
| **Relationship-Based** | Access conditional on relationships between users and objects |
| **Scalable** | Multi-region deployment with caching |

### Authorization Models Supported

NAPS supports three access control models:

1. **RBAC (Role-Based Access Control)**: Permissions assigned based on user roles (e.g., `editor`, `viewer`)

2. **ABAC (Attribute-Based Access Control)**: Permissions based on user/resource attributes (e.g., `marketing` + `manager`)

3. **ReBAC (Relationship-Based Access Control)**: Permissions based on relationships between users and objects (e.g., parent folder access)

ReBAC is the primary model, as it encompasses RBAC and can express ABAC when attributes are modeled as relationships.

### OpenFGA Configuration

NAPS uses OpenFGA (backed by Auth0/Okta) as the authorization engine. The service is deployed as:

- **OpenFGA Container**: Deployed on ECS Fargate
- **Data Store**: Aurora MySQL Serverless (multi-region capable)
- **Cache Layer**: DynamoDB for reverse lookups

#### OpenFGA Model Example

```dsl
model
  schema 1.1

type user

type folder
  relations
    define parent: [folder]
    define owner: [user]
    define writer: [user, group#member] or owner
    define commenter: [user, group#member] or writer
    define viewer: [user, group#member] or commenter

type conversation
  relations
    define parent: [folder]
    define owner: [user]
    define writer: [user, group#member] or owner
    define commenter: [user, group#member] or writer
    define viewer: [user, group#member] or commenter

type group
  relations
    define member: [user]
```

### Infrastructure

```hcl
# OpenFGA ECS Service Configuration
module "openfga" {
  source = "./openfga"
  
  # Multi-region deployment
  regions = ["us-east-2", "us-west-2"]
  
  # Database configuration
  database_type = "mysql"
  
  # Container configuration
  container_image = "openfga/openfga:latest"
  cpu             = 512
  memory          = 1024
}
```

### API Endpoints

NAPS exposes REST endpoints via API Gateway:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/check` | POST | Check if user has permission on object |
| `/write` | POST | Write new authorization tuple |
| `/read` | POST | Read existing tuples |
| `/expand` | POST | Expand permission tree |
| `/list-objects` | POST | List objects user can access |
| `/list-users` | POST | List users with access to object |

### API Security

The NAPS API uses two authentication methods:

1. **Gatekeeper JWT Authorizer**: For user-facing requests
2. **AWS IAM Signature (SigV4)**: For service-to-service communication

```yaml
# From api.yaml OpenAPI spec
securityDefinitions:
  GatekeeperJWTAuthoriser:
    type: apiKey
    name: Authorization
    in: header
    x-amazon-apigateway-authtype: custom
    x-amazon-apigateway-authorizer:
      type: request
      authorizerUri: ${gatekeeper_authorizer_invoke_arn}
      authorizerResultTtlInSeconds: 0
      identitySource: method.request.header.Authorization

  sigv4:
    type: apiKey
    name: Authorization
    in: header
    x-amazon-apigateway-authtype: awsSigv4
```

---

## 2. Gatekeeper Lambda Authorizer

### Purpose

The Gatekeeper Lambda Authorizer validates JWT tokens from Auth0 and generates IAM policies for API Gateway. It acts as the security boundary between clients and backend services.

### Implementation

The authorizer is deployed as a Lambda function configured via Terraform:

```hcl
# Gatekeeper Authorizer Configuration
variable "gatekeeper_lambda" {
  type = object({
    invoke_arn    = string
    function_name = string
  })
  description = "The Gatekeeper Lambda function details"
}

# API Gateway Authorizer
resource "aws_apigatewayv2_authorizer" "gatekeeper" {
  api_id                            = aws_apigatewayv2_api.api.id
  authorizer_type                   = "REQUEST"
  authorizer_uri                    = var.gatekeeper_lambda.invoke_arn
  authorizer_payload_format_version = "2.0"
  identity_sources                  = ["$request.header.Authorization"]
  name                              = "GatekeeperJWTAuthoriser"
  authorizer_result_ttl_in_seconds  = 0  # No caching for real-time validation
}
```

### Authorization Flow

```
1. Client Request
   │
   ▼
2. API Gateway receives request with Authorization header
   │
   ▼
3. Gatekeeper Lambda invoked
   │
   ├─► Extract JWT from Authorization header
   ├─► Validate JWT signature against Auth0 JWKS
   ├─► Extract claims (sub, aud, scope, org_id, etc.)
   ├─► Validate token expiry and audience
   │
   ▼
4. OpenFGA Permission Check (optional)
   │
   ├─► Query NAPS for fine-grained permissions
   ├─► Check user-object relationships
   │
   ▼
5. Generate IAM Policy
   │
   ├─► Allow: Generate policy allowing API invocation
   └─► Deny: Generate deny policy with error context
```

### Response Format

```json
{
  "isAuthorized": true,
  "context": {
    "userId": "auth0|123456789",
    "orgId": "org_abc123",
    "scopes": "read:conversations write:conversations",
    "email": "user@example.com"
  }
}
```

### AppSync Integration

For GraphQL APIs, the Gatekeeper pattern extends to AppSync Lambda authorizers:

```
Client Application
       │
       ▼ (API Key or JWT)
┌──────────────────────────┐
│    AWS AppSync API       │
│   (AWS_LAMBDA auth)      │
└──────────────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Shared Lambda Authorizer │
│  • API Key Validation    │
│  • JWT Validation        │
│  • OpenFGA Permission    │
└──────────────────────────┘
       │
       ▼
┌──────────────────────────┐
│   DynamoDB (API Keys)    │
│   OpenFGA (Permissions)  │
└──────────────────────────┘
```

---

## 3. Auth0 Integration

### Architecture

Auth0 serves as the central Identity Provider (IdP) for the Natterbox platform:

```
┌─────────────────────────────────────────────────────────────────┐
│                           Auth0                                  │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Applications   │  │      APIs       │  │   Organizations │ │
│  │  (M2M, SPA)     │  │   (Audiences)   │  │   (Tenants)     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Token Issuance                           ││
│  │  • User JWTs (interactive login)                            ││
│  │  • M2M JWTs (client credentials)                            ││
│  │  • Refresh Tokens                                           ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Token Types

#### User JWT (Interactive Login)

Issued when a user logs in via the UI:

```json
{
  "iss": "https://natterbox.eu.auth0.com/",
  "sub": "auth0|abc123",
  "aud": ["https://api.natterbox.net"],
  "iat": 1737385200,
  "exp": 1737471600,
  "scope": "openid profile email read:conversations",
  "org_id": "org_xyz789"
}
```

#### M2M JWT (Machine-to-Machine)

Issued for service-to-service communication:

```json
{
  "iss": "https://natterbox.eu.auth0.com/",
  "sub": "client123@clients",
  "aud": "https://naps.natterbox.net",
  "iat": 1737385200,
  "exp": 1737471600,
  "scope": "read:permissions write:permissions",
  "gty": "client-credentials"
}
```

### M2M Authentication Methods

#### 1. Client ID and Secret (Basic)

```bash
curl --request POST \
  --url https://natterbox.eu.auth0.com/oauth/token \
  --header 'content-type: application/json' \
  --data '{
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "audience": "https://api.natterbox.net",
    "grant_type": "client_credentials"
  }'
```

#### 2. Private Key JWT (Recommended)

More secure approach using asymmetric key pairs:

```
┌─────────────┐                    ┌─────────────┐
│   Client    │                    │   Auth0     │
│             │                    │   (Issuer)  │
└──────┬──────┘                    └──────┬──────┘
       │                                   │
       │ 1. Generate assertion JWT         │
       │    (signed with private key)      │
       │                                   │
       │ 2. POST /oauth/token              │
       │    client_assertion_type:         │
       │    urn:ietf:params:oauth:         │
       │    client-assertion-type:jwt-bearer
       │─────────────────────────────────►│
       │                                   │
       │                    3. Validate    │
       │                       assertion   │
       │                       signature   │
       │                                   │
       │◄─────────────────────────────────│
       │ 4. Signed session JWT             │
       │                                   │
```

### Scope-Based Authorization

Scopes define what operations a token allows:

| Scope | Description |
|-------|-------------|
| `read:conversations` | View conversations |
| `write:conversations` | Create/update conversations |
| `admin:organization` | Organization admin access |
| `cai:basic` | Basic CAI operations |
| `cai:admin` | CAI administrative operations |
| `lumina:basic` | Lumina basic access |

---

## 4. JWT Token Handling

### Token Validation Process

```python
# Pseudo-code for JWT validation
def validate_jwt(token: str) -> dict:
    # 1. Decode header (unverified)
    header = jwt.get_unverified_header(token)
    
    # 2. Fetch JWKS from Auth0
    jwks = fetch_jwks(f"{AUTH0_DOMAIN}/.well-known/jwks.json")
    
    # 3. Find matching key
    key = find_key(jwks, header['kid'])
    
    # 4. Verify signature and decode
    payload = jwt.decode(
        token,
        key,
        algorithms=['RS256'],
        audience=EXPECTED_AUDIENCE,
        issuer=AUTH0_DOMAIN
    )
    
    # 5. Validate claims
    validate_claims(payload)
    
    return payload
```

### Security Considerations

| Aspect | Implementation |
|--------|---------------|
| **Algorithm** | RS256 (asymmetric) |
| **Key Rotation** | JWKS endpoint with key rotation support |
| **Token Expiry** | Short-lived tokens (1 hour default) |
| **Audience Validation** | Strict audience checking |
| **Issuer Validation** | Validate against expected Auth0 domain |
| **Clock Skew** | Allow 30-second tolerance |

---

## 5. Permission Models

### Role-Based Access Control (RBAC)

Traditional role assignment:

```
User ────► Role ────► Permissions
```

**Example Roles:**
- `Basic` - Standard user access
- `Team Leader` - Team-level access
- `Admin` - Full administrative access

### Relationship-Based Access Control (ReBAC)

Permissions based on object relationships:

```
User ────► owns ────► Folder
                        │
                        ├── Subfolder
                        │      │
                        │      └── Conversation
                        │
                        └── Conversation
```

**Permission Inheritance:**
```
Folder (viewer: UserA)
   └── Subfolder (inherits from parent)
         └── Conversation (inherits from parent)

Result: UserA can view all nested objects
```

### Scope-Based Authorization (OpenFGA)

```
User ────► owns ────► API Key ────► has ────► Scope ────► can_execute ────► Operation
```

**Example:**
```
user:john owns apikey:abc123
apikey:abc123 has scope:cai:basic
scope:cai:basic can_execute query:getTools
```

---

## 6. Authorization Patterns

### Pattern 1: Basic FGA Check

Direct permission check for a specific operation:

```
┌─────────┐     ┌─────────────┐     ┌─────────┐     ┌─────────────┐
│  User   │────►│ API Gateway │────►│ Lambda  │────►│   OpenFGA   │
│ (Joe)   │     │             │     │         │     │   fga.check │
└─────────┘     └─────────────┘     └─────────┘     └─────────────┘
                                         │                 │
                                         │  "Can Joe view  │
                                         │   conv-1?"      │
                                         │◄────────────────┤
                                         │  allowed/denied │
```

**Code Example:**
```python
async def check_access(user_id: str, object_id: str, relation: str) -> bool:
    response = await fga_client.check({
        "tuple_key": {
            "user": f"user:{user_id}",
            "relation": relation,
            "object": f"conversation:{object_id}"
        }
    })
    return response.allowed
```

### Pattern 2: Publish by Permissions (Reverse Lookup)

Determine which users can access a given object (for WebSocket notifications):

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ EventBridge │────►│  WebSocket  │────►│    NAPS     │
│   Event     │     │   Lambda    │     │  list-users │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           │  "Who can access  │
                           │   conv-1?"        │
                           │◄──────────────────┤
                           │  [user1, user2]   │
                           │                   │
                           ▼
                    Send WebSocket
                    to each user
```

### Pattern 3: List Objects

Determine what objects a user can access:

```python
async def list_accessible_objects(user_id: str, object_type: str) -> list:
    response = await fga_client.list_objects({
        "user": f"user:{user_id}",
        "relation": "viewer",
        "type": object_type
    })
    return response.objects
```

---

## 7. API Key Management

### Generated API Keys (For External Access)

For external clients accessing GraphQL APIs without JWT capability:

```
┌──────────────────────────────────────────────────────────────┐
│                    API Key Lifecycle                          │
│                                                               │
│  1. Generate ────► 2. Store Hash ────► 3. Validate ────► 4. Expire
│     (bcrypt)         (DynamoDB)         (Lambda)          (TTL)
└──────────────────────────────────────────────────────────────┘
```

**Security Model:**
- **Show Once Policy**: Full key displayed only at generation
- **Bcrypt Hashing**: Keys stored as bcrypt hashes
- **Prefix Display**: Only first 5 characters shown in UI
- **TTL Expiration**: Automatic cleanup of expired keys

### Customer Provided Secrets

For integration with external REST tools:

```
┌─────────────────────────────────────────────────────────────┐
│                 Customer Secret Storage                      │
│                                                              │
│  • Full key stored in encrypted DynamoDB                     │
│  • IAM-only access via getFullKeyName query                  │
│  • Multi-region replication                                  │
│  • Used by CAI Rest, CAI WebSocket services                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Service Integration

### Internal Service Communication (IAM)

Services within the platform use IAM role assumption for NAPS access:

```hcl
# IAM Role Trust Policy
data "aws_iam_policy_document" "api_access_role_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${account_id}:root"]
    }
    
    condition {
      test     = "StringLike"
      variable = "aws:PrincipalTag/AllowedRoles"
      values   = ["*Naps_APIAccess*"]
    }
  }
}
```

### Cross-Service Authorization Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Calling        │     │     STS         │     │      NAPS       │
│  Service        │────►│  AssumeRole     │────►│      API        │
│                 │     │                 │     │                 │
│  AllowedRoles:  │     │  Temporary      │     │  SigV4 Auth     │
│  Naps_APIAccess │     │  Credentials    │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## 9. Multi-Region Deployment

### Regional Architecture

NAPS is deployed across multiple regions for low latency and high availability:

```
                    ┌─────────────────────────────────────┐
                    │           Route 53                   │
                    │    (Latency-based routing)           │
                    └─────────────────┬───────────────────┘
                                      │
           ┌──────────────────────────┼──────────────────────────┐
           │                          │                          │
           ▼                          ▼                          ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│    us-east-2        │   │     us-west-2       │   │     eu-west-1       │
│                     │   │                     │   │                     │
│  ┌───────────────┐  │   │  ┌───────────────┐  │   │  ┌───────────────┐  │
│  │ API Gateway   │  │   │  │ API Gateway   │  │   │  │ API Gateway   │  │
│  └───────────────┘  │   │  └───────────────┘  │   │  └───────────────┘  │
│         │           │   │         │           │   │         │           │
│  ┌───────────────┐  │   │  ┌───────────────┐  │   │  ┌───────────────┐  │
│  │ OpenFGA (ECS) │  │   │  │ OpenFGA (ECS) │  │   │  │ OpenFGA (ECS) │  │
│  └───────────────┘  │   │  └───────────────┘  │   │  └───────────────┘  │
│         │           │   │         │           │   │         │           │
│  ┌───────────────┐  │   │  ┌───────────────┐  │   │  ┌───────────────┐  │
│  │ Aurora MySQL  │  │   │  │ Aurora MySQL  │  │   │  │ Aurora MySQL  │  │
│  │  (Primary)    │──┼───┼──│  (Replica)    │──┼───┼──│  (Replica)    │  │
│  └───────────────┘  │   │  └───────────────┘  │   │  └───────────────┘  │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
```

### DynamoDB Global Tables

For the reverse lookup cache:

```hcl
resource "aws_dynamodb_table" "fga_cache" {
  name             = "naps-fga-cache"
  billing_mode     = "PAY_PER_REQUEST"
  hash_key         = "pk"
  range_key        = "sk"
  
  replica {
    region_name = "us-west-2"
  }
  
  replica {
    region_name = "eu-west-1"
  }
}
```

---

## 10. Implementation Guides

### Adding a New Permission Model

1. **Define the model in OpenFGA DSL:**
```dsl
type new_resource
  relations
    define owner: [user]
    define editor: [user, group#member] or owner
    define viewer: [user, group#member] or editor
```

2. **Deploy model update via Lambda:**
```go
// lambda/openfga-init/main.go
func updateModel(ctx context.Context, model string) error {
    // Write model to OpenFGA store
    return fgaClient.WriteAuthorizationModel(ctx, model)
}
```

3. **Add API endpoints:**
```yaml
# In api.yaml
/resources/{resourceId}/permissions:
  get:
    security:
      - GatekeeperJWTAuthoriser: []
```

### Integrating a New Service

1. **Add IAM role tag:**
```hcl
resource "aws_iam_role" "service_role" {
  name = "my-service-role"
  
  tags = {
    AllowedRoles = "Naps_APIAccess"
  }
}
```

2. **Configure SigV4 signing:**
```typescript
import { SignatureV4 } from "@aws-sdk/signature-v4";

const signer = new SignatureV4({
  service: "execute-api",
  region: "us-east-2",
  credentials: await getCredentials()
});

const signedRequest = await signer.sign(request);
```

3. **Make NAPS API calls:**
```typescript
const response = await fetch(`${NAPS_ENDPOINT}/check`, {
  method: "POST",
  headers: signedRequest.headers,
  body: JSON.stringify({
    tuple_key: {
      user: `user:${userId}`,
      relation: "viewer",
      object: `conversation:${convId}`
    }
  })
});
```

---

## Related Documentation

- [OpenFGA Documentation](https://openfga.dev/)
- [Auth0 Machine-to-Machine](https://auth0.com/docs/get-started/authentication-and-authorization-flow/client-credentials-flow)
- [AWS API Gateway Lambda Authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html)

## Source References

- **Repository**: `redmatter/naps`
- **Terraform Auth**: `redmatter/ideas-terraform-auth`
- **Confluence**: Authorization Management - Fine Grained Access Control
- **Confluence**: API Key Management Architecture with OpenFGA Authentication
