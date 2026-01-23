# Category Query Syntax Guide

## Overview

The Insight Category UI service provides a powerful query syntax system for defining categories that analyze call transcriptions. This query syntax enables customers to create sophisticated rules for categorizing calls based on spoken words, phrases, and logical combinations thereof.

The category query system is designed to work with the agnostic categorization engine, supporting multiple transcription partners while maintaining consistent syntax and behavior. Understanding this syntax is essential for creating effective category definitions that accurately capture the intent of call analysis requirements.

### Purpose and Scope

This guide covers:
- Basic syntax elements and their usage
- Word and phrase matching rules
- Logical operators and their precedence
- Complex query construction patterns
- Validation rules and constraints
- Error handling and troubleshooting
- Parser implementation details for developers extending the system

### Target Audience

This documentation is intended for:
- **Category Administrators**: Users creating and managing categories through the UI
- **Frontend Developers**: Engineers working on the category creation components
- **Integration Developers**: Teams integrating with the categorization API
- **QA Engineers**: Testing category query functionality

---

## Basic Syntax

The category query syntax follows a structured format that supports various matching patterns and logical operations. All queries are evaluated against transcription text to determine category membership.

### Syntax Elements

| Element | Description | Example |
|---------|-------------|---------|
| Word | Single word match | `refund` |
| Phrase | Multiple word sequence | `"request a refund"` |
| Operator | Logical combinator | `AND`, `OR`, `NOT` |
| Grouping | Precedence control | `(word1 OR word2)` |
| Proximity | Word distance matching | `"cancel NEAR/5 subscription"` |

### Case Sensitivity

By default, all query matching is **case-insensitive**. The following queries are equivalent:

```
refund
REFUND
Refund
```

### Whitespace Handling

Whitespace is normalized during parsing:
- Multiple spaces are collapsed to single spaces
- Leading and trailing whitespace is trimmed
- Newlines and tabs are converted to spaces

```typescript
// These queries are functionally identical
const query1 = "cancel    subscription";
const query2 = "cancel subscription";
```

---

## Words and Phrases

### Single Word Matching

Single words match any occurrence in the transcription text. Word boundaries are automatically respected.

```
refund
```

This matches:
- ✅ "I want a refund"
- ✅ "Can you process the refund?"
- ❌ "The refunding process" (matches "refund" stem, configurable)

### Phrase Matching

Phrases are enclosed in double quotes and match the exact sequence of words.

```
"request a refund"
```

This matches:
- ✅ "I would like to request a refund please"
- ❌ "I request that you give me a refund"

### Wildcard Patterns

Wildcards allow flexible matching within words:

| Wildcard | Description | Example | Matches |
|----------|-------------|---------|---------|
| `*` | Zero or more characters | `refund*` | refund, refunds, refunding |
| `?` | Single character | `colo?r` | color, colour |

```typescript
// Example: Match any word starting with "cancel"
const wildcardQuery = "cancel*";
// Matches: cancel, canceled, cancellation, cancelling
```

### Stemming Configuration

The query parser supports optional stemming to match word variations:

```typescript
interface QueryOptions {
  enableStemming: boolean;
  language: 'en' | 'es' | 'fr' | 'de';
}

// With stemming enabled
// Query: "run" matches "running", "runs", "ran"
```

---

## Logical Operators

### AND Operator

The `AND` operator requires both conditions to be present in the transcription.

```
refund AND complaint
```

Matches transcriptions containing **both** "refund" and "complaint".

```typescript
// TypeScript representation in the query builder
const andQuery: QueryNode = {
  type: 'AND',
  children: [
    { type: 'WORD', value: 'refund' },
    { type: 'WORD', value: 'complaint' }
  ]
};
```

### OR Operator

The `OR` operator matches if either condition is present.

```
refund OR return
```

Matches transcriptions containing "refund" **or** "return" (or both).

### NOT Operator

The `NOT` operator excludes matches containing the specified term.

```
refund AND NOT satisfied
```

Matches transcriptions with "refund" but **without** "satisfied".

### Operator Precedence

Operators are evaluated in the following order (highest to lowest):

1. `NOT` - Negation
2. `AND` - Conjunction
3. `OR` - Disjunction

