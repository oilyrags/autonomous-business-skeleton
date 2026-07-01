# Schemas (shared kernel)

The shared kernel: the Pydantic models for every domain event (matching the AsyncAPI contract) and the gateway's tool-argument schemas. Depended on by all contexts.

## Language

**Envelope**:
The common block every domain event carries: event name, id, occurred-at, producer, classification, subject_ref.
_Avoid_: header, metadata

**Subject Ref**:
The typed reference to what an event is about (a Business, Experiment, LedgerTransaction, Charge…).
_Avoid_: target, entity, ref (bare)

**Data Classification**:
An event's sensitivity tier (public / internal / confidential / personal / financial) that governs egress.
_Avoid_: label, tag, level
