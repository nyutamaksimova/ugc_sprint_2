import json

from src.services.producer import EventProducer


class RecordingKafka:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    def produce(self, **message) -> None:
        self.messages.append(message)

    def flush(self, timeout: float) -> int:
        return 0


def test_publish_enriches_event_and_uses_user_key():
    kafka = RecordingKafka()
    producer = EventProducer(kafka)

    producer.publish([{"event_id": "id-1", "event_type": "click"}], "user-42")

    assert kafka.messages[0]["topic"] == "click-events"
    assert kafka.messages[0]["key"] == "user-42"
    published = json.loads(kafka.messages[0]["value"])
    assert published["user_id"] == "user-42"
    assert published["schema_version"] == 1
    assert published["received_at"].endswith("+00:00")
