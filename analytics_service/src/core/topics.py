TOPICS = {
    "click": "click-events",
    "page_opened": "page-view-events",
    "page_closed": "page-view-events",
    "video_quality_changed": "video-events",
    "video_started": "video-events",
    "video_completed": "video-events",
    "search_filter_applied": "search-events",
}


def topic_for(event_type: str) -> str:
    return TOPICS[event_type]