Use parentheses to override default precedence:

```
// Without parentheses: NOT applied first, then AND, then OR
refund AND complaint OR return

// Equivalent to:
(refund AND complaint) OR return

// With explicit grouping:
refund AND (complaint OR return)
```

### Proximity Operator (NEAR)

The `NEAR` operator matches words within a specified distance:

```
"cancel NEAR/5 subscription"
```

Matches when "cancel" and "subscription" appear within 5 words of each other.

```typescript
// Proximity query configuration
interface ProximityQuery {
  term1: string;
  term2: string;
  maxDistance: number;
  ordered: boolean; // If true, term1 must appear before term2
}
```

---

## Complex Query Examples

### Example 1: Customer Complaint Detection

```
("very upset" OR "extremely frustrated" OR "terrible service") 
AND 
(refund OR compensation OR "speak to manager")
AND NOT
(resolved OR "thank you" OR satisfied)
```

This query identifies calls where:
- Customer expresses strong negative emotions
- Requests some form of resolution
- Issue is not yet resolved

### Example 2: Sales Opportunity Identification

```
(upgrade OR "premium plan" OR "additional features")
AND
(interested OR "tell me more" OR "how much")
AND NOT
("not interested" OR "no thank you" OR expensive)
```

### Example 3: Compliance Monitoring

```typescript
// Building complex queries programmatically
import { QueryBuilder } from '@insight/category-query';

const complianceQuery = new QueryBuilder()
  .phrase("terms and conditions")
  .and()
  .group(
    new QueryBuilder()
      .word("agree")
      .or()
      .word("accept")
      .or()
      .word("confirm")
  )
  .and()
  .not()
  .group(
    new QueryBuilder()
      .word("skip")
      .or()
      .phrase("not sure")
  )
  .build();

// Resulting query string:
// "terms and conditions" AND (agree OR accept OR confirm) AND NOT (skip OR "not sure")
```

### Example 4: Multi-Language Support

```typescript
// Query with language-specific configuration
const multiLangQuery: CategoryQuery = {
  query: 'cancelar OR "devolver el producto"',
  options: {
    language: 'es',
    enableStemming: true,
    caseSensitive: false
  }
};
```

---

## Validation Rules

### Syntax Validation

The query parser enforces strict syntax rules to ensure valid queries:

| Rule | Valid Example | Invalid Example | Error Code |
|------|---------------|-----------------|------------|
| Balanced parentheses | `(a OR b)` | `(a OR b` | `UNBALANCED_PARENS` |
| Balanced quotes | `"exact phrase"` | `"unclosed phrase` | `UNBALANCED_QUOTES` |
| Valid operators | `a AND b` | `a ANDOR b` | `INVALID_OPERATOR` |
| Non-empty terms | `refund` | `AND OR` | `EMPTY_TERM` |
| Maximum depth | 10 levels | 11+ levels | `MAX_DEPTH_EXCEEDED` |

### Semantic Validation

```typescript
interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

interface ValidationError {
  code: string;
  message: string;
  position: {
    start: number;
    end: number;
    line: number;
    column: number;
  };
  severity: 'error' | 'warning';
}

// Example validation
const validateQuery = (query: string): ValidationResult => {
  const errors: ValidationError[] = [];
  
  // Check for empty query
  if (!query.trim()) {
    errors.push({
      code: 'EMPTY_QUERY',
      message: 'Query cannot be empty',
      position: { start: 0, end: 0, line: 1, column: 1 },
      severity: 'error'
    });
  }
  
  // Check for balanced parentheses
  const parenBalance = countParentheses(query);
  if (parenBalance !== 0) {
    errors.push({
      code: 'UNBALANCED_PARENS',
      message: `Unbalanced parentheses: ${parenBalance > 0 ? 'missing closing' : 'missing opening'}`,
      position: findUnbalancedPosition(query),
      severity: 'error'
    });
  }
  
  return {
    isValid: errors.filter(e => e.severity === 'error').length === 0,
    errors,
    warnings: []
  };
};
```

### Query Length Limits

