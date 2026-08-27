import json
from datetime import UTC, datetime
from typing import Any, Protocol

from src.core.topics import topic_for


class KafkaClient(Protocol):
    def produce(self, **kwargs: Any) -> None: ...

    def flush(self, timeout: float) -> int: ...


class KafkaUnavailableError(RuntimeError):
    pass


class EventProducer:
    def __init__(self, kafka: KafkaClient) -> None:
        self._kafka = kafka

    def publish(self, events: list[dict[str, Any]], user_id: str) -> None:
        try:
            for event in events:
                enriched = {
                    **event,
                    "user_id": user_id,
                    "received_at": datetime.now(UTC).isoformat(),
                    "schema_version": 1,
                }
                self._kafka.produce(
                    topic=topic_for(event["event_type"]),
                    key=user_id,
                    value=json.dumps(enriched),
                )
            if self._kafka.flush(timeout=5) != 0:
                raise KafkaUnavailableError("Kafka did not confirm delivery")
        except KafkaUnavailableError:
            raise
        except Exception as error:
            raise KafkaUnavailableError("Kafka is unavailable") from error


def build_event_producer(bootstrap_servers: str) -> EventProducer:
    from confluent_kafka import Producer

    return EventProducer(Producer({"bootstrap.servers": bootstrap_servers}))
