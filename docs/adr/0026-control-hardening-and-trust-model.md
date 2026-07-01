---
status: accepted
---

# Control hardening from an adversarial self-review + the caller-assertion trust model

After closing the verification audits, an adversarial review of the control code surfaced a
set of weak/partial spots. This ADR records the three that were fixed and documents the
limitations that are inherent to the current (pre-provenance) trust model.

## Fixed

- **Payee allow-list could be dodged by omitting `payee`** (`ab_ledger.core`). The new-payee
  maker-checker rule keyed on an *optional* `Transaction.payee`, so an under-cap payment with
  `payee=None` bypassed the allow-list. Payees are now **derived** from the postings:
  money leaving to an `external:<party>` account contributes `<party>` to `Transaction.payees`
  (plus any explicit `payee`). An outbound payment can no longer hide its counterparty by
  leaving a field blank. *(Residual: this still relies on external movements being booked to
  `external:` accounts — a full fix needs a typed chart of accounts; deferred.)*
- **Art.22 profile with no declared bias threshold slipped through** (`ab_evals.gate`). The
  gate required a bias *dimension* to exist for `art22_significant` profiles but not a
  *threshold*, so a failing bias case could pass on overall score. The gate now
  `setdefault`s the Art.22 bias threshold to **1.0**, so significant-decision profiles always
  clear a full bias bar even if the suite author forgot to set one.
- **Compliance check was inconsistent about `financial`** (`ab_compliance.ropa`). It demanded
  a lawful basis for `financial` 08 records but exempted `financial` events. Made it explicit
  and GDPR-correct: **lawful basis is a `personal`-data requirement** (`_NEEDS_BASIS`), while
  **both `personal` and `financial` must be inventoried + retention-mapped** (`_MUST_INVENTORY`).

## Known limitations (documented, not silently accepted)

- **Caller-asserted classification & trust** (`ToolCallRequest.data_classification`,
  `untrusted_input`). The exfiltration and prompt-injection gates key off fields the calling
  agent sets, defaulting to permissive (`internal` / `false`). They are genuine
  defense-in-depth against accidental/buggy leakage, but a *fully compromised* agent can lie
  about its own data. Robustly closing this needs server-side derivation of classification and
  trust from data provenance / flow-tracking — deferred to the data-governance phase.
- **Grounding "abstain" proxy** (`ab_evals.suites._abstains`) treats "contains ABSTAIN and no
  digit" as "didn't fabricate" — a narrow proxy; a real grounding judge (citation faithfulness
  over retrieved sources) supersedes it later.
- **`ops_long_2` retention alias** in `08` is a documentation stub the RoPA check accepts as a
  defined policy; tighten when `08` is completed per venture.

## Verified

`make compliance` / `make failsim` still pass; the `bad_payment` scenario now exercises the
derived-payee path (external account, no `payee` field). +3 tests (external-account approval;
Art.22 bias-floor block; consistent compliance rules). Full ledger suite (17) green against
Postgres; lint + mypy strict clean.