| Constraint | Limit | Configurable |
|------------|-------|--------------|
| Maximum query length | 10,000 characters | Yes |
| Maximum terms | 500 | Yes |
| Maximum nesting depth | 10 levels | Yes |
| Maximum phrase length | 100 words | Yes |

---

## Error Handling

### Error Types

The query parser provides detailed error information for troubleshooting:

```typescript
enum QueryErrorCode {
  // Syntax Errors
  SYNTAX_ERROR = 'SYNTAX_ERROR',
  UNBALANCED_PARENTHESES = 'UNBALANCED_PARENTHESES',
  UNBALANCED_QUOTES = 'UNBALANCED_QUOTES',
  INVALID_OPERATOR = 'INVALID_OPERATOR',
  UNEXPECTED_TOKEN = 'UNEXPECTED_TOKEN',
  
  // Semantic Errors
  EMPTY_QUERY = 'EMPTY_QUERY',
  EMPTY_GROUP = 'EMPTY_GROUP',
  DANGLING_OPERATOR = 'DANGLING_OPERATOR',
  
  // Limit Errors
  QUERY_TOO_LONG = 'QUERY_TOO_LONG',
  TOO_MANY_TERMS = 'TOO_MANY_TERMS',
  NESTING_TOO_DEEP = 'NESTING_TOO_DEEP'
}
```

### Error Messages and Recovery

```typescript
// Error handling in the UI component
const handleQueryError = (error: QueryError): void => {
  switch (error.code) {
    case QueryErrorCode.UNBALANCED_PARENTHESES:
      // Highlight the unbalanced section
      highlightError(error.position);
      showSuggestion('Add missing parenthesis at position ' + error.position.end);
      break;
      
    case QueryErrorCode.INVALID_OPERATOR:
      // Suggest valid operators
      showSuggestion('Valid operators are: AND, OR, NOT, NEAR');
      break;
      
    case QueryErrorCode.QUERY_TOO_LONG:
      // Show character count
      showWarning(`Query exceeds maximum length of ${MAX_QUERY_LENGTH} characters`);
      break;
      
    default:
      showGenericError(error.message);
  }
};
```

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `UNBALANCED_PARENTHESES` | Missing `(` or `)` | Review grouping and add missing parenthesis |
| `DANGLING_OPERATOR` | Operator without operand | Add term before/after operator |
| `EMPTY_GROUP` | Empty parentheses `()` | Add terms inside group or remove empty parens |
| `NESTING_TOO_DEEP` | Excessive nesting | Flatten query structure |

---

## Parser Implementation Details

### Architecture Overview

The query parser follows a multi-stage architecture:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Lexer     │ -> │   Parser    │ -> │  Validator  │ -> │  Optimizer  │
│  (Tokens)   │    │    (AST)    │    │  (Errors)   │    │ (Simplified)│
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Lexer Implementation

```typescript
// Token types
enum TokenType {
  WORD = 'WORD',
  PHRASE = 'PHRASE',
  AND = 'AND',
  OR = 'OR',
  NOT = 'NOT',
  NEAR = 'NEAR',
  LPAREN = 'LPAREN',
  RPAREN = 'RPAREN',
  EOF = 'EOF'
}

interface Token {
  type: TokenType;
  value: string;
  position: number;
}

class QueryLexer {
  private input: string;
  private position: number = 0;
  
  constructor(input: string) {
    this.input = input.trim();
  }
  
  tokenize(): Token[] {
    const tokens: Token[] = [];
    
    while (this.position < this.input.length) {
      this.skipWhitespace();
      
      if (this.position >= this.input.length) break;
      
      const char = this.input[this.position];
      
      if (char === '(') {
        tokens.push({ type: TokenType.LPAREN, value: '(', position: this.position });
        this.position++;
      } else if (char === ')') {
        tokens.push({ type: TokenType.RPAREN, value: ')', position: this.position });
        this.position++;
      } else if (char === '"') {
        tokens.push(this.readPhrase());
      } else {
        tokens.push(this.readWord());
      }
    }
    
    tokens.push({ type: TokenType.EOF, value: '', position: this.position });
    return tokens;
  }
  
  private readPhrase(): Token {
    const start = this.position;
    this.position++; // Skip opening quote
    
    let value = '';
    while (this.position < this.input.length && this.input[this.position] !== '"') {
      value += this.input[this.position];
      this.position++;
    }
    
    this.position++; // Skip closing quote
    return { type: TokenType.PHRASE, value, position: start };
  }
  
  private readWord(): Token {
    const start = this.position;
    let value = '';
    
    while (this.position < this.input.length && !this.isDelimiter(this.input[this.position])) {
      value += this.input[this.position];
      this.position++;
    }
    
    // Check if it's an operator
    const upperValue = value.toUpperCase();
    if (upperValue === 'AND') return { type: TokenType.AND, value, position: start };
    if (upperValue === 'OR') return { type: TokenType.OR, value, position: start };
    if (upperValue === 'NOT') return { type: TokenType.NOT, value, position: start };
    if (upperValue.startsWith('NEAR/')) return { type: TokenType.NEAR, value, position: start };
    
    return { type: TokenType.WORD, value, position: start };
  }
  
  private isDelimiter(char: string): boolean {
    return /[\s()]/.test(char);
  }
  
  private skipWhitespace(): void {
    while (this.position < this.input.length && /\s/.test(this.input[this.position])) {
      this.position++;
    }
  }
}
```

