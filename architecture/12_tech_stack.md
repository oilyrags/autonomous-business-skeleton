# 12 — Technology Stack (open-source / open-weight preferred)

Policy: prefer mature open-source/open-weight. Choose proprietary only when it materially beats open alternatives on a hard requirement (compliance, latency, accuracy, reliability, security, supportability, cost). **Every major choice has an abstraction boundary and an exit path** so the proprietary option is swappable.

Each row: Requirement · Recommended OSS · Managed/proprietary alt · Abstraction boundary · Rationale · Risks · Exit path.

## Core platform

| Requirement | OSS choice | Managed alt | Abstraction | Rationale | Risks | Exit path |
|---|---|---|---|---|---|---|
| LLM serving | **vLLM** (TGI/Ollama/llama.cpp) | Bedrock/Vertex/Anthropic API | Model Gateway (OpenAI-compatible) | high throughput, open | GPU ops burden | swap behind gateway; profiles unchanged |
| Open-weight models | **Llama, Qwen, Mistral/Mixtral, DeepSeek, Gemma** | managed frontier | Task Profiles (`11`) | swappable, on-prem capable | quality gap on hardest tasks | dual primary+managed per critical profile |
| Agent orchestration | **LangGraph** (+ LlamaIndex/Haystack for RAG) | managed agent svc | agent runtime interface | stateful graphs, OSS | framework churn | graphs are code; portable |
| Durable workflows | **Temporal** (Argo/Dagster/Prefect) | Temporal Cloud | Workflow context API | exactly-once, durable, approvals | operational complexity | Temporal OSS ↔ Cloud identical SDK |
| Event backbone | **Redpanda** (Kafka API) / Kafka / NATS / Pulsar | Confluent/MSK | AsyncAPI contracts | Kafka-compatible, simpler ops | partition design | Kafka wire-compat = portable |
| APIs | **REST + gRPC**, OpenAPI, AsyncAPI, GraphQL (BFF) | API gateways | contract specs | standard, tooled | over-fragmentation | specs are vendor-neutral |

## Data fabric

| Requirement | OSS choice | Managed alt | Abstraction | Rationale | Risks | Exit path |
|---|---|---|---|---|---|---|
| Lakehouse table format | **Apache Iceberg** (or Delta) | Databricks/Snowflake | medallion + data contracts | open table format, engine-agnostic | metadata ops | Iceberg readable by many engines |
| Transform | **dbt** (+ DuckDB local) | dbt Cloud | semantic layer above | standard, tested | model sprawl | SQL/dbt portable |
| Query engines | **Trino, DuckDB, ClickHouse, Postgres** | managed equivalents | semantic layer | right tool per workload | many engines | SQL-standard |
| Semantic / metrics | **Cube** (or MetricFlow) | proprietary BI | one-definition-per-KPI rule | governs canonical metrics | adoption discipline | metric defs as code |
| BI | **Superset / Metabase** | Looker/Tableau | semantic layer | OSS dashboards | feature gaps | dashboards re-pointable |
| Vector search | **Qdrant** (Weaviate/Milvus/pgvector) | Pinecone | retrieval interface | OSS, fast, filterable | scaling | embeddings portable; re-index |
| Knowledge graph | **Neo4j Community / Apache AGE** | Neptune | KG interface | provenance/relationships | query lang lock | export to RDF/Cypher |
| Catalog / lineage | **OpenMetadata / DataHub**, **OpenLineage** | managed catalogs | catalog API | lineage = compliance evidence | integration effort | open standards |
| Feature store | **Feast** | managed | feature interface | OSS, online/offline | freshness | feature defs as code |

## AI / LLM ops

| Requirement | OSS choice | Managed alt | Abstraction | Rationale | Risks | Exit path |
|---|---|---|---|---|---|---|
| Model registry / experiments | **MLflow** | managed MLOps | registry interface | standard | scale | open format |
| Drift / data quality | **Evidently** | managed | monitoring hooks | OSS | tuning | metrics portable |
| LLM tracing / evals | **Langfuse** + custom harness | LangSmith | tracing interface | OSS, self-host | eval coverage | OTel-based, portable |
| Tracing standard | **OpenTelemetry** | vendor APM | OTel | universal | volume | vendor-neutral |

## Governance, security, infra

| Requirement | OSS choice | Managed alt | Abstraction | Rationale | Risks | Exit path |
|---|---|---|---|---|---|---|
| Policy-as-code | **OPA** (+ Cedar-style) | managed policy | authZ interface (`10`) | standard, testable | policy sprawl | Rego/Cedar portable |
| IAM | **Keycloak / Zitadel** | Auth0/Okta | OIDC | OSS OIDC | HA ops | OIDC standard |
| Secrets | **Vault** + **SOPS** | cloud KMS/secrets | secrets interface | OSS, mature | ops | export/migrate |
| Observability | **Prometheus, Grafana, Loki, Tempo** | Datadog | OTel + PromQL | OSS stack | storage cost | OTel portable |
| Infra | **Kubernetes, OpenTofu, Helm, GitOps (Argo/Flux)** | managed K8s | IaC | portable, declarative | complexity | OpenTofu multi-cloud |
| Security scanning | **Trivy, Syft/Grype, Semgrep, OWASP ZAP, Falco** | commercial AppSec | CI gates | OSS coverage | noise | CI-pluggable |

## When proprietary is justified (documented exceptions)

- **Frontier model for the hardest reasoning/coding** where open-weight eval scores miss the bar — used *via the gateway*, behind a task profile, with an open-weight fallback always wired. Exit path: flip the profile's primary.
- **Managed KMS / HSM** where a compliance pack (payments) requires certified key custody. Exit path: envelope-encryption keys re-wrappable.
- **Sovereign managed cloud** where a jurisdiction mandates it. Exit path: OpenTofu modules + Iceberg/Postgres portability.

Every exception carries: requirement, why open fell short (evidence), abstraction boundary, and a tested exit path — audited in `16` (open-source audit).
