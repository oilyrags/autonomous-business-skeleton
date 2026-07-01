"""CLI: consume decisions from the event bus, build the warehouse, print canonical KPIs.

uv run python -m ab_data
"""

from ab_data import freshness, ingest, pipeline


def main() -> None:
    landed = ingest.consume_to_bronze(group="ab-data-cli", max_messages=1000, timeout=5.0)
    if landed == 0:
        print("no AgentDecisionMade events on the bus — nothing to build")
        return
    result = pipeline.run()  # bronze already landed by consume_to_bronze
    print(f"landed {landed} event(s); silver rows = {result.bronze_rows}")
    print("canonical KPIs:")
    for name, value in result.metrics.items():
        print(f"  {name} = {value}")
    for q in result.quality:
        print(f"  [{'ok' if q.passed else 'FAIL'}] {q.check}: {q.detail}")
    f = freshness.read_freshness()
    latest = f.latest_event_at.isoformat() if f.latest_event_at else "—"
    print(f"freshness: {f.rows} row(s), newest event {latest}")


if __name__ == "__main__":
    main()
