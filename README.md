# Autonomous AI-First Business Skeleton

The **operating system of an AI-run business**: a reusable, domain-driven architecture skeleton on which many business ideas can be launched, operated, scaled, pivoted, or shut down without rebuilding the foundation. AI-first, open-source-preferred, privacy-preserving (GDPR-first), audit-ready, and deterministic where it must be (money, identity, access, consent, irreversible actions).

## Start here

- **[PROJECT.md](PROJECT.md)** — living project tracker: status, decisions, pending work, conventions, change log. **Read this first.**
- **[autonomous-business-architecture-merged-prompt.md](autonomous-business-architecture-merged-prompt.md)** — the master spec (requirements, schemas, acceptance criteria).
- **[architecture/](architecture/)** — the design package (19 artifacts).

## The architecture package

Mode B (Build Specification). Bounded contexts, agents, events, data model, compliance, security, decision OS, roadmap, and verification:

| | Artifact |
|---|---|
| 00 | [Enterprise overview](architecture/00_enterprise_overview.md) |
| 01 | [Context map](architecture/01_context_map.mermaid) |
| 02 | [Ubiquitous glossary](architecture/02_ubiquitous_glossary.md) |
| 03 | [Domain catalog](architecture/03_domain_catalog.md) (16 bounded contexts) |
| 04 | [Event catalog](architecture/04_event_catalog.md) + [AsyncAPI spec](architecture/events.asyncapi.yaml) |
| 05 | [Agent registry](architecture/05_agent_registry.json) |
| 06 | [Autonomy authority matrix](architecture/06_autonomy_authority_matrix.md) |
| 07 | [Canonical data model](architecture/07_data_model.md) + [data inventory](architecture/08_data_inventory_template.json) |
| 09 | [Compliance architecture](architecture/09_compliance_architecture.md) |
| 10 | [Security architecture](architecture/10_security_architecture.md) |
| 11 | [Model & agent architecture](architecture/11_model_and_agent_architecture.md) |
| 12 | [Technology stack](architecture/12_tech_stack.md) |
| 13 | [Decision operating system](architecture/13_decision_operating_system.md) |
| 14 | [Instantiation guide](architecture/14_instantiation_guide.md) (worked example) |
| 15 | [Implementation roadmap & backlog](architecture/15_implementation_roadmap.md) |
| 16 | [Verification report](architecture/16_verification_report.md) |
| — | [Minimum viable skeleton](architecture/business_skeleton.md) |

## Status

Design package **v1.0 complete**. Implementation not started. See [PROJECT.md](PROJECT.md) for current status and next steps.
