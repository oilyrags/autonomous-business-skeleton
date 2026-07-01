# Ledger

The deterministic double-entry ledger — the single source of truth for money. Integer minor units, balanced postings, idempotent and maker-checker governed.

## Language

**Ledger Entry**:
An append-only, double-entry accounting record; immutable. Signed postings that sum to zero.
_Avoid_: transaction, posting, journal (informally)

**Maker-Checker**:
The separation-of-duties control: a payment over the cap or to a new payee needs a *checker* distinct from the *maker*.
_Avoid_: dual control, four-eyes (informally)

**Spend Cap**:
A pre-authorized maximum an agent may commit (in one payment) without human approval.
_Avoid_: budget, limit (a Budget is the planned-spend aggregate)

**Trial Balance**:
The balance invariant: the ledger's signed entries always sum to zero.
_Avoid_: reconciliation, total
