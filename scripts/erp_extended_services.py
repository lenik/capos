"""Extended ERP service / integration / UI capabilities for underrepresented domains."""

from __future__ import annotations

SC = "https://json-schema.org/draft/2020-12/schema"
PAGE_REQ = {"$ref": "../../_shared/schemas/page-request.json"}
PAGE_RES = {"$ref": "../../_shared/schemas/page-response.json"}
ERR_REF = {"$ref": "../../_shared/schemas/erp-error.json"}


def emit_extended_erp(emit_capability, emit_module) -> None:
    def ec(
        name: str,
        category: str,
        summary: str,
        *,
        idempotent: bool,
        side_effect: bool,
        transactional: bool,
        request: dict,
        response: dict,
        examples: list[dict],
        tests: list[dict],
        capability_type: str = "service",
    ) -> None:
        emit_capability(
            name,
            category=category,
            summary=summary,
            idempotent=idempotent,
            side_effect=side_effect,
            transactional=transactional,
            lifecycle="draft",
            request=request,
            response=response,
            examples=examples,
            tests=tests,
            capability_type=capability_type,
        )

    # --- org ---
    ec(
        "org.unit.get",
        "org",
        "Retrieve an organization unit (cost center, department, legal entity node) by id.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["orgUnitId"],
            "properties": {"orgUnitId": {"type": "string"}},
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["orgUnitId", "code", "name", "orgUnitType"],
            "properties": {
                "orgUnitId": {"type": "string"},
                "code": {"type": "string"},
                "name": {"type": "string"},
                "orgUnitType": {"type": "string"},
                "parentOrgUnitId": {"type": "string"},
            },
        },
        examples=[
            {
                "request": {"orgUnitId": "ou-east"},
                "response": {
                    "orgUnitId": "ou-east",
                    "code": "EAST",
                    "name": "East Region",
                    "orgUnitType": "region",
                    "parentOrgUnitId": "ou-root",
                },
            },
            {
                "request": {"orgUnitId": "missing"},
                "error": {"code": "NOT_FOUND", "message": "Organization unit not found"},
            },
        ],
        tests=[
            {"name": "org-unit-get-ok", "request": {"orgUnitId": "ou-east"}, "expect": {"status": "success"}},
            {
                "name": "org-unit-get-not-found",
                "request": {"orgUnitId": "missing"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )

    ec(
        "org.unit.list",
        "org",
        "List organization units visible to the caller with optional parent filter and paging.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "parentOrgUnitId": {"type": "string"},
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
                        "required": ["orgUnitId", "code", "name"],
                        "properties": {
                            "orgUnitId": {"type": "string"},
                            "code": {"type": "string"},
                            "name": {"type": "string"},
                            "orgUnitType": {"type": "string"},
                        },
                    },
                },
                "page": PAGE_RES,
            },
        },
        examples=[
            {
                "request": {"parentOrgUnitId": "ou-root", "page": {"limit": 20}},
                "response": {
                    "items": [
                        {
                            "orgUnitId": "ou-east",
                            "code": "EAST",
                            "name": "East Region",
                            "orgUnitType": "region",
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
            {"name": "org-unit-list-ok", "request": {}, "expect": {"status": "success"}},
            {
                "name": "org-unit-list-bad-page",
                "request": {"page": {"limit": 0}},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    line_item = {
        "type": "object",
        "additionalProperties": False,
        "required": ["itemId", "quantity", "unitPrice"],
        "properties": {
            "itemId": {"type": "string"},
            "quantity": {"type": "number", "exclusiveMinimum": 0},
            "unitPrice": {"type": "number", "minimum": 0},
        },
    }

    ec(
        "quotation.create",
        "quotation",
        "Create a sales quotation with lines and optional validity date.",
        idempotent=False,
        side_effect=True,
        transactional=True,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["customerId", "currency", "lines"],
            "properties": {
                "customerId": {"type": "string"},
                "currency": {"type": "string", "minLength": 3, "maxLength": 3},
                "validUntil": {"type": "string", "format": "date"},
                "lines": {"type": "array", "minItems": 1, "items": line_item},
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["quotationId", "status"],
            "properties": {
                "quotationId": {"type": "string"},
                "status": {"type": "string"},
                "totalAmount": {"type": "number"},
            },
        },
        examples=[
            {
                "request": {
                    "customerId": "cus-001",
                    "currency": "USD",
                    "lines": [{"itemId": "it-1", "quantity": 2, "unitPrice": 10}],
                },
                "response": {"quotationId": "qt-50", "status": "draft", "totalAmount": 20},
            },
            {
                "request": {"customerId": "cus-001", "currency": "USD", "lines": []},
                "error": {"code": "INVALID_REQUEST", "message": "lines must not be empty"},
            },
        ],
        tests=[
            {
                "name": "quotation-create-ok",
                "request": {
                    "customerId": "cus-001",
                    "currency": "USD",
                    "lines": [{"itemId": "it-1", "quantity": 1, "unitPrice": 1}],
                },
                "expect": {"status": "success"},
            },
            {
                "name": "quotation-create-invalid",
                "request": {"customerId": "cus-001", "currency": "USD", "lines": []},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    ec(
        "quotation.get",
        "quotation",
        "Retrieve quotation header, lines, and status by id.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["quotationId"],
            "properties": {"quotationId": {"type": "string"}},
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["quotationId", "customerId", "status", "lines"],
            "properties": {
                "quotationId": {"type": "string"},
                "customerId": {"type": "string"},
                "status": {"type": "string"},
                "currency": {"type": "string"},
                "lines": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
            },
        },
        examples=[
            {
                "request": {"quotationId": "qt-50"},
                "response": {
                    "quotationId": "qt-50",
                    "customerId": "cus-001",
                    "status": "sent",
                    "currency": "USD",
                    "lines": [],
                },
            },
            {
                "request": {"quotationId": "missing"},
                "error": {"code": "NOT_FOUND", "message": "Quotation not found"},
            },
        ],
        tests=[
            {"name": "quotation-get-ok", "request": {"quotationId": "qt-50"}, "expect": {"status": "success"}},
            {
                "name": "quotation-get-not-found",
                "request": {"quotationId": "missing"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )

    pr_line = {
        "type": "object",
        "additionalProperties": False,
        "required": ["itemId", "quantity", "neededBy"],
        "properties": {
            "itemId": {"type": "string"},
            "quantity": {"type": "number", "exclusiveMinimum": 0},
            "neededBy": {"type": "string", "format": "date"},
        },
    }

    ec(
        "purchaseRequest.create",
        "purchaseRequest",
        "Create an internal purchase requisition with requested lines.",
        idempotent=False,
        side_effect=True,
        transactional=True,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["requestorId", "lines"],
            "properties": {
                "requestorId": {"type": "string"},
                "orgUnitId": {"type": "string"},
                "lines": {"type": "array", "minItems": 1, "items": pr_line},
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["purchaseRequestId", "status"],
            "properties": {
                "purchaseRequestId": {"type": "string"},
                "status": {"type": "string"},
            },
        },
        examples=[
            {
                "request": {
                    "requestorId": "usr-1",
                    "lines": [
                        {
                            "itemId": "it-1",
                            "quantity": 5,
                            "neededBy": "2025-04-01",
                        }
                    ],
                },
                "response": {"purchaseRequestId": "pr-10", "status": "draft"},
            },
            {
                "request": {"requestorId": "usr-1", "lines": []},
                "error": {"code": "INVALID_REQUEST", "message": "lines must not be empty"},
            },
        ],
        tests=[
            {
                "name": "purchase-request-create-ok",
                "request": {
                    "requestorId": "usr-1",
                    "lines": [{"itemId": "it-1", "quantity": 1, "neededBy": "2025-04-01"}],
                },
                "expect": {"status": "success"},
            },
            {
                "name": "purchase-request-create-invalid",
                "request": {"requestorId": "usr-1", "lines": []},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    ec(
        "purchaseRequest.get",
        "purchaseRequest",
        "Retrieve a purchase requisition by id.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["purchaseRequestId"],
            "properties": {"purchaseRequestId": {"type": "string"}},
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["purchaseRequestId", "requestorId", "status", "lines"],
            "properties": {
                "purchaseRequestId": {"type": "string"},
                "requestorId": {"type": "string"},
                "status": {"type": "string"},
                "lines": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
            },
        },
        examples=[
            {
                "request": {"purchaseRequestId": "pr-10"},
                "response": {
                    "purchaseRequestId": "pr-10",
                    "requestorId": "usr-1",
                    "status": "submitted",
                    "lines": [],
                },
            },
            {
                "request": {"purchaseRequestId": "missing"},
                "error": {"code": "NOT_FOUND", "message": "Purchase request not found"},
            },
        ],
        tests=[
            {
                "name": "purchase-request-get-ok",
                "request": {"purchaseRequestId": "pr-10"},
                "expect": {"status": "success"},
            },
            {
                "name": "purchase-request-get-not-found",
                "request": {"purchaseRequestId": "missing"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )

    ship_line = {
        "type": "object",
        "additionalProperties": False,
        "required": ["itemId", "quantity"],
        "properties": {
            "itemId": {"type": "string"},
            "quantity": {"type": "number", "exclusiveMinimum": 0},
        },
    }

    ec(
        "shipment.create",
        "shipment",
        "Create an outbound shipment from a sales order reference and picked lines.",
        idempotent=False,
        side_effect=True,
        transactional=True,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["salesOrderId", "warehouseId", "lines"],
            "properties": {
                "salesOrderId": {"type": "string"},
                "warehouseId": {"type": "string"},
                "carrierCode": {"type": "string"},
                "lines": {"type": "array", "minItems": 1, "items": ship_line},
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["shipmentId", "status"],
            "properties": {
                "shipmentId": {"type": "string"},
                "status": {"type": "string"},
            },
        },
        examples=[
            {
                "request": {
                    "salesOrderId": "so-100",
                    "warehouseId": "wh-01",
                    "lines": [{"itemId": "it-1", "quantity": 2}],
                },
                "response": {"shipmentId": "shp-3", "status": "draft"},
            },
            {
                "request": {"salesOrderId": "so-100", "warehouseId": "wh-01", "lines": []},
                "error": {"code": "INVALID_REQUEST", "message": "lines must not be empty"},
            },
        ],
        tests=[
            {
                "name": "shipment-create-ok",
                "request": {
                    "salesOrderId": "so-100",
                    "warehouseId": "wh-01",
                    "lines": [{"itemId": "it-1", "quantity": 1}],
                },
                "expect": {"status": "success"},
            },
            {
                "name": "shipment-create-invalid",
                "request": {"salesOrderId": "so-100", "warehouseId": "wh-01", "lines": []},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    ec(
        "shipment.get",
        "shipment",
        "Retrieve shipment header, carrier info, and lines by id.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["shipmentId"],
            "properties": {"shipmentId": {"type": "string"}},
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["shipmentId", "salesOrderId", "status", "lines"],
            "properties": {
                "shipmentId": {"type": "string"},
                "salesOrderId": {"type": "string"},
                "status": {"type": "string"},
                "trackingNumber": {"type": "string"},
                "lines": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
            },
        },
        examples=[
            {
                "request": {"shipmentId": "shp-3"},
                "response": {
                    "shipmentId": "shp-3",
                    "salesOrderId": "so-100",
                    "status": "shipped",
                    "trackingNumber": "1Z999",
                    "lines": [],
                },
            },
            {
                "request": {"shipmentId": "missing"},
                "error": {"code": "NOT_FOUND", "message": "Shipment not found"},
            },
        ],
        tests=[
            {"name": "shipment-get-ok", "request": {"shipmentId": "shp-3"}, "expect": {"status": "success"}},
            {
                "name": "shipment-get-not-found",
                "request": {"shipmentId": "missing"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )

    recv_line = {
        "type": "object",
        "additionalProperties": False,
        "required": ["itemId", "quantity"],
        "properties": {
            "itemId": {"type": "string"},
            "quantity": {"type": "number", "exclusiveMinimum": 0},
        },
    }

    ec(
        "receipt.create",
        "receipt",
        "Post a goods receipt against a purchase order (inbound confirmation).",
        idempotent=False,
        side_effect=True,
        transactional=True,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["purchaseOrderId", "warehouseId", "lines"],
            "properties": {
                "purchaseOrderId": {"type": "string"},
                "warehouseId": {"type": "string"},
                "lines": {"type": "array", "minItems": 1, "items": recv_line},
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["receiptId", "status"],
            "properties": {
                "receiptId": {"type": "string"},
                "status": {"type": "string"},
            },
        },
        examples=[
            {
                "request": {
                    "purchaseOrderId": "po-20",
                    "warehouseId": "wh-01",
                    "lines": [{"itemId": "it-1", "quantity": 5}],
                },
                "response": {"receiptId": "rcpt-2", "status": "posted"},
            },
            {
                "request": {"purchaseOrderId": "po-20", "warehouseId": "wh-01", "lines": []},
                "error": {"code": "INVALID_REQUEST", "message": "lines must not be empty"},
            },
        ],
        tests=[
            {
                "name": "receipt-create-ok",
                "request": {
                    "purchaseOrderId": "po-20",
                    "warehouseId": "wh-01",
                    "lines": [{"itemId": "it-1", "quantity": 1}],
                },
                "expect": {"status": "success"},
            },
            {
                "name": "receipt-create-invalid",
                "request": {"purchaseOrderId": "po-20", "warehouseId": "wh-01", "lines": []},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    ec(
        "receipt.get",
        "receipt",
        "Retrieve a goods receipt by id.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["receiptId"],
            "properties": {"receiptId": {"type": "string"}},
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["receiptId", "purchaseOrderId", "status", "lines"],
            "properties": {
                "receiptId": {"type": "string"},
                "purchaseOrderId": {"type": "string"},
                "status": {"type": "string"},
                "lines": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
            },
        },
        examples=[
            {
                "request": {"receiptId": "rcpt-2"},
                "response": {
                    "receiptId": "rcpt-2",
                    "purchaseOrderId": "po-20",
                    "status": "posted",
                    "lines": [],
                },
            },
            {
                "request": {"receiptId": "missing"},
                "error": {"code": "NOT_FOUND", "message": "Receipt not found"},
            },
        ],
        tests=[
            {"name": "receipt-get-ok", "request": {"receiptId": "rcpt-2"}, "expect": {"status": "success"}},
            {
                "name": "receipt-get-not-found",
                "request": {"receiptId": "missing"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )

    je_line = {
        "type": "object",
        "additionalProperties": False,
        "required": ["accountId", "debit", "credit"],
        "properties": {
            "accountId": {"type": "string"},
            "debit": {"type": "number", "minimum": 0},
            "credit": {"type": "number", "minimum": 0},
            "dimensions": {"type": "object", "additionalProperties": {"type": "string"}},
        },
    }

    ec(
        "gl.journal.post",
        "gl",
        "Post a balanced journal entry to the general ledger.",
        idempotent=False,
        side_effect=True,
        transactional=True,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["postingDate", "lines", "description"],
            "properties": {
                "postingDate": {"type": "string", "format": "date"},
                "description": {"type": "string"},
                "lines": {"type": "array", "minItems": 2, "items": je_line},
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["journalEntryId", "status"],
            "properties": {
                "journalEntryId": {"type": "string"},
                "status": {"type": "string"},
            },
        },
        examples=[
            {
                "request": {
                    "postingDate": "2025-03-23",
                    "description": "Cash sale",
                    "lines": [
                        {"accountId": "1000", "debit": 100, "credit": 0},
                        {"accountId": "4000", "debit": 0, "credit": 100},
                    ],
                },
                "response": {"journalEntryId": "je-900", "status": "posted"},
            },
            {
                "request": {"postingDate": "2025-03-23", "description": "x", "lines": []},
                "error": {"code": "INVALID_REQUEST", "message": "at least two lines required"},
            },
        ],
        tests=[
            {
                "name": "gl-journal-post-ok",
                "request": {
                    "postingDate": "2025-03-23",
                    "description": "Adj",
                    "lines": [
                        {"accountId": "1000", "debit": 1, "credit": 0},
                        {"accountId": "4000", "debit": 0, "credit": 1},
                    ],
                },
                "expect": {"status": "success"},
            },
            {
                "name": "gl-journal-post-invalid",
                "request": {"postingDate": "2025-03-23", "description": "x", "lines": []},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    ec(
        "gl.account.list",
        "gl",
        "List GL accounts matching optional code prefix with paging.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "codePrefix": {"type": "string"},
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
                        "required": ["accountId", "code", "name"],
                        "properties": {
                            "accountId": {"type": "string"},
                            "code": {"type": "string"},
                            "name": {"type": "string"},
                            "accountType": {"type": "string"},
                        },
                    },
                },
                "page": PAGE_RES,
            },
        },
        examples=[
            {
                "request": {"codePrefix": "4", "page": {"limit": 50}},
                "response": {
                    "items": [
                        {
                            "accountId": "acc-4000",
                            "code": "4000",
                            "name": "Revenue",
                            "accountType": "revenue",
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
            {"name": "gl-account-list-ok", "request": {}, "expect": {"status": "success"}},
            {
                "name": "gl-account-list-bad-page",
                "request": {"page": {"limit": 10000}},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    ec(
        "contract.get",
        "contract",
        "Retrieve a contract header (customer, dates, status) by id.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["contractId"],
            "properties": {"contractId": {"type": "string"}},
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["contractId", "counterpartyId", "status", "startDate", "endDate"],
            "properties": {
                "contractId": {"type": "string"},
                "counterpartyId": {"type": "string"},
                "status": {"type": "string"},
                "startDate": {"type": "string", "format": "date"},
                "endDate": {"type": "string", "format": "date"},
            },
        },
        examples=[
            {
                "request": {"contractId": "ctr-1"},
                "response": {
                    "contractId": "ctr-1",
                    "counterpartyId": "cus-001",
                    "status": "active",
                    "startDate": "2025-01-01",
                    "endDate": "2025-12-31",
                },
            },
            {
                "request": {"contractId": "missing"},
                "error": {"code": "NOT_FOUND", "message": "Contract not found"},
            },
        ],
        tests=[
            {"name": "contract-get-ok", "request": {"contractId": "ctr-1"}, "expect": {"status": "success"}},
            {
                "name": "contract-get-not-found",
                "request": {"contractId": "missing"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )

    ec(
        "workOrder.create",
        "workOrder",
        "Create a manufacturing work order for an item and quantity.",
        idempotent=False,
        side_effect=True,
        transactional=True,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["itemId", "quantity", "plantId"],
            "properties": {
                "itemId": {"type": "string"},
                "quantity": {"type": "number", "exclusiveMinimum": 0},
                "plantId": {"type": "string"},
                "productionPlanId": {"type": "string"},
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["workOrderId", "status"],
            "properties": {
                "workOrderId": {"type": "string"},
                "status": {"type": "string"},
            },
        },
        examples=[
            {
                "request": {
                    "itemId": "it-fg-1",
                    "quantity": 100,
                    "plantId": "plant-01",
                },
                "response": {"workOrderId": "wo-77", "status": "released"},
            },
            {
                "request": {"itemId": "it-fg-1", "quantity": 0, "plantId": "plant-01"},
                "error": {"code": "INVALID_REQUEST", "message": "quantity must be positive"},
            },
        ],
        tests=[
            {
                "name": "work-order-create-ok",
                "request": {"itemId": "it-1", "quantity": 1, "plantId": "p1"},
                "expect": {"status": "success"},
            },
            {
                "name": "work-order-create-invalid",
                "request": {"itemId": "it-1", "quantity": 0, "plantId": "p1"},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    ec(
        "workOrder.get",
        "workOrder",
        "Retrieve work order status, quantity, and plant by id.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["workOrderId"],
            "properties": {"workOrderId": {"type": "string"}},
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["workOrderId", "itemId", "quantity", "plantId", "status"],
            "properties": {
                "workOrderId": {"type": "string"},
                "itemId": {"type": "string"},
                "quantity": {"type": "number"},
                "plantId": {"type": "string"},
                "status": {"type": "string"},
            },
        },
        examples=[
            {
                "request": {"workOrderId": "wo-77"},
                "response": {
                    "workOrderId": "wo-77",
                    "itemId": "it-fg-1",
                    "quantity": 100,
                    "plantId": "plant-01",
                    "status": "inProgress",
                },
            },
            {
                "request": {"workOrderId": "missing"},
                "error": {"code": "NOT_FOUND", "message": "Work order not found"},
            },
        ],
        tests=[
            {"name": "work-order-get-ok", "request": {"workOrderId": "wo-77"}, "expect": {"status": "success"}},
            {
                "name": "work-order-get-not-found",
                "request": {"workOrderId": "missing"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )

    ec(
        "integration.webhook.receive",
        "integration",
        "Accept an inbound webhook: verify provider signature, normalize payload, dedupe by event id.",
        idempotent=True,
        side_effect=True,
        transactional=True,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["provider", "eventId", "payload"],
            "properties": {
                "provider": {"type": "string"},
                "eventId": {"type": "string"},
                "payload": {"type": "object", "additionalProperties": True},
                "signature": {"type": "string"},
                "receivedAt": {"type": "string", "format": "date-time"},
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["accepted", "dedupeKey"],
            "properties": {
                "accepted": {"type": "boolean"},
                "dedupeKey": {"type": "string"},
            },
        },
        examples=[
            {
                "request": {
                    "provider": "stripe",
                    "eventId": "evt_123",
                    "payload": {"type": "charge.succeeded"},
                    "signature": "v1=abc",
                },
                "response": {"accepted": True, "dedupeKey": "stripe:evt_123"},
            },
            {
                "request": {"provider": "stripe", "eventId": "evt_bad", "payload": {}},
                "error": {"code": "UNAUTHORIZED", "message": "Invalid webhook signature"},
            },
        ],
        tests=[
            {
                "name": "integration-webhook-receive-ok",
                "request": {
                    "provider": "partner",
                    "eventId": "e1",
                    "payload": {"k": 1},
                },
                "expect": {"status": "success"},
            },
            {
                "name": "integration-webhook-receive-rejected",
                "request": {"provider": "partner", "eventId": "bad", "payload": {}},
                "expectError": {"code": "UNAUTHORIZED"},
            },
        ],
        capability_type="integration",
    )

    emit_module(
        "ui.view.salesOrder.detail",
        category="salesOrder",
        summary="Read-only sales order detail view: header, lines, and bound backend capabilities.",
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
                "$schema": SC,
                "type": "object",
                "additionalProperties": False,
                "required": ["salesOrderId"],
                "properties": {
                    "salesOrderId": {"type": "string"},
                    "uiContext": {"type": "object", "additionalProperties": True},
                },
            },
            "schemas/response.json": {
                "$schema": SC,
                "type": "object",
                "additionalProperties": False,
                "required": ["header", "lines"],
                "properties": {
                    "header": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["salesOrderId", "customerId", "status"],
                        "properties": {
                            "salesOrderId": {"type": "string"},
                            "customerId": {"type": "string"},
                            "status": {"type": "string"},
                            "currency": {"type": "string"},
                            "totalAmount": {"type": "number"},
                        },
                    },
                    "lines": {
                        "type": "array",
                        "items": {"type": "object", "additionalProperties": True},
                    },
                },
            },
            "schemas/ui.json": {
                "$schema": SC,
                "type": "object",
                "additionalProperties": False,
                "required": ["viewKind", "bindings"],
                "properties": {
                    "viewKind": {"const": "salesOrder.detail"},
                    "bindings": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["getCapability"],
                        "properties": {
                            "getCapability": {"type": "string"},
                            "customerLookupCapability": {"type": "string"},
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
                "request": {"salesOrderId": "so-100"},
                "response": {
                    "header": {
                        "salesOrderId": "so-100",
                        "customerId": "cus-001",
                        "status": "confirmed",
                        "currency": "USD",
                        "totalAmount": 250,
                    },
                    "lines": [{"lineId": "1", "itemId": "it-1", "quantity": 2}],
                },
            },
            {
                "request": {"salesOrderId": "missing"},
                "error": {"code": "NOT_FOUND", "message": "Sales order not found"},
            },
        ],
        tests=[
            {
                "name": "ui-view-sales-order-detail-ok",
                "request": {"salesOrderId": "so-100"},
                "expect": {"status": "success"},
            },
            {
                "name": "ui-view-sales-order-detail-not-found",
                "request": {"salesOrderId": "missing"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )
