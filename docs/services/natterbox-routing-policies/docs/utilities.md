# Utility Functions Reference

## Overview

The `natterbox-routing-policies` frontend application provides a comprehensive set of utility functions designed to streamline common operations across the routing policy management interface. These utilities handle everything from text manipulation and encoding to feature flag management and phone number processing.

This document serves as the definitive reference for all utility functions available in the application, providing detailed explanations, usage examples, parameter specifications, and best practices for each function.

## Text Utilities

### highlightMatchedText

The `highlightMatchedText` function is a core utility for the search and filtering functionality within the routing policies interface. It enables visual highlighting of matched search terms within text content, improving user experience when searching through large policy lists.

#### Function Signature

```typescript
function highlightMatchedText(
  text: string,
  searchTerm: string,
  options?: HighlightOptions
): React.ReactNode | string
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | `string` | Yes | The source text to search within |
| `searchTerm` | `string` | Yes | The term to find and highlight |
| `options` | `HighlightOptions` | No | Configuration options for highlighting behavior |

#### Options Interface

```typescript
interface HighlightOptions {
  caseSensitive?: boolean;      // Default: false
  highlightClass?: string;      // Default: 'highlight-match'
  maxHighlights?: number;       // Default: unlimited
  returnPlainText?: boolean;    // Default: false
}
```

#### Usage Examples

**Basic Usage:**

```tsx
import { highlightMatchedText } from '@/utils/textUtils';

const PolicyListItem = ({ policyName, searchQuery }) => {
  return (
    <div className="policy-item">
      <span className="policy-name">
        {highlightMatchedText(policyName, searchQuery)}
      </span>
    </div>
  );
};
```

**Advanced Usage with Options:**

```tsx
const SearchResults = ({ results, query }) => {
  return (
    <ul>
      {results.map((result) => (
        <li key={result.id}>
          {highlightMatchedText(result.name, query, {
            caseSensitive: false,
            highlightClass: 'search-highlight',
            maxHighlights: 3
          })}
        </li>
      ))}
    </ul>
  );
};
```

#### Return Value

Returns a `React.ReactNode` containing the original text with matched portions wrapped in `<mark>` elements, or the original string if no matches are found.

#### Edge Cases

- Returns original text unchanged if `searchTerm` is empty or null
- Handles special regex characters safely (escapes them automatically)
- Returns empty string if `text` is null or undefined

---

## Encoding Utilities

### md5Encode

The `md5Encode` function provides MD5 hashing capability, primarily used for generating cache keys, creating unique identifiers for policy configurations, and checksum validation.

#### Function Signature

```typescript
function md5Encode(input: string | object): string
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input` | `string \| object` | Yes | The data to encode |

#### Usage Examples

**String Encoding:**

```typescript
import { md5Encode } from '@/utils/encoding';

// Generate a cache key for policy data
const cacheKey = md5Encode(`policy-${policyId}-${version}`);
// Returns: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

// Use in API requests
const fetchPolicy = async (policyId: string) => {
  const etag = md5Encode(JSON.stringify(localPolicyData));
  const response = await fetch(`/api/policies/${policyId}`, {
    headers: {
      'If-None-Match': etag
    }
  });
  return response;
};
```

**Object Encoding:**

```typescript
// Create a checksum for policy configuration
const policyConfig = {
  name: 'Customer Support Routing',
  rules: [
    { type: 'date', condition: 'business_hours' },
    { type: 'selection', condition: 'department' }
  ]
};

const configChecksum = md5Encode(policyConfig);
```

#### Implementation Notes

- Objects are automatically serialized using `JSON.stringify()` with sorted keys for consistent hashing
- Uses a lightweight MD5 implementation optimized for browser environments
- **Security Note:** MD5 should not be used for cryptographic purposes; use only for checksums and cache keys

---

## Data Extraction Utilities

### extractKeys

The `extractKeys` function is a powerful utility for extracting specific keys from complex nested data structures, particularly useful when working with routing policy configurations and variable definitions.

#### Function Signature

```typescript
function extractKeys<T>(
  data: object | object[],
  keys: string[],
  options?: ExtractOptions
): T[]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `data` | `object \| object[]` | Yes | Source data to extract from |
| `keys` | `string[]` | Yes | Array of key names to extract |
| `options` | `ExtractOptions` | No | Extraction configuration |

#### Options Interface

```typescript
interface ExtractOptions {
  deep?: boolean;           // Recursively search nested objects
  includeNull?: boolean;    // Include keys with null values
  flatten?: boolean;        // Flatten nested results
  unique?: boolean;         // Remove duplicate values
}
```

#### Usage Examples

**Basic Extraction:**

```typescript
import { extractKeys } from '@/utils/dataExtraction';

const routingRules = [
  { id: 1, name: 'Rule A', type: 'date', priority: 1 },
  { id: 2, name: 'Rule B', type: 'string', priority: 2 },
  { id: 3, name: 'Rule C', type: 'number', priority: 1 }
];

const ruleNames = extractKeys(routingRules, ['name']);
// Returns: [{ name: 'Rule A' }, { name: 'Rule B' }, { name: 'Rule C' }]

const multipleKeys = extractKeys(routingRules, ['id', 'type']);
// Returns: [{ id: 1, type: 'date' }, { id: 2, type: 'string' }, ...]
```

**Deep Extraction from Nested Structures:**

```typescript
const policyData = {
  policy: {
    name: 'Main Policy',
    routes: [
      {
        destination: { agentId: 'agent-001', queue: 'support' },
        conditions: { type: 'date', value: 'weekday' }
      },
      {
        destination: { agentId: 'agent-002', queue: 'sales' },
        conditions: { type: 'selection', value: 'vip' }
      }
    ]
  }
};

const agentIds = extractKeys(policyData, ['agentId'], { 
  deep: true, 
  unique: true 
});
// Returns: ['agent-001', 'agent-002']
```

#### Common Use Cases

1. **Extracting variable names** from routing configurations
2. **Collecting all agent IDs** referenced in a policy
3. **Building dropdown options** from complex data structures
4. **Validating required fields** exist in imported configurations

---

## Feature Flags Utilities

### featureFlagsHelper

The `featureFlagsHelper` provides a comprehensive interface for working with feature flags throughout the application, enabling gradual feature rollouts and A/B testing capabilities.

#### API Reference

```typescript
const featureFlagsHelper = {
  isEnabled: (flagName: string, context?: FlagContext) => boolean,
  getValue: <T>(flagName: string, defaultValue: T) => T,
  getAllFlags: () => Record<string, boolean | string | number>,
  refresh: () => Promise<void>,
  subscribe: (callback: FlagChangeCallback) => UnsubscribeFn
};
```

#### Methods

##### isEnabled

Checks if a specific feature flag is enabled.

```typescript
import { featureFlagsHelper } from '@/utils/featureFlags';

// Basic usage
if (featureFlagsHelper.isEnabled('ai_routing_enabled')) {
  // Render AI routing configuration options
}

// With context (user/organization specific)
const showAdvancedFeatures = featureFlagsHelper.isEnabled('advanced_routing', {
  userId: currentUser.id,
  organizationId: currentUser.orgId,
  environment: process.env.NODE_ENV
});
```

##### getValue

Retrieves the value of a feature flag with type safety.

```typescript
// Get numeric limit
const maxRoutes = featureFlagsHelper.getValue('max_routing_rules', 10);

// Get string configuration
const defaultCountry = featureFlagsHelper.getValue('default_country_code', 'US');
```

##### subscribe

Subscribe to feature flag changes for real-time updates.

```typescript
useEffect(() => {
  const unsubscribe = featureFlagsHelper.subscribe((changedFlags) => {
    console.log('Flags updated:', changedFlags);
    // Update component state accordingly
  });

  return () => unsubscribe();
}, []);
```

#### Available Feature Flags

| Flag Name | Type | Description |
|-----------|------|-------------|
| `ai_routing_enabled` | boolean | Enables AI-powered routing configurations |
| `policy_snapshots_enabled` | boolean | Enables policy versioning and snapshots |
| `advanced_variable_types` | boolean | Enables boolean and selection variable types |
| `max_routing_rules` | number | Maximum rules per policy |
| `beta_features` | boolean | Enables experimental features |

