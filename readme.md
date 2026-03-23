# Capability Description Specification

## 1. Overview

A **Capability** represents a standardized, callable contract that exposes a specific function of a system.  
Capabilities are the fundamental building blocks used by modules to provide functionality within the platform.

This specification defines how a capability must be described so that it can be:

- discovered
- validated
- tested
- implemented
- consumed by modules

A capability description **does not include permissions or dependency declarations**.  
Permissions belong to the runtime security layer, and dependencies belong to module definitions.

---

# 2. Core Principles

A capability definition must follow these principles:

### 2.1 Deterministic Contract

A capability must define a clear and deterministic contract consisting of:

- input schema
- output schema
- error schema
- execution semantics

### 2.2 Independent Definition

A capability definition must be **independent of module implementation**.

Modules implement capabilities, but the capability definition itself does not reference modules.

### 2.3 Stable Interface

Once released, a capability interface should remain stable across compatible versions.

### 2.4 Machine Verifiable

All capability definitions must be machine-readable and testable.

---

# 3. Capability Naming

Capabilities must use the following naming convention:

```

domain.action

```

Examples:

```

contact.get
contact.search
inventory.reserve
salesOrder.create
invoice.issue

```

Naming rules:

- lower case
- dot-separated
- first segment represents the domain
- second segment represents the action

---

# 4. Capability Versioning

Capabilities use **Semantic Versioning**:

```

MAJOR.MINOR.PATCH

```

Example:

```

contact.get 1.0.0

```

Versioning rules:

| Change Type | Version Change |
|-------------|---------------|
| Breaking change | MAJOR |
| Backward compatible addition | MINOR |
| Bug fix or correction | PATCH |

---

# 5. Capability Structure

Each capability must be described by a **capability definition file**.

```

capability.json

````

Example structure:

```json
{
  "capability": {
    "name": "contact.get",
    "version": "1.0.0",
    "category": "contact",
    "summary": "Retrieve a contact by identifier"
  },

  "type": "service",

  "signature": {
    "model": "request-response",
    "requestSchema": "schemas/request.json",
    "responseSchema": "schemas/response.json",
    "errorSchema": "schemas/error.json"
  },

  "semantics": {
    "idempotent": true,
    "sideEffect": false,
    "transactional": false
  },

  "examples": [
    "examples/example1.json"
  ],

  "tests": {
    "contractTests": "tests/contract-tests.yaml"
  }
}
````

---

# 6. Capability Types

A capability must declare its type.

Supported capability types include:

| Type          | Description                              |
| ------------- | ---------------------------------------- |
| service       | request-response operation               |
| event-handler | event consumer                           |
| data          | data query capability                    |
| resource      | file, storage, cache or queue operations |
| ui            | UI interaction capability                |
| integration   | external system interaction              |

Example:

```json
{
  "type": "service"
}
```

---

# 7. Capability Signature Models

Different capability types use different signature models.

### 7.1 Request–Response

Used for service operations.

```
Response handle(Request request)
```

Example:

```
contact.get
inventory.reserve
invoice.issue
```

---

### 7.2 Event Handler

Used for event-driven capabilities.

```
void onEvent(Event event)
```

Example:

```
on.salesOrder.confirmed
on.contact.created
```

---

### 7.3 Query Execution

Used for data access capabilities.

```
ResultSet execute(Query query)
```

Example:

```
data.sql.query
data.csql.query
```

---

### 7.4 UI Interaction

Used for UI capabilities.

```
UIModel handle(UIInput, UIAction, UIContext)
```

Example:

```
ui.widget.contact.selector
ui.view.salesOrder.detail
```

---

# 8. Request Schema

The request structure must be defined using **JSON Schema**.

Example:

```json
{
  "type": "object",
  "required": ["contactId"],
  "properties": {
    "contactId": {
      "type": "string"
    }
  }
}
```

---

# 9. Response Schema

The response structure must also use **JSON Schema**.

Example:

```json
{
  "type": "object",
  "required": ["contactId", "displayName"],
  "properties": {
    "contactId": {
      "type": "string"
    },
    "displayName": {
      "type": "string"
    },
    "avatar": {
      "type": "string"
    }
  }
}
```

---

# 10. Error Model

All capabilities must follow a unified error structure.

Example:

```json
{
  "type": "object",
  "required": ["code", "message"],
  "properties": {
    "code": {
      "type": "string"
    },
    "message": {
      "type": "string"
    },
    "retryable": {
      "type": "boolean"
    }
  }
}
```

Example error codes:

```
CONTACT_NOT_FOUND
INVALID_REQUEST
INTERNAL_ERROR
```

---

# 11. Capability Semantics

Capabilities must declare execution semantics.

Example:

```json
{
  "idempotent": true,
  "sideEffect": false,
  "transactional": false
}
```

Definitions:

| Field         | Meaning                                |
| ------------- | -------------------------------------- |
| idempotent    | repeated calls produce the same result |
| sideEffect    | modifies system state                  |
| transactional | must execute within a transaction      |

---

# 12. Examples

Each capability should include at least one example.

Example:

```json
{
  "request": {
    "contactId": "c1001"
  },
  "response": {
    "contactId": "c1001",
    "displayName": "Alice"
  }
}
```

---

# 13. Contract Tests

Each capability must include automated contract tests.

Example:

```yaml
tests:

  - name: contact-get-success
    request:
      contactId: "c1001"
    expect:
      status: success

  - name: contact-get-not-found
    request:
      contactId: "invalid"
    expectError:
      code: CONTACT_NOT_FOUND
```

These tests ensure that implementations conform to the capability contract.

---

# 14. Capability Lifecycle

Capabilities move through the following lifecycle stages:

```
Draft → Stable → Deprecated → Retired
```

| Stage      | Meaning               |
| ---------- | --------------------- |
| Draft      | under development     |
| Stable     | recommended for use   |
| Deprecated | scheduled for removal |
| Retired    | no longer supported   |

---

# 15. Summary

A capability description must include:

* name
* version
* type
* signature model
* request schema
* response schema
* error schema
* semantics
* examples
* contract tests

Capability definitions **must not include**:

* permission rules
* module dependencies

These concerns are handled separately by the runtime platform and module metadata.

