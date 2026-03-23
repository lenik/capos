"""Reference implementation for contact.* capabilities (in-memory)."""

from __future__ import annotations

import re
from typing import Any

from utils.captest.runner import CapError


def _norm_id(s: str) -> str:
    return (s or "").strip()


def _valid_email(s: str) -> bool:
    if not s:
        return True
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", s))


class ContactBook:
    def __init__(self) -> None:
        self._by_id: dict[str, dict[str, Any]] = {}
        self._email_owner: dict[str, str] = {}
        self._tombstone: set[str] = set()
        self._seq = 0
        self._protected_delete: set[str] = set()

    def _next_id(self) -> str:
        self._seq += 1
        return f"con-{self._seq}"

    def seed_contact(
        self,
        contact_id: str,
        *,
        display_name: str,
        email: str | None = None,
        version: int = 1,
    ) -> None:
        row = {
            "contactId": contact_id,
            "displayName": display_name,
            "email": email,
            "phone": None,
            "companyName": None,
            "tags": [],
            "version": version,
        }
        self._by_id[contact_id] = row
        if email:
            self._email_owner[email.lower()] = contact_id

    def mark_referenced(self, contact_id: str) -> None:
        self._protected_delete.add(contact_id)

    def create(self, req: dict[str, Any]) -> dict[str, Any]:
        name = req.get("displayName", "")
        if not isinstance(name, str) or len(name.strip()) == 0:
            raise CapError("INVALID_REQUEST", "displayName is required")
        email = req.get("email")
        if email is not None:
            if not isinstance(email, str) or not _valid_email(email):
                raise CapError("INVALID_REQUEST", "invalid email")
            if email.lower() in self._email_owner:
                raise CapError("CONFLICT", "duplicate email")
        cid = self._next_id()
        row = {
            "contactId": cid,
            "displayName": name.strip(),
            "email": email,
            "phone": req.get("phone"),
            "companyName": req.get("companyName"),
            "tags": list(req.get("tags") or []),
            "version": 1,
        }
        self._by_id[cid] = row
        if email:
            self._email_owner[email.lower()] = cid
        out: dict[str, Any] = {
            "contactId": cid,
            "displayName": row["displayName"],
            "version": row["version"],
        }
        for k in ("email", "phone", "companyName", "tags"):
            if row.get(k) not in (None, [], ""):
                out[k] = row[k]
        return out

    def get(self, req: dict[str, Any]) -> dict[str, Any]:
        cid = _norm_id(req.get("contactId", ""))
        if not cid:
            raise CapError("INVALID_REQUEST", "contactId is required")
        row = self._by_id.get(cid)
        if not row:
            raise CapError("NOT_FOUND", "Contact not found")
        return self._public(row)

    def search(self, req: dict[str, Any]) -> dict[str, Any]:
        q = (req.get("query") or "").strip().lower()
        tag = (req.get("tag") or "").strip()
        page = req.get("page") or {}
        limit = page.get("limit", 50)
        if limit is not None and limit < 1:
            raise CapError("INVALID_REQUEST", "limit must be >= 1")
        if limit is not None and limit > 500:
            raise CapError("INVALID_REQUEST", "limit exceeds maximum")
        items = []
        for row in self._by_id.values():
            blob = " ".join(
                filter(
                    None,
                    [
                        row.get("displayName"),
                        row.get("email"),
                        row.get("companyName"),
                    ],
                )
            ).lower()
            if q and q not in blob:
                continue
            if tag and tag not in (row.get("tags") or []):
                continue
            items.append(
                {
                    "contactId": row["contactId"],
                    "displayName": row["displayName"],
                    **({"email": row["email"]} if row.get("email") else {}),
                    **({"companyName": row["companyName"]} if row.get("companyName") else {}),
                    **({"tags": row["tags"]} if row.get("tags") else {}),
                }
            )
        return {"items": items, "page": {"hasMore": False}}

    def update(self, req: dict[str, Any]) -> dict[str, Any]:
        cid = _norm_id(req.get("contactId", ""))
        if not cid:
            raise CapError("INVALID_REQUEST", "contactId is required")
        row = self._by_id.get(cid)
        if not row:
            raise CapError("NOT_FOUND", "Contact not found")
        ev = req.get("expectedVersion")
        if ev is not None and ev != row["version"]:
            raise CapError("CONFLICT", "Version mismatch")
        if "displayName" in req:
            dn = req["displayName"]
            if not isinstance(dn, str) or len(dn.strip()) == 0:
                raise CapError("INVALID_REQUEST", "displayName invalid")
            row["displayName"] = dn.strip()
        if "email" in req:
            em = req["email"]
            if em is not None and (not isinstance(em, str) or not _valid_email(em)):
                raise CapError("INVALID_REQUEST", "invalid email")
            old = row.get("email")
            if old and str(old).lower() in self._email_owner:
                del self._email_owner[str(old).lower()]
            row["email"] = em
            if em:
                self._email_owner[em.lower()] = cid
        if "phone" in req:
            row["phone"] = req["phone"] or None
        if "companyName" in req:
            row["companyName"] = req["companyName"]
        if "tags" in req and req["tags"] is not None:
            row["tags"] = list(req["tags"])
        row["version"] = int(row["version"]) + 1
        return self._public(row)

    def delete(self, req: dict[str, Any]) -> dict[str, Any]:
        cid = _norm_id(req.get("contactId", ""))
        if not cid:
            raise CapError("INVALID_REQUEST", "contactId is required")
        if cid in self._protected_delete:
            raise CapError("CONFLICT", "Contact referenced by party master")
        if cid in self._by_id:
            row = self._by_id.pop(cid)
            em = row.get("email")
            if em and str(em).lower() in self._email_owner:
                del self._email_owner[str(em).lower()]
            self._tombstone.add(cid)
            return {"deleted": True, "contactId": cid}
        if cid in self._tombstone:
            return {"deleted": True, "contactId": cid}
        raise CapError("NOT_FOUND", "Contact not found")

    def _public(self, row: dict[str, Any]) -> dict[str, Any]:
        out = {
            "contactId": row["contactId"],
            "displayName": row["displayName"],
            "version": row["version"],
        }
        for k in ("email", "phone", "companyName", "tags"):
            if row.get(k) is not None and row.get(k) != []:
                out[k] = row[k]
        return out


class ContactBookAdapter:
    def __init__(self, book: ContactBook) -> None:
        self.book = book

    @classmethod
    def with_demo_data(cls) -> ContactBookAdapter:
        b = ContactBook()
        b.seed_contact(
            "con-100",
            display_name="Jordan Smith",
            email="jordan@example.com",
            version=1,
        )
        b.seed_contact(
            "con-dup-seed",
            display_name="Existing Dup",
            email="duplicate@example.com",
            version=1,
        )
        b.mark_referenced("con-in-use")
        b.seed_contact("con-in-use", display_name="Locked", email="locked@example.com")
        b.seed_contact("con-200", display_name="Disposable", email="disposable@example.com")
        return cls(b)

    def invoke(self, capability_name: str, request: dict[str, Any]) -> dict[str, Any]:
        if capability_name == "contact.create":
            return self.book.create(request)
        if capability_name == "contact.get":
            return self.book.get(request)
        if capability_name == "contact.search":
            return self.book.search(request)
        if capability_name == "contact.update":
            return self.book.update(request)
        if capability_name == "contact.delete":
            return self.book.delete(request)
        raise CapError("INVALID_REQUEST", f"unknown capability {capability_name}")
