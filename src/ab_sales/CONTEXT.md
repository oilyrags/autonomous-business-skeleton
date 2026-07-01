# Sales & Revenue Operations

The deterministic pipeline that moves an opportunity from lead to close, and turns a won deal into a customer charge for the Revenue context.

## Language

**Lead**:
An inbound opportunity with a fit score, budget, and quoted amount — the pipeline's input.
_Avoid_: prospect, contact (a Contact is the person)

**Opportunity**:
A qualified potential deal with a stage, value, and close date.
_Avoid_: deal (until won), prospect

**Qualification**:
The gate deciding a lead is worth quoting (fit + budget thresholds).
_Avoid_: screening, vetting

**Won / Lost**:
The terminal pipeline stages; a won deal becomes a `Charge` for `ab_revenue`.
_Avoid_: closed, converted (informally)

**Contact**:
A natural person we hold data about; the DSAR subject unit.
_Avoid_: user, person, lead

**Account**:
An organization we sell to or serve (B2B).
_Avoid_: company, org, client

**Customer**:
An Account or Contact with at least one active or past paid relationship.
_Avoid_: client, buyer
