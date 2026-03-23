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
approval.action.approve

```

Naming rules:

- Dot-separated segments; each segment is **lowerCamelCase** (starts with a lowercase letter; inner words use capital letters, e.g. `salesOrder`, `purchaseOrder`).
- The first segment is the primary domain; further segments refine the resource or namespace before the action.
- At least two segments are required (`domain.action` minimum). Compound flows may use more segments (e.g. `approval.action.approve`).

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

### 5.1 ERP module directory layout

When capabilities are collected under an ERP module registry, use:

- `sample/caps/<capability.name>/capability.json` — definition file; `signature.*Schema` paths are relative to this directory.
- `sample/caps/<capability.name>/schemas/` — request, response, and error JSON Schemas for that capability.
- `sample/caps/<capability.name>/examples/` — machine-readable examples (success and failure where applicable).
- `sample/caps/<capability.name>/tests/contract-tests.yaml` — contract tests (and optional `tests/cases/*.yaml` — see **Scenarios** below).
- `sample/caps/_shared/schemas/` — cross-capability JSON Schemas, referenced with relative `$ref` from files under `sample/caps/<capability.name>/schemas/`.

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

### 7.5 Signature schema pointers

| Model             | `signature` fields (paths relative to `capability.json`) |
| ----------------- | -------------------------------------------------------- |
| request-response  | `requestSchema`, `responseSchema`, `errorSchema`         |
| query-execution   | `querySchema`, `responseSchema`, `errorSchema`           |
| ui-interaction    | `requestSchema`, `responseSchema`, `errorSchema`, `uiSchema` |
| event-handler     | `eventSchema`, `errorSchema`                             |

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

For packaged capabilities under `sample/caps/<capability.name>/`, the `examples` array in `capability.json` typically lists JSON files such as `examples/success.json` (happy path) and `examples/failure.json` (validation or domain error payload), each containing a `request` and either a `response` or an `error` object.

For **event-handler** capabilities, use an **`event`** object instead of `request` in those JSON files, and optionally a **`response`** ack object when the handler contract returns a processing acknowledgement (see `on.salesOrder.confirmed` in the module registry). Contract tests may still use a YAML `request:` block to supply the same payload shape for runners that expect a single input key.

---

# 12.1 Scenarios

Each capability may include a **`scenarios`** array in `capability.json`: real-world **instances** describing how the capability is used. Categories include **functional** flows (who does what, which other capabilities are involved) and **non_functional** expectations (security, performance, compliance, resilience). Use **`nfrTargets`** for measurable hints (e.g. max latency). This complements examples and tests: scenarios explain *why* and *under which constraints* the contract matters.

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
      code: NOT_FOUND
```

The **`tests`** object may also list **`caseFiles`**: paths (relative to the capability directory) to YAML files whose top-level key is **`cases:`** with the same per-entry shape as above. Use this for large conformance suites. Optional **`casesDirectory`** documents where those files live (e.g. `tests/cases`). Tools such as **captest** (under `utils/`) can execute `contractTests` and all **`caseFiles`** against an implementation.

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

# 15. Module implementations and platform references

Implementation modules (any language) are described by **ModuleSpec** (`spec/modulespec.md`, `schemas/modulespec.schema.json`); examples live under `sample/modules/`. The **memcos** reference runtime (`spec/memcos.md`, `util/memcos/`) provides in-memory capability routing, platform lifecycle events (`module.installed`, …), and an event bus for tests and demos.

---

# 16. Summary

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

