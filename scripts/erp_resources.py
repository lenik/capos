"""ERP TODO §9 resource capabilities (file, object, cache, queue). Used by generate_erp_modules."""

from __future__ import annotations

SC = "https://json-schema.org/draft/2020-12/schema"


def emit_resource_capabilities(emit_capability) -> None:
    """Emit type=resource capabilities with request-response signatures."""

    def er(
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
            capability_type="resource",
        )

    # --- Files ---
    er(
        "file.upload",
        "file",
        "Register an upload session or accept streamed file metadata and return a stored file id.",
        idempotent=False,
        side_effect=True,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["fileName", "contentType", "sizeBytes"],
            "properties": {
                "fileName": {"type": "string", "minLength": 1},
                "contentType": {"type": "string"},
                "sizeBytes": {"type": "integer", "minimum": 0},
                "sha256": {"type": "string"},
                "folder": {"type": "string"},
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["fileId", "uri"],
            "properties": {
                "fileId": {"type": "string"},
                "uri": {"type": "string"},
            },
        },
        examples=[
            {
                "request": {
                    "fileName": "quote.pdf",
                    "contentType": "application/pdf",
                    "sizeBytes": 102400,
                },
                "response": {"fileId": "fil-9a2", "uri": "s3://bucket/key"},
            },
            {
                "request": {"fileName": "", "contentType": "application/pdf", "sizeBytes": 0},
                "error": {"code": "INVALID_REQUEST", "message": "fileName is required"},
            },
        ],
        tests=[
            {
                "name": "file-upload-ok",
                "request": {
                    "fileName": "a.bin",
                    "contentType": "application/octet-stream",
                    "sizeBytes": 10,
                },
                "expect": {"status": "success"},
            },
            {
                "name": "file-upload-invalid-name",
                "request": {
                    "fileName": "",
                    "contentType": "application/octet-stream",
                    "sizeBytes": 1,
                },
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    er(
        "file.download",
        "file",
        "Resolve a time-limited download URL or transfer handle for a stored file.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["fileId"],
            "properties": {"fileId": {"type": "string"}},
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["downloadUrl", "expiresAt", "fileName", "contentType", "sizeBytes"],
            "properties": {
                "downloadUrl": {"type": "string"},
                "expiresAt": {"type": "string", "format": "date-time"},
                "fileName": {"type": "string"},
                "contentType": {"type": "string"},
                "sizeBytes": {"type": "integer", "minimum": 0},
            },
        },
        examples=[
            {
                "request": {"fileId": "fil-9a2"},
                "response": {
                    "downloadUrl": "https://storage.example/get?sig=abc",
                    "expiresAt": "2025-03-23T15:00:00Z",
                    "fileName": "quote.pdf",
                    "contentType": "application/pdf",
                    "sizeBytes": 102400,
                },
            },
            {
                "request": {"fileId": "missing"},
                "error": {"code": "NOT_FOUND", "message": "File not found"},
            },
        ],
        tests=[
            {
                "name": "file-download-ok",
                "request": {"fileId": "fil-9a2"},
                "expect": {"status": "success"},
            },
            {
                "name": "file-download-not-found",
                "request": {"fileId": "missing"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )

    er(
        "file.delete",
        "file",
        "Delete a stored file by id (irreversible).",
        idempotent=False,
        side_effect=True,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["fileId"],
            "properties": {"fileId": {"type": "string"}},
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["deleted"],
            "properties": {"deleted": {"type": "boolean"}},
        },
        examples=[
            {"request": {"fileId": "fil-9a2"}, "response": {"deleted": True}},
            {
                "request": {"fileId": "missing"},
                "error": {"code": "NOT_FOUND", "message": "File not found"},
            },
        ],
        tests=[
            {"name": "file-delete-ok", "request": {"fileId": "fil-9a2"}, "expect": {"status": "success"}},
            {
                "name": "file-delete-not-found",
                "request": {"fileId": "missing"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )

    er(
        "file.preview",
        "file",
        "Obtain a preview URL or rendition for an image or document file.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["fileId"],
            "properties": {
                "fileId": {"type": "string"},
                "variant": {"type": "string", "enum": ["thumb", "medium", "pdf"]},
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["previewUrl", "expiresAt"],
            "properties": {
                "previewUrl": {"type": "string"},
                "expiresAt": {"type": "string", "format": "date-time"},
            },
        },
        examples=[
            {
                "request": {"fileId": "fil-9a2", "variant": "thumb"},
                "response": {
                    "previewUrl": "https://cdn.example/p/fil-9a2-thumb",
                    "expiresAt": "2025-03-23T16:00:00Z",
                },
            },
            {
                "request": {"fileId": "missing"},
                "error": {"code": "NOT_FOUND", "message": "File not found"},
            },
        ],
        tests=[
            {
                "name": "file-preview-ok",
                "request": {"fileId": "fil-9a2", "variant": "thumb"},
                "expect": {"status": "success"},
            },
            {
                "name": "file-preview-not-found",
                "request": {"fileId": "missing"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )

    # --- Object storage ---
    er(
        "object.put",
        "object",
        "Register or complete put of an object into a bucket/key namespace.",
        idempotent=False,
        side_effect=True,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["bucket", "objectKey", "contentType", "sizeBytes"],
            "properties": {
                "bucket": {"type": "string"},
                "objectKey": {"type": "string"},
                "contentType": {"type": "string"},
                "sizeBytes": {"type": "integer", "minimum": 0},
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["etag"],
            "properties": {
                "etag": {"type": "string"},
                "versionId": {"type": "string"},
            },
        },
        examples=[
            {
                "request": {
                    "bucket": "erp-docs",
                    "objectKey": "2025/so-100/attach.bin",
                    "contentType": "application/octet-stream",
                    "sizeBytes": 2048,
                },
                "response": {"etag": '"abc123"', "versionId": "v1"},
            },
            {
                "request": {
                    "bucket": "",
                    "objectKey": "k",
                    "contentType": "application/octet-stream",
                    "sizeBytes": 1,
                },
                "error": {"code": "INVALID_REQUEST", "message": "bucket is required"},
            },
        ],
        tests=[
            {
                "name": "object-put-ok",
                "request": {
                    "bucket": "b",
                    "objectKey": "k",
                    "contentType": "application/octet-stream",
                    "sizeBytes": 1,
                },
                "expect": {"status": "success"},
            },
            {
                "name": "object-put-invalid",
                "request": {
                    "bucket": "",
                    "objectKey": "k",
                    "contentType": "application/octet-stream",
                    "sizeBytes": 1,
                },
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    er(
        "object.get",
        "object",
        "Resolve a time-limited URL or read handle for an object in storage.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["bucket", "objectKey"],
            "properties": {
                "bucket": {"type": "string"},
                "objectKey": {"type": "string"},
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["downloadUrl", "expiresAt", "sizeBytes"],
            "properties": {
                "downloadUrl": {"type": "string"},
                "expiresAt": {"type": "string", "format": "date-time"},
                "sizeBytes": {"type": "integer", "minimum": 0},
            },
        },
        examples=[
            {
                "request": {"bucket": "erp-docs", "objectKey": "2025/a.bin"},
                "response": {
                    "downloadUrl": "https://s3.example/presigned",
                    "expiresAt": "2025-03-23T17:00:00Z",
                    "sizeBytes": 2048,
                },
            },
            {
                "request": {"bucket": "erp-docs", "objectKey": "none"},
                "error": {"code": "NOT_FOUND", "message": "Object not found"},
            },
        ],
        tests=[
            {
                "name": "object-get-ok",
                "request": {"bucket": "b", "objectKey": "k"},
                "expect": {"status": "success"},
            },
            {
                "name": "object-get-not-found",
                "request": {"bucket": "b", "objectKey": "missing"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )

    er(
        "object.delete",
        "object",
        "Delete an object from a bucket/key namespace.",
        idempotent=False,
        side_effect=True,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["bucket", "objectKey"],
            "properties": {
                "bucket": {"type": "string"},
                "objectKey": {"type": "string"},
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["deleted"],
            "properties": {"deleted": {"type": "boolean"}},
        },
        examples=[
            {
                "request": {"bucket": "erp-docs", "objectKey": "2025/a.bin"},
                "response": {"deleted": True},
            },
            {
                "request": {"bucket": "erp-docs", "objectKey": "none"},
                "error": {"code": "NOT_FOUND", "message": "Object not found"},
            },
        ],
        tests=[
            {
                "name": "object-delete-ok",
                "request": {"bucket": "b", "objectKey": "k"},
                "expect": {"status": "success"},
            },
            {
                "name": "object-delete-not-found",
                "request": {"bucket": "b", "objectKey": "missing"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )

    # --- Cache ---
    er(
        "cache.get",
        "cache",
        "Read a value from a namespaced cache key.",
        idempotent=True,
        side_effect=False,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["namespace", "key"],
            "properties": {
                "namespace": {"type": "string"},
                "key": {"type": "string"},
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["hit"],
            "properties": {
                "hit": {"type": "boolean"},
                "value": {},
            },
        },
        examples=[
            {
                "request": {"namespace": "pricing", "key": "item:it-1"},
                "response": {"hit": True, "value": {"listPrice": 9.99}},
            },
            {
                "request": {"namespace": "pricing", "key": "missing"},
                "response": {"hit": False},
            },
        ],
        tests=[
            {
                "name": "cache-get-hit",
                "request": {"namespace": "n", "key": "k"},
                "expect": {"status": "success"},
            },
            {
                "name": "cache-get-miss",
                "request": {"namespace": "n", "key": "unknown"},
                "expect": {"status": "success"},
            },
        ],
    )

    er(
        "cache.set",
        "cache",
        "Store a JSON-serializable value under a namespaced cache key with optional TTL.",
        idempotent=False,
        side_effect=True,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["namespace", "key", "value"],
            "properties": {
                "namespace": {"type": "string"},
                "key": {"type": "string"},
                "value": True,
                "ttlSeconds": {"type": "integer", "minimum": 1},
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["ok"],
            "properties": {"ok": {"type": "boolean"}},
        },
        examples=[
            {
                "request": {
                    "namespace": "pricing",
                    "key": "item:it-1",
                    "value": {"listPrice": 9.99},
                    "ttlSeconds": 300,
                },
                "response": {"ok": True},
            },
            {
                "request": {"namespace": "", "key": "k", "value": 1},
                "error": {"code": "INVALID_REQUEST", "message": "namespace is required"},
            },
        ],
        tests=[
            {
                "name": "cache-set-ok",
                "request": {"namespace": "n", "key": "k", "value": {"a": 1}},
                "expect": {"status": "success"},
            },
            {
                "name": "cache-set-invalid",
                "request": {"namespace": "", "key": "k", "value": 1},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    er(
        "cache.delete",
        "cache",
        "Remove a key from a cache namespace.",
        idempotent=False,
        side_effect=True,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["namespace", "key"],
            "properties": {
                "namespace": {"type": "string"},
                "key": {"type": "string"},
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["deleted"],
            "properties": {"deleted": {"type": "boolean"}},
        },
        examples=[
            {"request": {"namespace": "pricing", "key": "item:it-1"}, "response": {"deleted": True}},
            {
                "request": {"namespace": "", "key": "k"},
                "error": {"code": "INVALID_REQUEST", "message": "namespace is required"},
            },
        ],
        tests=[
            {"name": "cache-delete-ok", "request": {"namespace": "n", "key": "k"}, "expect": {"status": "success"}},
            {
                "name": "cache-delete-invalid",
                "request": {"namespace": "", "key": "k"},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    # --- Queue ---
    er(
        "queue.publish",
        "queue",
        "Publish a message to a topic or queue endpoint.",
        idempotent=False,
        side_effect=True,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["topic", "body"],
            "properties": {
                "topic": {"type": "string"},
                "body": {"type": "object", "additionalProperties": True},
                "attributes": {"type": "object", "additionalProperties": {"type": "string"}},
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["messageId"],
            "properties": {"messageId": {"type": "string"}},
        },
        examples=[
            {
                "request": {
                    "topic": "erp.inventory.movement",
                    "body": {"movementId": "mov-1"},
                    "attributes": {"correlationId": "c1"},
                },
                "response": {"messageId": "msg-77"},
            },
            {
                "request": {"topic": "", "body": {}},
                "error": {"code": "INVALID_REQUEST", "message": "topic is required"},
            },
        ],
        tests=[
            {
                "name": "queue-publish-ok",
                "request": {"topic": "t", "body": {"a": 1}},
                "expect": {"status": "success"},
            },
            {
                "name": "queue-publish-invalid",
                "request": {"topic": "", "body": {}},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    er(
        "queue.consume",
        "queue",
        "Pull up to N messages from a subscription with optional visibility timeout.",
        idempotent=False,
        side_effect=True,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["subscriptionId", "maxMessages"],
            "properties": {
                "subscriptionId": {"type": "string"},
                "maxMessages": {"type": "integer", "minimum": 1, "maximum": 100},
                "visibilityTimeoutSeconds": {"type": "integer", "minimum": 0},
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["messages"],
            "properties": {
                "messages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["messageId", "body"],
                        "properties": {
                            "messageId": {"type": "string"},
                            "body": {"type": "object", "additionalProperties": True},
                            "attributes": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                            },
                        },
                    },
                }
            },
        },
        examples=[
            {
                "request": {"subscriptionId": "sub-inv", "maxMessages": 10},
                "response": {
                    "messages": [
                        {
                            "messageId": "msg-77",
                            "body": {"movementId": "mov-1"},
                            "attributes": {},
                        }
                    ]
                },
            },
            {
                "request": {"subscriptionId": "", "maxMessages": 5},
                "error": {"code": "INVALID_REQUEST", "message": "subscriptionId is required"},
            },
        ],
        tests=[
            {
                "name": "queue-consume-ok",
                "request": {"subscriptionId": "sub", "maxMessages": 1},
                "expect": {"status": "success"},
            },
            {
                "name": "queue-consume-invalid",
                "request": {"subscriptionId": "", "maxMessages": 1},
                "expectError": {"code": "INVALID_REQUEST"},
            },
        ],
    )

    er(
        "database.connection.ping",
        "database",
        "Verify a pooled DB connection handle is alive (resource layer; distinct from data.csql.query).",
        idempotent=True,
        side_effect=False,
        transactional=False,
        request={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["connectionHandle"],
            "properties": {
                "connectionHandle": {
                    "type": "string",
                    "description": "Opaque handle from the pool; not a SQL string.",
                }
            },
        },
        response={
            "$schema": SC,
            "type": "object",
            "additionalProperties": False,
            "required": ["ok", "latencyMs"],
            "properties": {
                "ok": {"type": "boolean"},
                "latencyMs": {"type": "number", "minimum": 0},
            },
        },
        examples=[
            {
                "request": {"connectionHandle": "dbh-pool-7f3a"},
                "response": {"ok": True, "latencyMs": 2.5},
            },
            {
                "request": {"connectionHandle": "expired"},
                "error": {"code": "NOT_FOUND", "message": "Connection handle unknown or expired"},
            },
        ],
        tests=[
            {
                "name": "database-ping-ok",
                "request": {"connectionHandle": "dbh-1"},
                "expect": {"status": "success"},
            },
            {
                "name": "database-ping-bad-handle",
                "request": {"connectionHandle": "expired"},
                "expectError": {"code": "NOT_FOUND"},
            },
        ],
    )