### AST Node Types

```typescript
type ASTNode = 
  | WordNode 
  | PhraseNode 
  | AndNode 
  | OrNode 
  | NotNode 
  | ProximityNode;

interface WordNode {
  type: 'WORD';
  value: string;
  wildcard: boolean;
}

interface PhraseNode {
  type: 'PHRASE';
  value: string;
  words: string[];
}

interface AndNode {
  type: 'AND';
  left: ASTNode;
  right: ASTNode;
}

interface OrNode {
  type: 'OR';
  left: ASTNode;
  right: ASTNode;
}

interface NotNode {
  type: 'NOT';
  operand: ASTNode;
}

interface ProximityNode {
  type: 'NEAR';
  left: ASTNode;
  right: ASTNode;
  distance: number;
  ordered: boolean;
}
```

### Redux Integration

```typescript
// Category query state slice
interface CategoryQueryState {
  currentQuery: string;
  parsedAST: ASTNode | null;
  validationResult: ValidationResult | null;
  isValidating: boolean;
  parseError: QueryError | null;
}

const categoryQuerySlice = createSlice({
  name: 'categoryQuery',
  initialState: {
    currentQuery: '',
    parsedAST: null,
    validationResult: null,
    isValidating: false,
    parseError: null
  } as CategoryQueryState,
  reducers: {
    setQuery: (state, action: PayloadAction<string>) => {
      state.currentQuery = action.payload;
    },
    setParseResult: (state, action: PayloadAction<{ ast: ASTNode; validation: ValidationResult }>) => {
      state.parsedAST = action.payload.ast;
      state.validationResult = action.payload.validation;
      state.parseError = null;
    },
    setParseError: (state, action: PayloadAction<QueryError>) => {
      state.parseError = action.payload;
      state.parsedAST = null;
    }
  }
});
```

---

## Best Practices

### Query Design Guidelines

1. **Start Simple**: Begin with basic word matches and add complexity as needed
2. **Use Grouping**: Always use parentheses to make operator precedence explicit
3. **Test Incrementally**: Validate each part of a complex query before combining
4. **Document Intent**: Add comments in the UI explaining what each query section targets
5. **Consider Performance**: Highly complex queries may impact categorization speed

### Performance Optimization

```typescript
// Query optimization example
const optimizeQuery = (ast: ASTNode): ASTNode => {
  // Flatten nested OR groups
  if (ast.type === 'OR') {
    const flattenedChildren = flattenOrNodes(ast);
    return { type: 'OR_GROUP', children: flattenedChildren };
  }
  
  // Remove redundant NOT NOT
  if (ast.type === 'NOT' && ast.operand.type === 'NOT') {
    return ast.operand.operand;
  }
  
  return ast;
};
```

---

## Related Documentation

- [Category Management API Reference](./api-reference.md)
- [Template System Guide](./templates.md)
- [User Assignment Documentation](./user-assignment.md)
- [Categorization Engine Integration](./categorization-engine.md)