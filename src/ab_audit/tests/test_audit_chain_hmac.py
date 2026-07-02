"""The audit chain link is keyed (VULN-006): its value depends on a key held outside the DB, so a
DB-write adversary without the key cannot forge a valid successor hash. Pure — no infra."""

from __future__ import annotations

import hmac
from hashlib import sha256

import pytest

from ab_audit import store


def test_chain_link_is_an_hmac_under_the_audit_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(store.settings, "audit_hmac_key", "the-real-key")
    expected = hmac.new(b"the-real-key", b"PREVCANON", sha256).hexdigest()
    assert store._hash("PREV", "CANON") == expected  # keyed, not a bare sha256(prev+canon)
    assert store._hash("PREV", "CANON") != sha256(b"PREVCANON").hexdigest()  # unkeyed would differ


def test_a_wrong_key_produces_a_different_link(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(store.settings, "audit_hmac_key", "genuine-key")
    genuine = store._hash("PREV", "CANON")
    monkeypatch.setattr(store.settings, "audit_hmac_key", "attacker-guess")
    assert store._hash("PREV", "CANON") != genuine  # can't re-forge the chain without the key
