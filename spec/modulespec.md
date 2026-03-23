# ModuleSpec — implementation module contract

A **module** is a deployable unit of software that **implements** one or more **capabilities** (CapSpecs). The same capability may have multiple module implementations; the **platform** selects an implementation per routing policy.

`ModuleSpec` is metadata: it does **not** replace CapSpec JSON for individual capabilities; it **binds** a module id to the set of capability names it claims to satisfy and documents runtime and lifecycle expectations.

## File layout

- Recommended path: `sample/modules/<moduleId>/modulespec.json` (alongside code and tests).
- Validate with `schemas/modulespec.schema.json`.

## Fields (summary)

| Area | Meaning |
|------|---------|
| `module.id` | Unique module identifier in a tenant/deployment. |
| `module.version` | Artifact version (semver). |
| `module.implements` | List of **capability names** (`contact.get`, …) this module provides. |
| `module.requiresCapabilities` | Capabilities the module **calls** through the platform (routing to other implementations). |
| `module.runtime` | Language and entrypoint hints for loaders. |
| `module.lifecycle.handlesPlatformLifecycle` | If `true`, the module participates in **platform lifecycle events** (see `spec/memcos.md`). |

## Conformance testing

- Implementations are verified against CapSpecs using **captest** (`utils/captest`) and contract YAML under `sample/caps/<capability>/tests/`.
- `testing.captestPrefix` may narrow which capabilities under `sample/caps/` are run in CI for this module.

## Relationship to CapSpec

- **CapSpec** = contract for **one** capability (request/response schemas, semantics, tests).
- **ModuleSpec** = manifest for **one** module implementing **many** capabilities and declaring dependencies on others.