---

## UI Helper Utilities

### getPlaceholder

Generates contextually appropriate placeholder text for form inputs based on field type and routing variable configuration.

#### Function Signature

```typescript
function getPlaceholder(
  fieldType: VariableType,
  fieldName?: string,
  options?: PlaceholderOptions
): string
```

#### Usage Examples

```typescript
import { getPlaceholder } from '@/utils/uiHelpers';

// In a dynamic form component
const RoutingVariableInput = ({ variable }) => {
  const placeholder = getPlaceholder(variable.type, variable.name);
  
  return (
    <input
      type={variable.type === 'number' ? 'number' : 'text'}
      placeholder={placeholder}
      name={variable.name}
    />
  );
};

// Examples by type:
getPlaceholder('date');       // "Select a date (YYYY-MM-DD)"
getPlaceholder('string');     // "Enter text value"
getPlaceholder('number');     // "Enter numeric value"
getPlaceholder('boolean');    // "Select true or false"
getPlaceholder('selection');  // "Choose from available options"
```

### renderLabelWithAsterisk

Renders form labels with required field indicators, maintaining consistent styling across the application.

#### Function Signature

```typescript
function renderLabelWithAsterisk(
  label: string,
  isRequired?: boolean,
  tooltipText?: string
): React.ReactNode
```

#### Usage Examples

```tsx
import { renderLabelWithAsterisk } from '@/utils/uiHelpers';

const PolicyForm = () => {
  return (
    <form>
      <label>
        {renderLabelWithAsterisk('Policy Name', true)}
        <input type="text" name="policyName" required />
      </label>
      
      <label>
        {renderLabelWithAsterisk(
          'Description', 
          false, 
          'Optional description for this routing policy'
        )}
        <textarea name="description" />
      </label>
      
      <label>
        {renderLabelWithAsterisk(
          'AI Configuration',
          true,
          'Required when AI routing is enabled'
        )}
        <select name="aiConfig" required>
          {/* options */}
        </select>
      </label>
    </form>
  );
};
```

#### Rendered Output

```html
<!-- Required field -->
<span class="form-label">
  Policy Name
  <span class="required-indicator" aria-label="required">*</span>
</span>

<!-- Optional with tooltip -->
<span class="form-label">
  Description
  <span class="tooltip-icon" title="Optional description...">ℹ</span>
</span>
```

---

## Policy Utilities

### generatePolicySnapshot

Creates immutable snapshots of routing policies for versioning, audit trails, and rollback capabilities.

#### Function Signature

```typescript
function generatePolicySnapshot(
  policy: RoutingPolicy,
  options?: SnapshotOptions
): PolicySnapshot
```

#### Interfaces

```typescript
interface SnapshotOptions {
  author?: string;
  comment?: string;
  includeMetadata?: boolean;
  compressionEnabled?: boolean;
}

interface PolicySnapshot {
  id: string;
  policyId: string;
  version: number;
  timestamp: string;
  checksum: string;
  data: RoutingPolicy;
  metadata?: SnapshotMetadata;
}
```

#### Usage Examples

```typescript
import { generatePolicySnapshot } from '@/utils/policyUtils';

// Create a snapshot before making changes
const createSnapshot = async (policy: RoutingPolicy) => {
  const snapshot = generatePolicySnapshot(policy, {
    author: currentUser.email,
    comment: 'Pre-modification snapshot',
    includeMetadata: true
  });

  // Save to backend
  await api.saveSnapshot(snapshot);
  
  return snapshot;
};

// Compare snapshots
const compareSnapshots = (before: PolicySnapshot, after: PolicySnapshot) => {
  if (before.checksum !== after.checksum) {
    console.log('Policy has been modified');
    // Show diff view
  }
};
```

#### Snapshot Workflow

