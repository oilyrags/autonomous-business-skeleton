# Revenue

The revenue rail: settled customer charges become balanced ledger income, per business. A real Stripe/Lemon Squeezy adapter sits behind the port.

## Language

**Charge**:
A settled customer payment (amount, currency, customer + external ref) that books to the ledger as income; the external ref is the idempotency anchor.
_Avoid_: payment, sale (a SaleClosed is the sales event), transaction

**Revenue Recognition**:
Deterministic allocation of received money to a business's `{business_id}:revenue` income account.
_Avoid_: revrec (in prose), booking

**Invoice**:
A demand for payment issued to a Customer; an account receivable.
_Avoid_: bill, statement

**Subscription**:
A recurring entitlement a Customer holds, driving repeat charges.
_Avoid_: plan, licence (a plan is the catalog template)
