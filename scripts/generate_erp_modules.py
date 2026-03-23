#!/usr/bin/env python3
"""Generate ERP CapSpec capability trees under sample/caps/. Run from repo root: python3 scripts/generate_erp_modules.py"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPS = ROOT / "sample" / "caps"
ERR_REF = {"$ref": "../../_shared/schemas/erp-error.json"}
PAGE_REQ = {"$ref": "../../_shared/schemas/page-request.json"}
PAGE_RES = {"$ref": "../../_shared/schemas/page-response.json"}


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_yaml(path: Path, tests: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["tests:"]
    for t in tests:
        lines.append(f"  - name: {t['name']}")
        lines.append("    request:")
        for k, v in t["request"].items():
            lines.append(f"      {k}: {json.dumps(v)}")
        if "expect" in t:
            lines.append("    expect:")
            for k, v in t["expect"].items():
                lines.append(f"      {k}: {json.dumps(v)}")
        if "expectError" in t:
            lines.append("    expectError:")
            for k, v in t["expectError"].items():
                lines.append(f"      {k}: {json.dumps(v)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_cases_yaml(path: Path, cases: list[dict]) -> None:
    """Write tests/cases/*.yaml with top-level `cases:` (for captest extended suites)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["cases:"]
    for c in cases:
        lines.append(f"  - name: {c['name']}")
        if "request" in c:
            lines.append("    request:")
            for k, v in c["request"].items():
                lines.append(f"      {k}: {json.dumps(v)}")
        if "expect" in c:
            lines.append("    expect:")
            for k, v in c["expect"].items():
                lines.append(f"      {k}: {json.dumps(v)}")
        if "expectError" in c:
            lines.append("    expectError:")
            for k, v in c["expectError"].items():
                lines.append(f"      {k}: {json.dumps(v)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def emit_module(
    name: str,
    *,
    category: str,
    summary: str,
    capability_type: str,
    signature: dict,
    schema_files: dict[str, object],
    examples: list[dict],
    tests: list[dict],
    idempotent: bool,
    side_effect: bool,
    transactional: bool,
    lifecycle: str,
) -> None:
    """Emit a capability tree with arbitrary schema files (e.g. data / ui signatures)."""
    base = CAPS / name
    for rel in sorted(schema_files.keys()):
        write_json(base / rel, schema_files[rel])
    ex_dir = base / "examples"
    example_paths: list[str] = []
    default_names = ["success.json", "failure.json"]
    for i, ex in enumerate(examples):
        fname = default_names[i] if i < len(default_names) else f"example-{i + 1}.json"
        write_json(ex_dir / fname, ex)
        example_paths.append(f"examples/{fname}")
    write_json(
        base / "capability.json",
        {
            "capability": {
                "name": name,
                "version": "1.0.0",
                "category": category,
                "summary": summary,
                "lifecycle": lifecycle,
            },
            "type": capability_type,
            "signature": signature,
            "semantics": {
                "idempotent": idempotent,
                "sideEffect": side_effect,
                "transactional": transactional,
            },
            "examples": example_paths,
            "tests": {"contractTests": "tests/contract-tests.yaml"},
        },
    )
    write_yaml(base / "tests" / "contract-tests.yaml", tests)


def emit_capability(
    name: str,
    *,
    category: str,
    summary: str,
    idempotent: bool,
    side_effect: bool,
    transactional: bool,
    lifecycle: str,
    request: dict,
    response: dict,
    examples: list[dict],
    tests: list[dict],
    capability_type: str = "service",
    scenarios: list[dict] | None = None,
    case_suites: list[tuple[str, list[dict]]] | None = None,
) -> None:
    base = CAPS / name
    write_json(base / "schemas" / "request.json", request)
    write_json(base / "schemas" / "response.json", response)
    write_json(base / "schemas" / "error.json", ERR_REF)
    ex_dir = base / "examples"
    example_paths: list[str] = []
    default_names = ["success.json", "failure.json"]
    for i, ex in enumerate(examples):
        fname = default_names[i] if i < len(default_names) else f"example-{i + 1}.json"
        write_json(ex_dir / fname, ex)
        example_paths.append(f"examples/{fname}")
    tests_block: dict = {"contractTests": "tests/contract-tests.yaml"}
    case_paths: list[str] = []
    if case_suites:
        for rel, cases in case_suites:
            write_cases_yaml(base / rel, cases)
            case_paths.append(rel)
        tests_block["caseFiles"] = case_paths
        tests_block["casesDirectory"] = "tests/cases"
    cap_payload: dict = {
        "capability": {
            "name": name,
            "version": "1.0.0",
            "category": category,
            "summary": summary,
            "lifecycle": lifecycle,
        },
        "type": capability_type,
        "signature": {
            "model": "request-response",
            "requestSchema": "schemas/request.json",
            "responseSchema": "schemas/response.json",
            "errorSchema": "schemas/error.json",
        },
        "semantics": {
            "idempotent": idempotent,
            "sideEffect": side_effect,
            "transactional": transactional,
        },
        "examples": example_paths,
        "tests": tests_block,
    }
    if scenarios:
        cap_payload["scenarios"] = scenarios
    write_json(base / "capability.json", cap_payload)
    write_yaml(base / "tests" / "contract-tests.yaml", tests)


def main() -> None:
    CAPS.mkdir(parents=True, exist_ok=True)

    from erp_resources import emit_resource_capabilities

    emit_resource_capabilities(emit_capability)

    # --- Platform ---
    emit_capability(
        "identity.current.get",
        category="identity",
        summary="Return the authenticated principal for the active session or token.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "tenantId": {
                    "type": "string",
                    "description": "Optional explicit tenant when the subject spans tenants.",
                }
            },
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["subjectId", "subjectType"],
            "properties": {
                "subjectId": {"type": "string"},
                "subjectType": {
                    "type": "string",
                    "enum": ["user", "service", "apiKey"],
                },
                "displayName": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "orgUnitIds": {"type": "array", "items": {"type": "string"}},
                "attributes": {"type": "object", "additionalProperties": True},
            },
        },
        examples=[
            {
                "title": "current user",
                "request": {},
                "response": {
                    "subjectId": "usr-1001",
                    "subjectType": "user",
                    "displayName": "Alice",
                    "email": "alice@example.com",
                    "orgUnitIds": ["ou-east"],
                },
            },
            {
                "title": "unauthenticated",
                "request": {},
                "error": {"code": "UNAUTHORIZED", "message": "Missing or invalid credentials"},
            },
        ],
        tests=[
            {
                "name": "identity-current-ok",
                "request": {},
                "expect": {"status": "success"},
            },
            {
                "name": "identity-current-unauthorized",
                "request": {},
                "expectError": {"code": "UNAUTHORIZED"},
            },
        ],
    )

    emit_capability(
        "auth.permission.check",
        category="auth",
        summary="Evaluate whether the active subject is allowed a permission on an optional resource.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["permission"],
            "properties": {
                "permission": {"type": "string"},
                "resourceType": {"type": "string"},
                "resourceId": {"type": "string"},
                "context": {"type": "object", "additionalProperties": True},
            },
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["allowed"],
            "properties": {
                "allowed": {"type": "boolean"},
                "reason": {"type": "string"},
            },
        },
        examples=[
            {
                "request": {"permission": "salesOrder.read", "resourceId": "so-9"},
                "response": {"allowed": True},
            },
            {
                "request": {"permission": "gl.post"},
                "response": {"allowed": False, "reason": "Missing accountant role"},
            },
        ],
        tests=[
            {
                "name": "auth-permission-allowed",
                "request": {
                    "permission": "salesOrder.read",
                    "resourceId": "so-9",
                },
                "expect": {"status": "success"},
            },
            {
                "name": "auth-permission-denied",
                "request": {"permission": "gl.post", "resourceId": "je-1"},
                "expect": {"status": "success"},
            },
        ],
    )

    emit_capability(
        "id.generate",
        category="platform",
        summary="Allocate one or more unique identifiers using a server-side scheme.",
        idempotent=False,
        side_effect=True,
        transactional=False,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["scheme"],
            "properties": {
                "scheme": {"type": "string", "enum": ["uuid", "snowflake", "sequential"]},
                "count": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 1},
                "namespace": {
                    "type": "string",
                    "description": "Optional logical namespace for sequential ids.",
                },
            },
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["ids"],
            "properties": {"ids": {"type": "array", "items": {"type": "string"}, "minItems": 1}},
        },
        examples=[
            {"request": {"scheme": "uuid", "count": 2}, "response": {"ids": ["a1b2c3", "d4e5f6"]}},
            {
                "request": {"scheme": "unknown"},
                "error": {"code": "INVALID_REQUEST", "message": "Unsupported scheme"},
            },
        ],
        tests=[
            {
                "name": "id-generate-uuid",
                "request": {"scheme": "uuid", "count": 1},
                "expect": {"status": "success"},
            },
            {
                "name": "id-generate-invalid-scheme",
                "request": {"scheme": "unknown"},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    emit_capability(
        "event.publish",
        category="platform",
        summary="Publish a domain event to the platform event bus for subscribers.",
        idempotent=False,
        side_effect=True,
        transactional=False,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["topic", "payload"],
            "properties": {
                "topic": {"type": "string"},
                "payload": {"type": "object", "additionalProperties": True},
                "correlationId": {"type": "string"},
                "causationId": {"type": "string"},
            },
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["eventId", "publishedAt"],
            "properties": {
                "eventId": {"type": "string"},
                "publishedAt": {"type": "string", "format": "date-time"},
            },
        },
        examples=[
            {
                "request": {
                    "topic": "salesOrder.created",
                    "payload": {"salesOrderId": "so-1"},
                    "correlationId": "corr-1",
                },
                "response": {"eventId": "evt-88", "publishedAt": "2025-03-23T12:00:00Z"},
            },
            {
                "request": {"topic": "", "payload": {}},
                "error": {"code": "INVALID_REQUEST", "message": "topic is required"},
            },
        ],
        tests=[
            {
                "name": "event-publish-ok",
                "request": {
                    "topic": "salesOrder.created",
                    "payload": {"salesOrderId": "so-1"},
                },
                "expect": {"status": "success"},
            },
            {
                "name": "event-publish-invalid",
                "request": {"topic": "", "payload": {}},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    # --- Master data: get / search / list patterns ---
    def party_get(name: str, category: str, id_field: str, entity: str) -> None:
        sample_id = {"customer": "cus-001", "supplier": "sup-001", "item": "itm-001"}.get(
            entity, f"{entity[:3]}-001"
        )
        resp_props = {
            id_field: {"type": "string"},
            "code": {"type": "string"},
            "name": {"type": "string"},
            "status": {"type": "string", "enum": ["active", "inactive", "blocked"]},
            "metadata": {"type": "object", "additionalProperties": True},
        }
        sample_resp = {
            id_field: sample_id,
            "code": "C001",
            "name": "Acme Corp",
            "status": "active",
            "metadata": {},
        }
        if entity in ("customer", "supplier"):
            resp_props["primaryContactId"] = {
                "type": "string",
                "description": "Primary contact record (contact.*); customers and suppliers reference contacts.",
            }
            sample_resp["primaryContactId"] = "con-001"
        emit_capability(
            name,
            category=category,
            summary=f"Retrieve a single {entity} by identifier."
            + (
                " Includes primaryContactId linking to contact.* master data."
                if entity in ("customer", "supplier")
                else ""
            ),
            idempotent=True,
            side_effect=False,
            transactional=False,
            lifecycle="draft",
            request={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": [id_field],
                "properties": {id_field: {"type": "string"}},
            },
            response={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": [id_field, "code", "name", "status"],
                "properties": resp_props,
            },
            examples=[
                {
                    "request": {id_field: sample_id},
                    "response": sample_resp,
                },
                {
                    "request": {id_field: "missing"},
                    "error": {"code": "NOT_FOUND", "message": f"{entity} not found"},
                },
            ],
            tests=[
                {
                    "name": f"{name.replace('.', '-')}-ok",
                    "request": {id_field: sample_id},
                    "expect": {"status": "success"},
                },
                {
                    "name": f"{name.replace('.', '-')}-not-found",
                    "request": {id_field: "missing"},
                    "expectError": {"code": "NOT_FOUND"},
                },
            ],
        )

    def party_search(name: str, category: str, id_field: str, entity: str) -> None:
        sample_id = {"customer": "cus-001", "supplier": "sup-001", "item": "itm-001"}.get(
            entity, f"{entity[:3]}-001"
        )
        item_props: dict = {
            id_field: {"type": "string"},
            "code": {"type": "string"},
            "name": {"type": "string"},
            "status": {"type": "string"},
        }
        sample_item = {
            id_field: sample_id,
            "code": "C001",
            "name": "Acme",
            "status": "active",
        }
        if entity in ("customer", "supplier"):
            item_props["primaryContactId"] = {"type": "string"}
            sample_item["primaryContactId"] = "con-001"
        emit_capability(
            name,
            category=category,
            summary=f"Search {entity} records with optional text query and paging."
            + (
                " Items may include primaryContactId (contact.*)."
                if entity in ("customer", "supplier")
                else ""
            ),
            idempotent=True,
            side_effect=False,
            transactional=False,
            lifecycle="draft",
            request={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "query": {"type": "string"},
                    "status": {"type": "string"},
                    "page": PAGE_REQ,
                },
            },
            response={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": ["items", "page"],
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": [id_field, "code", "name"],
                            "properties": item_props,
                            "additionalProperties": False,
                        },
                    },
                    "page": PAGE_RES,
                },
            },
            examples=[
                {
                    "request": {"query": "acme", "page": {"limit": 10}},
                    "response": {
                        "items": [
                            sample_item,
                        ],
                        "page": {"hasMore": False, "totalCount": 1},
                    },
                },
                {
                    "request": {"page": {"limit": 9999}},
                    "error": {"code": "INVALID_REQUEST", "message": "limit exceeds maximum"},
                },
            ],
            tests=[
                {
                    "name": f"{name.replace('.', '-')}-ok",
                    "request": {"query": "a", "page": {"limit": 5}},
                    "expect": {"status": "success"},
                },
                {
                    "name": f"{name.replace('.', '-')}-invalid-page",
                    "request": {"page": {"limit": 9999}},
                    "expectError": {"code": "INVALID_REQUEST"},
                },
            ],
        )

    party_get("customer.get", "customer", "customerId", "customer")
    party_search("customer.search", "customer", "customerId", "customer")
    party_get("supplier.get", "supplier", "supplierId", "supplier")
    party_search("supplier.search", "supplier", "supplierId", "supplier")
    party_get("item.get", "item", "itemId", "item")

    emit_capability(
        "item.search",
        category="item",
        summary="Search item/SKU master data with optional filters and paging.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "query": {"type": "string"},
                "itemType": {"type": "string"},
                "page": PAGE_REQ,
            },
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["items", "page"],
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["itemId", "sku", "name"],
                        "properties": {
                            "itemId": {"type": "string"},
                            "sku": {"type": "string"},
                            "name": {"type": "string"},
                            "uom": {"type": "string"},
                        },
                        "additionalProperties": False,
                    },
                },
                "page": PAGE_RES,
            },
        },
        examples=[
            {
                "request": {"query": "bolt", "page": {"limit": 20}},
                "response": {
                    "items": [
                        {
                            "itemId": "it-77",
                            "sku": "BOLT-M8",
                            "name": "M8 bolt",
                            "uom": "ea",
                        }
                    ],
                    "page": {"hasMore": False},
                },
            },
            {
                "request": {"page": {"limit": 0}},
                "error": {"code": "INVALID_REQUEST", "message": "limit must be >= 1"},
            },
        ],
        tests=[
            {
                "name": "item-search-ok",
                "request": {"query": "b"},
                "expect": {"status": "success"},
            },
            {
                "name": "item-search-invalid-page",
                "request": {"page": {"limit": 0}},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    emit_capability(
        "warehouse.get",
        category="warehouse",
        summary="Retrieve warehouse or storage location master by id.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["warehouseId"],
            "properties": {"warehouseId": {"type": "string"}},
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["warehouseId", "code", "name", "status"],
            "properties": {
                "warehouseId": {"type": "string"},
                "code": {"type": "string"},
                "name": {"type": "string"},
                "status": {"type": "string"},
                "address": {"type": "object", "additionalProperties": True},
            },
        },
        examples=[
            {
                "request": {"warehouseId": "wh-01"},
                "response": {
                    "warehouseId": "wh-01",
                    "code": "EAST-01",
                    "name": "East DC",
                    "status": "active",
                    "address": {},
                },
            },
            {
                "request": {"warehouseId": "missing"},
                "error": {"code": "NOT_FOUND", "message": "Warehouse not found"},
            },
        ],
        tests=[
            {
                "name": "warehouse-get-ok",
                "request": {"warehouseId": "wh-01"},
                "expect": {"status": "success"},
            },
            {
                "name": "warehouse-get-not-found",
                "request": {"warehouseId": "missing"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )

    emit_capability(
        "warehouse.list",
        category="warehouse",
        summary="List warehouses visible to the caller with paging.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "status": {"type": "string"},
                "page": PAGE_REQ,
            },
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["items", "page"],
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["warehouseId", "code", "name"],
                        "properties": {
                            "warehouseId": {"type": "string"},
                            "code": {"type": "string"},
                            "name": {"type": "string"},
                            "status": {"type": "string"},
                        },
                        "additionalProperties": False,
                    },
                },
                "page": PAGE_RES,
            },
        },
        examples=[
            {
                "request": {"page": {"limit": 50}},
                "response": {
                    "items": [
                        {
                            "warehouseId": "wh-01",
                            "code": "EAST-01",
                            "name": "East DC",
                            "status": "active",
                        }
                    ],
                    "page": {"hasMore": False},
                },
            },
            {
                "request": {"page": {"limit": 10000}},
                "error": {"code": "INVALID_REQUEST", "message": "limit exceeds maximum"},
            },
        ],
        tests=[
            {"name": "warehouse-list-ok", "request": {}, "expect": {"status": "success"}},
            {
                "name": "warehouse-list-bad-limit",
                "request": {"page": {"limit": 10000}},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    # --- Sales / purchase ---
    emit_capability(
        "salesOrder.create",
        category="salesOrder",
        summary="Create a sales order in draft or submitted state from header and lines.",
        idempotent=False,
        side_effect=True,
        transactional=True,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["customerId", "lines"],
            "properties": {
                "customerId": {"type": "string"},
                "currency": {"type": "string", "minLength": 3, "maxLength": 3},
                "requestedDate": {"type": "string", "format": "date"},
                "lines": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["itemId", "quantity"],
                        "properties": {
                            "itemId": {"type": "string"},
                            "quantity": {"type": "number", "exclusiveMinimum": 0},
                            "unitPrice": {"type": "number"},
                        },
                        "additionalProperties": False,
                    },
                },
            },
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["salesOrderId", "status"],
            "properties": {
                "salesOrderId": {"type": "string"},
                "status": {"type": "string"},
                "totalAmount": {"type": "number"},
            },
        },
        examples=[
            {
                "request": {
                    "customerId": "cust-1",
                    "currency": "USD",
                    "lines": [{"itemId": "it-1", "quantity": 2, "unitPrice": 10}],
                },
                "response": {
                    "salesOrderId": "so-100",
                    "status": "draft",
                    "totalAmount": 20,
                },
            },
            {
                "request": {"customerId": "cust-1", "currency": "USD", "lines": []},
                "error": {"code": "INVALID_REQUEST", "message": "lines must not be empty"},
            },
        ],
        tests=[
            {
                "name": "sales-order-create-ok",
                "request": {
                    "customerId": "cust-1",
                    "currency": "USD",
                    "lines": [{"itemId": "it-1", "quantity": 1}],
                },
                "expect": {"status": "success"},
            },
            {
                "name": "sales-order-create-invalid",
                "request": {"customerId": "cust-1", "lines": []},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    emit_capability(
        "salesOrder.get",
        category="salesOrder",
        summary="Retrieve sales order header, lines, and status by id.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["salesOrderId"],
            "properties": {"salesOrderId": {"type": "string"}},
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["salesOrderId", "customerId", "status", "lines"],
            "properties": {
                "salesOrderId": {"type": "string"},
                "customerId": {"type": "string"},
                "status": {"type": "string"},
                "currency": {"type": "string"},
                "lines": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
            },
        },
        examples=[
            {
                "request": {"salesOrderId": "so-100"},
                "response": {
                    "salesOrderId": "so-100",
                    "customerId": "cust-1",
                    "status": "confirmed",
                    "currency": "USD",
                    "lines": [],
                },
            },
            {
                "request": {"salesOrderId": "missing"},
                "error": {"code": "NOT_FOUND", "message": "Sales order not found"},
            },
        ],
        tests=[
            {
                "name": "sales-order-get-ok",
                "request": {"salesOrderId": "so-100"},
                "expect": {"status": "success"},
            },
            {
                "name": "sales-order-get-not-found",
                "request": {"salesOrderId": "missing"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )

    emit_capability(
        "purchaseOrder.create",
        category="purchaseOrder",
        summary="Create a purchase order for a supplier with lines.",
        idempotent=False,
        side_effect=True,
        transactional=True,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["supplierId", "lines"],
            "properties": {
                "supplierId": {"type": "string"},
                "currency": {"type": "string", "minLength": 3, "maxLength": 3},
                "lines": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["itemId", "quantity"],
                        "properties": {
                            "itemId": {"type": "string"},
                            "quantity": {"type": "number", "exclusiveMinimum": 0},
                            "unitCost": {"type": "number"},
                        },
                        "additionalProperties": False,
                    },
                },
            },
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["purchaseOrderId", "status"],
            "properties": {
                "purchaseOrderId": {"type": "string"},
                "status": {"type": "string"},
            },
        },
        examples=[
            {
                "request": {
                    "supplierId": "sup-1",
                    "currency": "USD",
                    "lines": [{"itemId": "it-1", "quantity": 5}],
                },
                "response": {"purchaseOrderId": "po-20", "status": "draft"},
            },
            {
                "request": {"supplierId": "sup-1", "currency": "USD", "lines": []},
                "error": {"code": "INVALID_REQUEST", "message": "lines must not be empty"},
            },
        ],
        tests=[
            {
                "name": "purchase-order-create-ok",
                "request": {
                    "supplierId": "sup-1",
                    "currency": "USD",
                    "lines": [{"itemId": "it-1", "quantity": 1}],
                },
                "expect": {"status": "success"},
            },
            {
                "name": "purchase-order-create-invalid",
                "request": {"supplierId": "sup-1", "lines": []},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    emit_capability(
        "purchaseOrder.get",
        category="purchaseOrder",
        summary="Retrieve purchase order by identifier.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["purchaseOrderId"],
            "properties": {"purchaseOrderId": {"type": "string"}},
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["purchaseOrderId", "supplierId", "status", "lines"],
            "properties": {
                "purchaseOrderId": {"type": "string"},
                "supplierId": {"type": "string"},
                "status": {"type": "string"},
                "lines": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
            },
        },
        examples=[
            {
                "request": {"purchaseOrderId": "po-20"},
                "response": {
                    "purchaseOrderId": "po-20",
                    "supplierId": "sup-1",
                    "status": "open",
                    "lines": [],
                },
            },
            {
                "request": {"purchaseOrderId": "missing"},
                "error": {"code": "NOT_FOUND", "message": "Purchase order not found"},
            },
        ],
        tests=[
            {
                "name": "purchase-order-get-ok",
                "request": {"purchaseOrderId": "po-20"},
                "expect": {"status": "success"},
            },
            {
                "name": "purchase-order-get-not-found",
                "request": {"purchaseOrderId": "missing"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )

    # --- Inventory ---
    emit_capability(
        "inventory.get",
        category="inventory",
        summary="Read on-hand or available quantity for an item at a warehouse.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["itemId", "warehouseId"],
            "properties": {
                "itemId": {"type": "string"},
                "warehouseId": {"type": "string"},
            },
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["itemId", "warehouseId", "onHand", "available"],
            "properties": {
                "itemId": {"type": "string"},
                "warehouseId": {"type": "string"},
                "onHand": {"type": "number", "minimum": 0},
                "available": {"type": "number", "minimum": 0},
                "reserved": {"type": "number", "minimum": 0},
            },
        },
        examples=[
            {
                "request": {"itemId": "it-1", "warehouseId": "wh-01"},
                "response": {
                    "itemId": "it-1",
                    "warehouseId": "wh-01",
                    "onHand": 100,
                    "available": 80,
                    "reserved": 20,
                },
            },
            {
                "request": {"itemId": "x", "warehouseId": "y"},
                "error": {"code": "NOT_FOUND", "message": "No inventory record for item/warehouse"},
            },
        ],
        tests=[
            {
                "name": "inventory-get-ok",
                "request": {"itemId": "it-1", "warehouseId": "wh-01"},
                "expect": {"status": "success"},
            },
            {
                "name": "inventory-get-not-found",
                "request": {"itemId": "x", "warehouseId": "y"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )

    emit_capability(
        "inventory.reserve",
        category="inventory",
        summary="Reserve quantity for an item at a warehouse (e.g. for a sales line).",
        idempotent=False,
        side_effect=True,
        transactional=True,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["itemId", "warehouseId", "quantity"],
            "properties": {
                "itemId": {"type": "string"},
                "warehouseId": {"type": "string"},
                "quantity": {"type": "number", "exclusiveMinimum": 0},
                "reservationKey": {
                    "type": "string",
                    "description": "Idempotency key for the same business reservation.",
                },
            },
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["reservationId"],
            "properties": {
                "reservationId": {"type": "string"},
                "expiresAt": {"type": "string", "format": "date-time"},
            },
        },
        examples=[
            {
                "request": {
                    "itemId": "it-1",
                    "warehouseId": "wh-01",
                    "quantity": 3,
                    "reservationKey": "so-line-9",
                },
                "response": {"reservationId": "res-1", "expiresAt": "2025-03-24T00:00:00Z"},
            },
            {
                "request": {
                    "itemId": "it-1",
                    "warehouseId": "wh-01",
                    "quantity": 999999,
                },
                "error": {"code": "INSUFFICIENT_STOCK", "message": "Not enough available quantity"},
            },
        ],
        tests=[
            {
                "name": "inventory-reserve-ok",
                "request": {
                    "itemId": "it-1",
                    "warehouseId": "wh-01",
                    "quantity": 1,
                },
                "expect": {"status": "success"},
            },
            {
                "name": "inventory-reserve-insufficient",
                "request": {
                    "itemId": "it-1",
                    "warehouseId": "wh-01",
                    "quantity": 999999,
                },
                "expectError": {"code": "INSUFFICIENT_STOCK"},
            },
        ],
    )

    for verb, summary in [
        ("inbound", "Post inbound stock (receipt) for an item at a warehouse."),
        ("outbound", "Post outbound stock (issue) for an item at a warehouse."),
    ]:
        cap = f"inventory.{verb}"
        emit_capability(
            cap,
            category="inventory",
            summary=summary,
            idempotent=False,
            side_effect=True,
            transactional=True,
            lifecycle="draft",
            request={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": ["warehouseId", "lines"],
                "properties": {
                    "warehouseId": {"type": "string"},
                    "referenceId": {"type": "string"},
                    "lines": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["itemId", "quantity"],
                            "properties": {
                                "itemId": {"type": "string"},
                                "quantity": {"type": "number", "exclusiveMinimum": 0},
                            },
                            "additionalProperties": False,
                        },
                    },
                },
            },
            response={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": ["movementId"],
                "properties": {"movementId": {"type": "string"}},
            },
            examples=[
                {
                    "request": {
                        "warehouseId": "wh-01",
                        "referenceId": "rcpt-1",
                        "lines": [{"itemId": "it-1", "quantity": 10}],
                    },
                    "response": {"movementId": "mov-1"},
                },
                {
                    "request": {"warehouseId": "wh-01", "lines": []},
                    "error": {"code": "INVALID_REQUEST", "message": "lines must not be empty"},
                },
            ],
            tests=[
                {
                    "name": f"{cap.replace('.', '-')}-ok",
                    "request": {
                        "warehouseId": "wh-01",
                        "lines": [{"itemId": "it-1", "quantity": 1}],
                    },
                    "expect": {"status": "success"},
                },
                {
                    "name": f"{cap.replace('.', '-')}-invalid",
                    "request": {"warehouseId": "wh-01", "lines": []},
                    "expectError": {"code": "INVALID_REQUEST"},
                },
            ],
        )

    emit_capability(
        "inventory.transfer",
        category="inventory",
        summary="Transfer quantity for an item between two warehouses.",
        idempotent=False,
        side_effect=True,
        transactional=True,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["itemId", "fromWarehouseId", "toWarehouseId", "quantity"],
            "properties": {
                "itemId": {"type": "string"},
                "fromWarehouseId": {"type": "string"},
                "toWarehouseId": {"type": "string"},
                "quantity": {"type": "number", "exclusiveMinimum": 0},
            },
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["transferId"],
            "properties": {"transferId": {"type": "string"}},
        },
        examples=[
            {
                "request": {
                    "itemId": "it-1",
                    "fromWarehouseId": "wh-01",
                    "toWarehouseId": "wh-02",
                    "quantity": 4,
                },
                "response": {"transferId": "tr-1"},
            },
            {
                "request": {
                    "itemId": "it-1",
                    "fromWarehouseId": "wh-01",
                    "toWarehouseId": "wh-01",
                    "quantity": 1,
                },
                "error": {"code": "INVALID_REQUEST", "message": "fromWarehouseId and toWarehouseId must differ"},
            },
        ],
        tests=[
            {
                "name": "inventory-transfer-ok",
                "request": {
                    "itemId": "it-1",
                    "fromWarehouseId": "wh-01",
                    "toWarehouseId": "wh-02",
                    "quantity": 1,
                },
                "expect": {"status": "success"},
            },
            {
                "name": "inventory-transfer-same-warehouse",
                "request": {
                    "itemId": "it-1",
                    "fromWarehouseId": "wh-01",
                    "toWarehouseId": "wh-01",
                    "quantity": 1,
                },
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    # --- Finance ---
    emit_capability(
        "invoice.create",
        category="invoice",
        summary="Create an AR invoice from billing lines and customer reference.",
        idempotent=False,
        side_effect=True,
        transactional=True,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["customerId", "lines"],
            "properties": {
                "customerId": {"type": "string"},
                "currency": {"type": "string", "minLength": 3, "maxLength": 3},
                "lines": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["description", "amount"],
                        "properties": {
                            "description": {"type": "string"},
                            "amount": {"type": "number"},
                            "taxCode": {"type": "string"},
                        },
                        "additionalProperties": False,
                    },
                },
            },
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["invoiceId", "status"],
            "properties": {
                "invoiceId": {"type": "string"},
                "status": {"type": "string"},
                "totalAmount": {"type": "number"},
            },
        },
        examples=[
            {
                "request": {
                    "customerId": "cust-1",
                    "currency": "USD",
                    "lines": [{"description": "Widget", "amount": 50}],
                },
                "response": {"invoiceId": "inv-1", "status": "draft", "totalAmount": 50},
            },
            {
                "request": {"customerId": "cust-1", "currency": "USD", "lines": []},
                "error": {"code": "INVALID_REQUEST", "message": "lines must not be empty"},
            },
        ],
        tests=[
            {
                "name": "invoice-create-ok",
                "request": {
                    "customerId": "cust-1",
                    "currency": "USD",
                    "lines": [{"description": "X", "amount": 1}],
                },
                "expect": {"status": "success"},
            },
            {
                "name": "invoice-create-invalid",
                "request": {"customerId": "cust-1", "lines": []},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    emit_capability(
        "payment.execute",
        category="payment",
        summary="Execute a payment against a payable or receivable instrument.",
        idempotent=False,
        side_effect=True,
        transactional=True,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["amount", "currency", "method"],
            "properties": {
                "amount": {"type": "number", "exclusiveMinimum": 0},
                "currency": {"type": "string", "minLength": 3, "maxLength": 3},
                "method": {"type": "string", "enum": ["card", "ach", "wire", "cash"]},
                "invoiceId": {"type": "string"},
                "purchaseOrderId": {"type": "string"},
                "idempotencyKey": {"type": "string"},
            },
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["paymentId", "status"],
            "properties": {
                "paymentId": {"type": "string"},
                "status": {"type": "string"},
                "processedAt": {"type": "string", "format": "date-time"},
            },
        },
        examples=[
            {
                "request": {
                    "amount": 120,
                    "currency": "USD",
                    "method": "ach",
                    "invoiceId": "inv-1",
                },
                "response": {
                    "paymentId": "pay-1",
                    "status": "completed",
                    "processedAt": "2025-03-23T12:00:00Z",
                },
            },
            {
                "request": {"amount": -1, "currency": "USD", "method": "cash"},
                "error": {"code": "INVALID_REQUEST", "message": "amount must be positive"},
            },
        ],
        tests=[
            {
                "name": "payment-execute-ok",
                "request": {"amount": 10, "currency": "USD", "method": "cash"},
                "expect": {"status": "success"},
            },
            {
                "name": "payment-execute-invalid",
                "request": {"amount": -1, "currency": "USD", "method": "cash"},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    def bill_create(name: str, side: str) -> None:
        emit_capability(
            name,
            category=side,
            summary=f"Create a {side.upper()} bill header with lines for posting.",
            idempotent=False,
            side_effect=True,
            transactional=True,
            lifecycle="draft",
            request={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": ["businessPartnerId", "lines"],
                "properties": {
                    "businessPartnerId": {"type": "string"},
                    "currency": {"type": "string", "minLength": 3, "maxLength": 3},
                    "lines": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["description", "amount"],
                            "properties": {
                                "description": {"type": "string"},
                                "amount": {"type": "number"},
                            },
                            "additionalProperties": False,
                        },
                    },
                },
            },
            response={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": ["billId", "status"],
                "properties": {
                    "billId": {"type": "string"},
                    "status": {"type": "string"},
                },
            },
            examples=[
                {
                    "request": {
                        "businessPartnerId": "cust-1",
                        "currency": "USD",
                        "lines": [{"description": "Line", "amount": 25}],
                    },
                    "response": {
                        "billId": "arb-1" if side == "ar" else "apb-1",
                        "status": "open",
                    },
                },
                {
                    "request": {"businessPartnerId": "cust-1", "currency": "USD", "lines": []},
                    "error": {"code": "INVALID_REQUEST", "message": "lines must not be empty"},
                },
            ],
            tests=[
                {
                    "name": f"{name.replace('.', '-')}-ok",
                    "request": {
                        "businessPartnerId": "cust-1",
                        "currency": "USD",
                        "lines": [{"description": "L", "amount": 1}],
                    },
                    "expect": {"status": "success"},
                },
                {
                    "name": f"{name.replace('.', '-')}-invalid",
                    "request": {"businessPartnerId": "cust-1", "lines": []},
                    "expectError": {"code": "INVALID_REQUEST"},
                },
            ],
        )

    bill_create("ar.bill.create", "ar")
    bill_create("ap.bill.create", "ap")

    # --- Task / approval ---
    emit_capability(
        "task.create",
        category="task",
        summary="Create a workflow or work item task assigned to users or roles.",
        idempotent=False,
        side_effect=True,
        transactional=True,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["title", "assignee"],
            "properties": {
                "title": {"type": "string"},
                "assignee": {"type": "string"},
                "dueAt": {"type": "string", "format": "date-time"},
                "payload": {"type": "object", "additionalProperties": True},
            },
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["taskId", "status"],
            "properties": {
                "taskId": {"type": "string"},
                "status": {"type": "string"},
            },
        },
        examples=[
            {
                "request": {"title": "Approve PO", "assignee": "usr-2"},
                "response": {"taskId": "tsk-1", "status": "open"},
            },
            {
                "request": {"title": "", "assignee": "usr-1"},
                "error": {"code": "INVALID_REQUEST", "message": "title is required"},
            },
        ],
        tests=[
            {
                "name": "task-create-ok",
                "request": {"title": "T", "assignee": "usr-1"},
                "expect": {"status": "success"},
            },
            {
                "name": "task-create-invalid",
                "request": {"title": "", "assignee": "usr-1"},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    emit_capability(
        "task.list",
        category="task",
        summary="List tasks for the caller with optional status filter and paging.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "status": {"type": "string"},
                "assignee": {"type": "string"},
                "page": PAGE_REQ,
            },
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["items", "page"],
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["taskId", "title", "status"],
                        "properties": {
                            "taskId": {"type": "string"},
                            "title": {"type": "string"},
                            "status": {"type": "string"},
                            "assignee": {"type": "string"},
                        },
                        "additionalProperties": False,
                    },
                },
                "page": PAGE_RES,
            },
        },
        examples=[
            {
                "request": {"status": "open", "page": {"limit": 10}},
                "response": {
                    "items": [
                        {
                            "taskId": "tsk-1",
                            "title": "Approve PO",
                            "status": "open",
                            "assignee": "usr-2",
                        }
                    ],
                    "page": {"hasMore": False},
                },
            },
            {
                "request": {"page": {"limit": 0}},
                "error": {"code": "INVALID_REQUEST", "message": "limit must be >= 1"},
            },
        ],
        tests=[
            {"name": "task-list-ok", "request": {}, "expect": {"status": "success"}},
            {
                "name": "task-list-bad-page",
                "request": {"page": {"limit": 0}},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    emit_capability(
        "approval.request.create",
        category="approval",
        summary="Start an approval workflow for a business object.",
        idempotent=False,
        side_effect=True,
        transactional=True,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["resourceType", "resourceId", "policyKey"],
            "properties": {
                "resourceType": {"type": "string"},
                "resourceId": {"type": "string"},
                "policyKey": {"type": "string"},
                "comment": {"type": "string"},
            },
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["approvalRequestId", "status"],
            "properties": {
                "approvalRequestId": {"type": "string"},
                "status": {"type": "string"},
            },
        },
        examples=[
            {
                "request": {
                    "resourceType": "purchaseOrder",
                    "resourceId": "po-20",
                    "policyKey": "po.manager",
                },
                "response": {"approvalRequestId": "apr-1", "status": "pending"},
            },
            {
                "request": {"resourceType": "", "resourceId": "po-20", "policyKey": "default"},
                "error": {"code": "INVALID_REQUEST", "message": "resourceType is required"},
            },
        ],
        tests=[
            {
                "name": "approval-request-create-ok",
                "request": {
                    "resourceType": "purchaseOrder",
                    "resourceId": "po-20",
                    "policyKey": "default",
                },
                "expect": {"status": "success"},
            },
            {
                "name": "approval-request-create-invalid",
                "request": {"resourceType": "", "resourceId": "x", "policyKey": "p"},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    for action, summary, status_word in [
        ("approve", "Record an approval decision on a pending approval request.", "approved"),
        ("reject", "Record a rejection decision on a pending approval request.", "rejected"),
    ]:
        cap = f"approval.action.{action}"
        emit_capability(
            cap,
            category="approval",
            summary=summary,
            idempotent=False,
            side_effect=True,
            transactional=True,
            lifecycle="draft",
            request={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": ["approvalRequestId", "actorId"],
                "properties": {
                    "approvalRequestId": {"type": "string"},
                    "actorId": {"type": "string"},
                    "comment": {"type": "string"},
                },
            },
            response={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": ["approvalRequestId", "status"],
                "properties": {
                    "approvalRequestId": {"type": "string"},
                    "status": {"type": "string"},
                },
            },
            examples=[
                {
                    "request": {
                        "approvalRequestId": "apr-1",
                        "actorId": "usr-2",
                        "comment": "ok",
                    },
                    "response": {"approvalRequestId": "apr-1", "status": status_word},
                },
                {
                    "request": {"approvalRequestId": "missing", "actorId": "usr-2"},
                    "error": {"code": "NOT_FOUND", "message": "Approval request not found"},
                },
            ],
            tests=[
                {
                    "name": f"approval-action-{action}-ok",
                    "request": {"approvalRequestId": "apr-1", "actorId": "usr-2"},
                    "expect": {"status": "success"},
                },
                {
                    "name": f"approval-action-{action}-not-found",
                    "request": {"approvalRequestId": "missing", "actorId": "usr-2"},
                    "expectError": {"code": "NOT_FOUND"},
                },
            ],
        )

    emit_module(
        "data.csql.query",
        category="data",
        summary="Execute a catalog-safe constrained SQL (CSQL) query and return a tabular result set.",
        capability_type="data",
        signature={
            "model": "query-execution",
            "querySchema": "schemas/query.json",
            "responseSchema": "schemas/response.json",
            "errorSchema": "schemas/error.json",
        },
        schema_files={
            "schemas/query.json": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": ["sql", "parameters"],
                "properties": {
                    "sql": {"type": "string"},
                    "parameters": {"type": "object", "additionalProperties": True},
                    "maxRows": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10000,
                        "default": 1000,
                    },
                },
            },
            "schemas/response.json": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": ["columns", "rows"],
                "properties": {
                    "columns": {"type": "array", "items": {"type": "string"}},
                    "rows": {
                        "type": "array",
                        "items": {"type": "object", "additionalProperties": True},
                    },
                    "truncated": {"type": "boolean"},
                },
            },
            "schemas/error.json": ERR_REF,
        },
        idempotent=True,
        side_effect=False,
        transactional=False,
        lifecycle="draft",
        examples=[
            {
                "request": {
                    "sql": "SELECT customer_id, name FROM customers WHERE status = :s LIMIT :lim",
                    "parameters": {"s": "active", "lim": 10},
                    "maxRows": 100,
                },
                "response": {
                    "columns": ["customer_id", "name"],
                    "rows": [{"customer_id": "cus-001", "name": "Acme"}],
                    "truncated": False,
                },
            },
            {
                "request": {"sql": "DROP TABLE customers", "parameters": {}},
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Statement type not allowed in CSQL catalog",
                },
            },
        ],
        tests=[
            {
                "name": "data-csql-select-ok",
                "request": {"sql": "SELECT 1 AS n", "parameters": {}},
                "expect": {"status": "success"},
            },
            {
                "name": "data-csql-mutation-rejected",
                "request": {"sql": "DELETE FROM customers", "parameters": {}},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    emit_module(
        "ui.widget.contact.selector",
        category="customer",
        summary="Embeddable contact picker: resolve UI state, optional search, and selected customer id.",
        capability_type="ui",
        signature={
            "model": "ui-interaction",
            "requestSchema": "schemas/request.json",
            "responseSchema": "schemas/response.json",
            "errorSchema": "schemas/error.json",
            "uiSchema": "schemas/ui.json",
        },
        schema_files={
            "schemas/request.json": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "uiContext": {"type": "object", "additionalProperties": True},
                    "searchText": {"type": "string"},
                    "selectedCustomerId": {"type": "string"},
                    "page": PAGE_REQ,
                },
            },
            "schemas/response.json": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": ["contacts", "selectedCustomerId", "page"],
                "properties": {
                    "contacts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["customerId", "displayName"],
                            "properties": {
                                "customerId": {"type": "string"},
                                "displayName": {"type": "string"},
                                "subtitle": {"type": "string"},
                            },
                        },
                    },
                    "selectedCustomerId": {"type": ["string", "null"]},
                    "page": PAGE_RES,
                },
            },
            "schemas/ui.json": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": ["widgetKind", "bindings"],
                "properties": {
                    "widgetKind": {"const": "contact.selector"},
                    "bindings": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["searchCapability", "valueField", "labelField"],
                        "properties": {
                            "searchCapability": {"type": "string"},
                            "getCapability": {"type": "string"},
                            "valueField": {"type": "string"},
                            "labelField": {"type": "string"},
                        },
                    },
                },
            },
            "schemas/error.json": ERR_REF,
        },
        idempotent=True,
        side_effect=False,
        transactional=False,
        lifecycle="draft",
        examples=[
            {
                "request": {"searchText": "ac", "page": {"limit": 5}},
                "response": {
                    "contacts": [
                        {
                            "customerId": "cus-001",
                            "displayName": "Acme Corp",
                            "subtitle": "C001",
                        }
                    ],
                    "selectedCustomerId": None,
                    "page": {"hasMore": False},
                },
            },
            {
                "request": {"selectedCustomerId": "missing"},
                "error": {"code": "NOT_FOUND", "message": "Customer not found"},
            },
        ],
        tests=[
            {
                "name": "ui-contact-selector-search",
                "request": {"searchText": "a", "page": {"limit": 10}},
                "expect": {"status": "success"},
            },
            {
                "name": "ui-contact-selector-not-found",
                "request": {"selectedCustomerId": "missing"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )

    emit_module(
        "on.salesOrder.confirmed",
        category="salesOrder",
        summary="Consume domain event when a sales order reaches confirmed state (milestone handler).",
        capability_type="event-handler",
        signature={
            "model": "event-handler",
            "eventSchema": "schemas/event.json",
            "responseSchema": "schemas/response.json",
            "errorSchema": "schemas/error.json",
        },
        schema_files={
            "schemas/event.json": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": ["salesOrderId", "confirmedAt"],
                "properties": {
                    "salesOrderId": {"type": "string", "minLength": 1},
                    "confirmedAt": {"type": "string", "format": "date-time"},
                    "confirmedBy": {"type": "string"},
                    "eventVersion": {"type": "integer", "minimum": 1},
                },
            },
            "schemas/response.json": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": ["ack"],
                "properties": {"ack": {"type": "boolean"}},
            },
            "schemas/error.json": ERR_REF,
        },
        idempotent=False,
        side_effect=True,
        transactional=True,
        lifecycle="draft",
        examples=[
            {
                "event": {
                    "salesOrderId": "so-100",
                    "confirmedAt": "2025-03-23T10:00:00Z",
                    "confirmedBy": "usr-1",
                    "eventVersion": 1,
                },
                "response": {"ack": True},
            },
            {
                "event": {"salesOrderId": ""},
                "error": {"code": "INVALID_REQUEST", "message": "salesOrderId is required"},
            },
        ],
        tests=[
            {
                "name": "on-sales-order-confirmed-ok",
                "request": {
                    "salesOrderId": "so-100",
                    "confirmedAt": "2025-03-23T10:00:00Z",
                    "confirmedBy": "usr-1",
                },
                "expect": {"status": "success"},
            },
            {
                "name": "on-sales-order-confirmed-invalid",
                "request": {"salesOrderId": ""},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    emit_capability(
        "integration.http.send",
        category="integration",
        summary="Outbound HTTP integration call with timeout, headers, and redacted error mapping.",
        idempotent=False,
        side_effect=True,
        transactional=False,
        lifecycle="draft",
        request={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["method", "url"],
            "properties": {
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                },
                "url": {"type": "string", "format": "uri"},
                "headers": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
                "body": {},
                "timeoutMs": {"type": "integer", "minimum": 100, "maximum": 120000},
            },
        },
        response={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["statusCode"],
            "properties": {
                "statusCode": {"type": "integer"},
                "headers": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
                "body": {},
            },
        },
        examples=[
            {
                "request": {
                    "method": "GET",
                    "url": "https://partner.example/api/v1/status",
                    "timeoutMs": 5000,
                },
                "response": {
                    "statusCode": 200,
                    "headers": {"content-type": "application/json"},
                    "body": {"status": "ok"},
                },
            },
            {
                "request": {"method": "GET", "url": "not-a-url"},
                "error": {"code": "INVALID_REQUEST", "message": "url must be a valid URI"},
            },
        ],
        tests=[
            {
                "name": "integration-http-send-ok",
                "request": {
                    "method": "GET",
                    "url": "https://example.com/",
                    "timeoutMs": 3000,
                },
                "expect": {"status": "success"},
            },
            {
                "name": "integration-http-send-invalid-url",
                "request": {"method": "GET", "url": "%%%"},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
        capability_type="integration",
    )

    from erp_extended_services import emit_extended_erp

    emit_extended_erp(emit_capability, emit_module)

    from contact_capabilities import emit_contact_capabilities

    emit_contact_capabilities(emit_capability)

    # Registry index
    caps = sorted(p.name for p in CAPS.iterdir() if p.is_dir() and not p.name.startswith("_"))
    write_json(
        CAPS / "registry.json",
        {
            "version": "1.0.0",
            "description": "ERP CapSpec sample registry (paths relative to sample/caps/). Includes contact.*, customer/supplier primaryContactId, core batch, resources, data/ui, events, integration, extended domains. See sample/modules/contactbook for contact.* reference implementation.",
            "capabilities": [
                {
                    "name": c,
                    "path": f"{c}/capability.json",
                    "version": "1.0.0",
                }
                for c in caps
            ],
        },
    )
    print(f"Wrote {len(caps)} capabilities under {CAPS}")


if __name__ == "__main__":
    main()