```typescript
// Complete versioning workflow
const policyVersioningWorkflow = async (policyId: string, changes: Partial<RoutingPolicy>) => {
  // 1. Load current policy
  const currentPolicy = await api.getPolicy(policyId);
  
  // 2. Create pre-change snapshot
  const beforeSnapshot = generatePolicySnapshot(currentPolicy, {
    comment: 'Automatic snapshot before edit'
  });
  
  // 3. Apply changes
  const updatedPolicy = { ...currentPolicy, ...changes };
  
  // 4. Create post-change snapshot
  const afterSnapshot = generatePolicySnapshot(updatedPolicy, {
    comment: `Updated: ${Object.keys(changes).join(', ')}`
  });
  
  // 5. Save both snapshots and updated policy
  await Promise.all([
    api.saveSnapshot(beforeSnapshot),
    api.saveSnapshot(afterSnapshot),
    api.updatePolicy(policyId, updatedPolicy)
  ]);
  
  return { beforeSnapshot, afterSnapshot, policy: updatedPolicy };
};
```

---

## Phone Utilities

### determineCountryCodePrefix

Intelligently determines the country code prefix for phone numbers, supporting the international telephony requirements of the Natterbox platform.

#### Function Signature

```typescript
function determineCountryCodePrefix(
  phoneNumber: string,
  options?: CountryCodeOptions
): CountryCodeResult
```

#### Interfaces

```typescript
interface CountryCodeOptions {
  defaultCountry?: string;      // ISO 3166-1 alpha-2 code
  strict?: boolean;             // Require valid country code
  includeDialingCode?: boolean; // Include + prefix
}

interface CountryCodeResult {
  countryCode: string;          // e.g., 'US', 'GB'
  dialingCode: string;          // e.g., '+1', '+44'
  nationalNumber: string;       // Number without country code
  isValid: boolean;
  confidence: 'high' | 'medium' | 'low';
}
```

#### Usage Examples

```typescript
import { determineCountryCodePrefix } from '@/utils/phoneUtils';

// Basic usage
const result = determineCountryCodePrefix('+1-555-123-4567');
// Returns: {
//   countryCode: 'US',
//   dialingCode: '+1',
//   nationalNumber: '5551234567',
//   isValid: true,
//   confidence: 'high'
// }

// UK number
const ukResult = determineCountryCodePrefix('+44 20 7946 0958');
// Returns: {
//   countryCode: 'GB',
//   dialingCode: '+44',
//   nationalNumber: '2079460958',
//   isValid: true,
//   confidence: 'high'
// }

// Number without country code (uses default)
const localResult = determineCountryCodePrefix('555-123-4567', {
  defaultCountry: 'US'
});
```

#### Integration with Routing Policies

```typescript
// Use in routing rule configuration
const configurePhoneRouting = (incomingNumber: string) => {
  const phoneInfo = determineCountryCodePrefix(incomingNumber);
  
  return {
    routeTo: phoneInfo.countryCode === 'GB' ? 'uk-support-queue' : 'us-support-queue',
    priority: phoneInfo.confidence === 'high' ? 1 : 2,
    metadata: {
      originalNumber: incomingNumber,
      normalizedNumber: phoneInfo.dialingCode + phoneInfo.nationalNumber
    }
  };
};
```

---

## Date Utilities

### formatDate

Formats dates consistently across the application, supporting multiple output formats and localization.

#### Function Signature

```typescript
function formatDate(
  date: Date | string | number,
  format?: DateFormat,
  options?: FormatOptions
): string
```

#### Supported Formats

| Format | Example Output |
|--------|----------------|
| `'short'` | `12/25/2024` |
| `'medium'` | `Dec 25, 2024` |
| `'long'` | `December 25, 2024` |
| `'full'` | `Wednesday, December 25, 2024` |
| `'iso'` | `2024-12-25T00:00:00.000Z` |
| `'relative'` | `2 days ago` |
| `'time'` | `2:30 PM` |
| `'datetime'` | `Dec 25, 2024, 2:30 PM` |

#### Usage Examples

```typescript
import { formatDate } from '@/utils/dateUtils';

// Various format examples
formatDate(new Date(), 'short');     // "12/25/2024"
formatDate(new Date(), 'relative');  // "just now"
formatDate('2024-01-15', 'long');    // "January 15, 2024"

// With localization
formatDate(new Date(), 'long', { locale: 'de-DE' }); // "25. Dezember 2024"

// In policy snapshot display
const SnapshotInfo = ({ snapshot }) => (
  <div className="snapshot-meta">
    <span>Created: {formatDate(snapshot.timestamp, 'datetime')}</span>
    <span>({formatDate(snapshot.timestamp, 'relative')})</span>
  </div>
);
```

