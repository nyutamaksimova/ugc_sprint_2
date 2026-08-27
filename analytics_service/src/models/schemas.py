from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, ValidationError, model_validator


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    event_type: Literal[
        "click",
        "page_opened",
        "page_closed",
        "video_quality_changed",
        "video_started",
        "video_completed",
        "search_filter_applied",
    ]
    occurred_at: datetime
    session_id: UUID
    payload: dict[str, Any]

    @model_validator(mode="after")
    def validate_payload(self) -> "Event":
        required = {
            "click": {"element"},
            "page_opened": {"page"},
            "page_closed": {"page"},
            "video_quality_changed": {"movie_id", "from_quality", "to_quality"},
            "video_started": {"movie_id"},
            "video_completed": {"movie_id"},
            "search_filter_applied": {"filters"},
        }[self.event_type]
        missing = required - self.payload.keys()
        if missing:
            raise ValueError(f"payload is missing fields: {', '.join(sorted(missing))}")
        if self.event_type == "search_filter_applied" and not isinstance(
            self.payload["filters"], dict
        ):
            raise ValueError("payload.filters must be an object")
        return self


class BatchValidationError(ValueError):
    def __init__(self, errors: list[dict[str, Any]]) -> None:
        self.errors = errors
        super().__init__("Batch contains invalid events")


def validate_event(data: object) -> dict[str, Any]:
    return Event.model_validate(data).model_dump(mode="json")


def validate_batch(data: object) -> list[dict[str, Any]]:
    if not isinstance(data, list) or not data or len(data) > 100:
        raise BatchValidationError(
            [{"index": None, "errors": ["Batch must contain from 1 to 100 events"]}]
        )
    events: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for index, item in enumerate(data):
        try:
            events.append(validate_event(item))
        except ValidationError as error:
            errors.append({"index": index, "errors": error.errors()})
    if errors:
        raise BatchValidationError(errors)
    return events
