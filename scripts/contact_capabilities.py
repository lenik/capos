"""contact.* CapSpecs: master contacts; customer/supplier reference contact ids (see party_get in generator)."""

from __future__ import annotations

SC = "https://json-schema.org/draft/2020-12/schema"
PAGE_REQ = {"$ref": "../../_shared/schemas/page-request.json"}
PAGE_RES = {"$ref": "../../_shared/schemas/page-response.json"}


def emit_contact_capabilities(emit_capability) -> None:
    shared_scenarios = [
        {
            "id": "crm-link-customer",
            "title": "Link customer primary contact after contact.create",
            "category": "functional",
            "description": "Sales creates a contact, then sets customer.primaryContactId to that contact.",
            "actors": ["sales_user"],
            "relatedCapabilities": ["customer.get", "customer.search", "contact.create"],
        },
        {
            "id": "supplier-onboarding",
            "title": "Supplier master references procurement contact",
            "category": "functional",
            "description": "Procurement maintains supplier.primaryContactId pointing to contact.get.",
            "actors": ["procurement_user"],
            "relatedCapabilities": ["supplier.get", "contact.get"],
        },
        {
            "id": "audit-pii-minimization",
            "title": "Contact fields in audit trail are minimized",
            "category": "non_functional",
            "description": "Platform logs contactId and action, not full phone/email body in default audit events.",
            "nfrTargets": {"auditPayload": "id_and_action_only"},
        },
        {
            "id": "search-rate-limit",
            "title": "Anonymous contact.search throttled",
            "category": "non_functional",
            "description": "Unauthenticated callers receive 429 after sustained search volume.",
            "nfrTargets": {"maxRpsAnonymous": 5},
        },
    ]

    contact_response_core = {
        "contactId": {"type": "string"},
        "displayName": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "phone": {"type": "string"},
        "companyName": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "version": {"type": "integer", "minimum": 1},
    }

    # --- contact.create ---
    create_cases_a = [
        {
            "name": "create-minimal-fields",
            "request": {"displayName": "Pat Lee"},
            "expect": {"status": "success"},
        },
        {
            "name": "create-full-profile",
            "request": {
                "displayName": "Alex Kim",
                "email": "alex@example.com",
                "phone": "+1-555-0100",
                "companyName": "Acme",
                "tags": ["vip", "apac"],
            },
            "expect": {"status": "success"},
        },
        {
            "name": "create-empty-display-name",
            "request": {"displayName": ""},
            "expectError": {"code": "INVALID_REQUEST"},
        },
        {
            "name": "create-invalid-email-format",
            "request": {"displayName": "X", "email": "not-an-email"},
            "expectError": {"code": "INVALID_REQUEST"},
        },
    ]
    create_cases_b = [
        {
            "name": "create-duplicate-email",
            "request": {
                "displayName": "Dup",
                "email": "duplicate@example.com",
            },
            "expectError": {"code": "CONFLICT"},
        },
        {
            "name": "create-unicode-display",
            "request": {"displayName": "名前テスト", "companyName": "株式会社試験"},
            "expect": {"status": "success"},
        },
        {
            "name": "create-many-tags",
            "request": {
                "displayName": "Tagged",
                "tags": ["a", "b", "c", "d", "e"],
            },
            "expect": {"status": "success"},
        },
    ]

    emit_capability(
        "contact.create",
        category="contact",
        summary="Create a contact record (person or role); referenced by customer.* and supplier.* as primaryContactId.",
        idempotent=False,
        side_effect=True,
        transactional=True,
        lifecycle="draft",
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["displayName"],
            "properties": {
                "displayName": {"type": "string", "minLength": 1, "maxLength": 200},
                "email": {"type": "string", "format": "email"},
                "phone": {"type": "string", "maxLength": 40},
                "companyName": {"type": "string", "maxLength": 200},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 32,
                },
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["contactId", "displayName", "version"],
            "properties": {
                "contactId": {"type": "string"},
                "displayName": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "companyName": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "version": {"type": "integer", "minimum": 1},
            },
        },
        examples=[
            {
                "request": {
                    "displayName": "Jordan Smith",
                    "email": "jordan@example.com",
                    "tags": ["buyer"],
                },
                "response": {
                    "contactId": "con-100",
                    "displayName": "Jordan Smith",
                    "email": "jordan@example.com",
                    "version": 1,
                },
            },
            {
                "request": {"displayName": ""},
                "error": {"code": "INVALID_REQUEST", "message": "displayName is required"},
            },
        ],
        tests=[
            {
                "name": "contact-create-ok",
                "request": {"displayName": "Test User"},
                "expect": {"status": "success"},
            },
            {
                "name": "contact-create-invalid",
                "request": {"displayName": ""},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
        scenarios=shared_scenarios
        + [
            {
                "id": "bulk-import-precheck",
                "title": "Import pipeline validates via contact.create",
                "category": "operational",
                "description": "ETL calls contact.create row-by-row; failures tagged INVALID_REQUEST vs CONFLICT.",
            }
        ],
        case_suites=[
            ("tests/cases/create-core.yaml", create_cases_a),
            ("tests/cases/create-edge.yaml", create_cases_b),
        ],
    )

    # --- contact.get ---
    get_cases = [
        {
            "name": "get-existing",
            "request": {"contactId": "con-100"},
            "expect": {"status": "success"},
        },
        {
            "name": "get-missing",
            "request": {"contactId": "con-missing"},
            "expectError": {"code": "NOT_FOUND"},
        },
        {
            "name": "get-empty-id",
            "request": {"contactId": ""},
            "expectError": {"code": "INVALID_REQUEST"},
        },
        {
            "name": "get-malformed-id",
            "request": {"contactId": "   "},
            "expectError": {"code": "INVALID_REQUEST"},
        },
    ]
    emit_capability(
        "contact.get",
        category="contact",
        summary="Retrieve a contact by id; used when resolving customer.primaryContactId / supplier.primaryContactId.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        lifecycle="draft",
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["contactId"],
            "properties": {"contactId": {"type": "string", "minLength": 1}},
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["contactId", "displayName", "version"],
            "properties": contact_response_core,
        },
        examples=[
            {
                "request": {"contactId": "con-100"},
                "response": {
                    "contactId": "con-100",
                    "displayName": "Jordan Smith",
                    "email": "jordan@example.com",
                    "version": 1,
                },
            },
            {
                "request": {"contactId": "none"},
                "error": {"code": "NOT_FOUND", "message": "Contact not found"},
            },
        ],
        tests=[
            {"name": "contact-get-ok", "request": {"contactId": "con-100"}, "expect": {"status": "success"}},
            {
                "name": "contact-get-not-found",
                "request": {"contactId": "missing"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
        scenarios=shared_scenarios
        + [
            {
                "id": "ui-detail-hydration",
                "title": "UI loads contact card from contact.get",
                "category": "functional",
                "description": "Detail panes call contact.get using id from customer record.",
                "relatedCapabilities": ["ui.widget.contact.selector"],
            }
        ],
        case_suites=[("tests/cases/get-cases.yaml", get_cases)],
    )

    search_cases_a = [
        {
            "name": "search-by-text",
            "request": {"query": "acme", "page": {"limit": 10}},
            "expect": {"status": "success"},
        },
        {
            "name": "search-empty-query-allowed",
            "request": {"page": {"limit": 5}},
            "expect": {"status": "success"},
        },
        {
            "name": "search-tag-filter",
            "request": {"query": "buyer", "tag": "vip", "page": {"limit": 20}},
            "expect": {"status": "success"},
        },
    ]
    search_cases_b = [
        {
            "name": "search-bad-limit",
            "request": {"query": "x", "page": {"limit": 0}},
            "expectError": {"code": "INVALID_REQUEST"},
        },
        {
            "name": "search-cursor-roundtrip",
            "request": {"query": "a", "page": {"limit": 2, "cursor": "cur-1"}},
            "expect": {"status": "success"},
        },
        {
            "name": "search-unicode",
            "request": {"query": "名前", "page": {"limit": 10}},
            "expect": {"status": "success"},
        },
    ]

    emit_capability(
        "contact.search",
        category="contact",
        summary="Search contacts by text, optional tag, with paging.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        lifecycle="draft",
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "query": {"type": "string"},
                "tag": {"type": "string"},
                "page": PAGE_REQ,
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["items", "page"],
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["contactId", "displayName"],
                        "properties": {
                            "contactId": {"type": "string"},
                            "displayName": {"type": "string"},
                            "email": {"type": "string"},
                            "companyName": {"type": "string"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
                "page": PAGE_RES,
            },
        },
        examples=[
            {
                "request": {"query": "jordan", "page": {"limit": 10}},
                "response": {
                    "items": [
                        {
                            "contactId": "con-100",
                            "displayName": "Jordan Smith",
                            "email": "jordan@example.com",
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
            {"name": "contact-search-ok", "request": {"query": "a"}, "expect": {"status": "success"}},
            {
                "name": "contact-search-bad-page",
                "request": {"page": {"limit": 0}},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
        scenarios=shared_scenarios,
        case_suites=[
            ("tests/cases/search-main.yaml", search_cases_a),
            ("tests/cases/search-edge.yaml", search_cases_b),
        ],
    )

    update_cases = [
        {
            "name": "update-display-name",
            "request": {"contactId": "con-100", "displayName": "Jordan S."},
            "expect": {"status": "success"},
        },
        {
            "name": "update-email-only",
            "request": {"contactId": "con-100", "email": "new@example.com"},
            "expect": {"status": "success"},
        },
        {
            "name": "update-version-mismatch",
            "request": {
                "contactId": "con-100",
                "displayName": "X",
                "expectedVersion": 99,
            },
            "expectError": {"code": "CONFLICT"},
        },
        {
            "name": "update-not-found",
            "request": {"contactId": "missing", "displayName": "Nope"},
            "expectError": {"code": "NOT_FOUND"},
        },
        {
            "name": "update-clear-phone",
            "request": {"contactId": "con-100", "phone": ""},
            "expect": {"status": "success"},
        },
    ]

    emit_capability(
        "contact.update",
        category="contact",
        summary="Patch mutable fields on a contact; optional optimistic expectedVersion.",
        idempotent=False,
        side_effect=True,
        transactional=True,
        lifecycle="draft",
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["contactId"],
            "properties": {
                "contactId": {"type": "string", "minLength": 1},
                "displayName": {"type": "string", "minLength": 1, "maxLength": 200},
                "email": {"type": "string", "format": "email"},
                "phone": {"type": "string"},
                "companyName": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "expectedVersion": {"type": "integer", "minimum": 1},
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["contactId", "displayName", "version"],
            "properties": contact_response_core,
        },
        examples=[
            {
                "request": {"contactId": "con-100", "phone": "+1-555-0199"},
                "response": {
                    "contactId": "con-100",
                    "displayName": "Jordan Smith",
                    "phone": "+1-555-0199",
                    "version": 2,
                },
            },
            {
                "request": {"contactId": "con-100", "expectedVersion": 5, "displayName": "X"},
                "error": {"code": "CONFLICT", "message": "Version mismatch"},
            },
        ],
        tests=[
            {
                "name": "contact-update-ok",
                "request": {"contactId": "con-100", "displayName": "New"},
                "expect": {"status": "success"},
            },
            {
                "name": "contact-update-not-found",
                "request": {"contactId": "missing", "displayName": "X"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
        scenarios=shared_scenarios,
        case_suites=[("tests/cases/update-cases.yaml", update_cases)],
    )

    delete_cases = [
        {
            "name": "delete-existing",
            "request": {"contactId": "con-100"},
            "expect": {"status": "success"},
        },
        {
            "name": "delete-idempotent-second-call",
            "request": {"contactId": "con-100"},
            "expect": {"status": "success"},
        },
        {
            "name": "delete-referenced-by-customer",
            "request": {"contactId": "con-in-use"},
            "expectError": {"code": "CONFLICT"},
        },
        {
            "name": "delete-not-found",
            "request": {"contactId": "con-none"},
            "expectError": {"code": "NOT_FOUND"},
        },
    ]

    emit_capability(
        "contact.delete",
        category="contact",
        summary="Delete a contact; must fail with CONFLICT if still referenced as primaryContactId.",
        idempotent=True,
        side_effect=True,
        transactional=True,
        lifecycle="draft",
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["contactId"],
            "properties": {"contactId": {"type": "string", "minLength": 1}},
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["deleted", "contactId"],
            "properties": {
                "deleted": {"type": "boolean"},
                "contactId": {"type": "string"},
            },
        },
        examples=[
            {"request": {"contactId": "con-100"}, "response": {"deleted": True, "contactId": "con-100"}},
            {
                "request": {"contactId": "con-in-use"},
                "error": {"code": "CONFLICT", "message": "Contact referenced by party master"},
            },
        ],
        tests=[
            {"name": "contact-delete-ok", "request": {"contactId": "con-200"}, "expect": {"status": "success"}},
            {
                "name": "contact-delete-conflict",
                "request": {"contactId": "con-in-use"},
                "expectError": {"code": "CONFLICT"},
            },
        ],
        scenarios=shared_scenarios
        + [
            {
                "id": "gdpr-erasure",
                "title": "Regulatory erasure request",
                "category": "compliance",
                "description": "contact.delete participates in data subject erasure when no legal hold.",
            }
        ],
        case_suites=[("tests/cases/delete-cases.yaml", delete_cases)],
    )
