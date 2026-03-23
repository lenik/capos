"""Unit tests: contactbook implementation vs sample/caps/contact.* CapSpecs (captest)."""

from __future__ import annotations

from pathlib import Path

import pytest

from contactbook.cap_impl import ContactBookAdapter
from utils.captest.runner import run_capabilities_matching

REPO = Path(__file__).resolve().parents[4]


def test_contact_capabilities_match_capspec() -> None:
    fails = run_capabilities_matching(
        REPO / "sample" / "caps",
        adapter_factory=lambda: ContactBookAdapter.with_demo_data().invoke,
        name_prefix="contact.",
    )
    assert not fails, "\n".join(fails)
