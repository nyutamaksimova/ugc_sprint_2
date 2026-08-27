import pytest

from src.models.schemas import BatchValidationError, validate_batch, validate_event
from src.core.topics import topic_for


def test_quality_event_maps_to_video_topic():
    event = validate_event(
        {
            "event_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "event_type": "video_quality_changed",
            "occurred_at": "2026-08-13T12:00:00Z",
            "session_id": "019ffafa-5fd5-7363-8154-84618a0104db",
            "payload": {
                "movie_id": "movie-1",
                "from_quality": "720p",
                "to_quality": "1080p",
            },
        }
    )

    assert event["event_type"] == "video_quality_changed"
    assert topic_for(event["event_type"]) == "video-events"


def test_invalid_batch_reports_all_indexes():
    with pytest.raises(BatchValidationError) as caught:
        validate_batch([{}, {"event_type": "unknown"}])

    assert [item["index"] for item in caught.value.errors] == [0, 1]


def test_user_id_is_rejected_in_request_body():
    with pytest.raises(ValueError, match="user_id"):
        validate_event(
            {
                "event_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "event_type": "click",
                "occurred_at": "2026-08-13T12:00:00Z",
                "session_id": "019ffafa-5fd5-7363-8154-84618a0104db",
                "user_id": "forged-user",
                "payload": {"element": "movie_card"},
            }
        )


def test_video_started_is_valid_and_routes_to_video_events():
    event = validate_event(
        {
            "event_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "event_type": "video_started",
            "occurred_at": "2026-08-16T12:00:00Z",
            "session_id": "019ffafa-5fd5-7363-8154-84618a0104db",
            "payload": {"movie_id": "movie-1"},
        }
    )

    assert topic_for(event["event_type"]) == "video-events"