### isEpochTime

Validates and identifies epoch timestamp values, crucial for handling legacy data and API responses.

#### Function Signature

```typescript
function isEpochTime(value: unknown): value is number
```

#### Usage Examples

```typescript
import { isEpochTime, formatDate } from '@/utils/dateUtils';

// Validate and convert epoch times
const normalizeTimestamp = (timestamp: unknown): Date => {
  if (isEpochTime(timestamp)) {
    // Convert epoch (seconds or milliseconds)
    const ms = timestamp > 9999999999 ? timestamp : timestamp * 1000;
    return new Date(ms);
  }
  
  if (typeof timestamp === 'string') {
    return new Date(timestamp);
  }
  
  throw new Error('Invalid timestamp format');
};

// Usage in data processing
const processApiResponse = (data: PolicyApiResponse) => {
  return {
    ...data,
    createdAt: isEpochTime(data.created_at) 
      ? new Date(data.created_at * 1000)
      : new Date(data.created_at),
    updatedAt: isEpochTime(data.updated_at)
      ? new Date(data.updated_at * 1000)
      : new Date(data.updated_at)
  };
};
```

---

## General Helpers

### Additional Utility Functions

#### debounce

Rate-limits function execution for search inputs and API calls.

```typescript
import { debounce } from '@/utils/helpers';

const SearchInput = () => {
  const debouncedSearch = debounce((query: string) => {
    fetchPolicies({ search: query });
  }, 300);

  return (
    <input 
      type="search"
      onChange={(e) => debouncedSearch(e.target.value)}
      placeholder="Search policies..."
    />
  );
};
```

#### deepClone

Creates deep copies of policy configurations for editing.

```typescript
import { deepClone } from '@/utils/helpers';

const editPolicy = (policy: RoutingPolicy) => {
  const workingCopy = deepClone(policy);
  // Modify workingCopy without affecting original
  return workingCopy;
};
```

#### isEmpty

Checks for empty values across different types.

```typescript
import { isEmpty } from '@/utils/helpers';

isEmpty(null);        // true
isEmpty(undefined);   // true
isEmpty('');          // true
isEmpty([]);          // true
isEmpty({});          // true
isEmpty('hello');     // false
isEmpty([1, 2, 3]);   // false
```

#### generateUniqueId

Creates unique identifiers for new routing rules and policies.

```typescript
import { generateUniqueId } from '@/utils/helpers';

const createNewRule = (): RoutingRule => ({
  id: generateUniqueId('rule'),  // "rule_a1b2c3d4e5"
  name: '',
  type: 'string',
  conditions: []
});
```

---

## Best Practices

### Performance Considerations

1. **Memoize expensive operations**: Use `useMemo` or `useCallback` with utility functions that process large datasets
2. **Debounce search operations**: Always debounce `highlightMatchedText` when used with live search
3. **Cache MD5 results**: Store computed checksums to avoid redundant calculations

### Error Handling

```typescript
// Always wrap utility calls in try-catch for production code
try {
  const snapshot = generatePolicySnapshot(policy);
} catch (error) {
  console.error('Failed to generate snapshot:', error);
  notifyUser('Unable to create policy snapshot');
}
```

### Type Safety

All utility functions are fully typed. Leverage TypeScript's type inference:

```typescript
// TypeScript will infer the correct return type
const result = extractKeys<{ id: string; name: string }>(data, ['id', 'name']);
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `highlightMatchedText` returns no highlights | Special characters in search term | Enable `escapeRegex` option |
| `determineCountryCodePrefix` returns low confidence | Ambiguous number format | Provide `defaultCountry` option |
| `formatDate` shows incorrect time | Timezone mismatch | Specify timezone in options |
| `generatePolicySnapshot` is slow | Large policy with many rules | Enable `compressionEnabled` option |

---

## Related Documentation

- [Data Models Reference](./data-models.md)
- [API Integration Guide](./api-integration.md)
- [Configuration Variables](./configuration.md)
- [Component Library](./components.md)