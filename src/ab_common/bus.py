"""Redpanda (Kafka API) producer/consumer helpers via confluent-kafka."""

from collections.abc import Iterator

from confluent_kafka import Consumer, Producer
from confluent_kafka.admin import AdminClient, NewTopic  # type: ignore[attr-defined]

from .config import settings


def ensure_topic(topic: str, *, num_partitions: int = 1) -> None:
    """Create the topic if it does not exist (idempotent)."""
    admin = AdminClient({"bootstrap.servers": settings.kafka_bootstrap})
    existing = admin.list_topics(timeout=10).topics
    if topic in existing:
        return
    futures = admin.create_topics([NewTopic(topic, num_partitions=num_partitions, replication_factor=1)])
    for fut in futures.values():
        try:
            fut.result(timeout=10)
        except Exception:  # noqa: BLE001 - topic may have been created concurrently
            pass


def publish(topic: str, key: str, value: str) -> None:
    producer = Producer({"bootstrap.servers": settings.kafka_bootstrap})
    producer.produce(topic, key=key.encode(), value=value.encode())
    producer.flush(10)


def consume(topic: str, group: str, *, max_messages: int = 1, timeout: float = 10.0) -> Iterator[str]:
    """Yield up to ``max_messages`` message values from ``topic`` (decoded)."""
    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap,
            "group.id": group,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
        }
    )
    consumer.subscribe([topic])
    seen = 0
    try:
        while seen < max_messages:
            msg = consumer.poll(timeout)
            if msg is None:
                break
            if msg.error():
                continue
            value = msg.value()
            if value is None:
                continue
            seen += 1
            yield value.decode()
    finally:
        consumer.close()
