import logging
from nats.js.client import JetStreamContext
from nats.js.api import StreamConfig, RetentionPolicy, StorageType
from shared.events.user_events import UserCreatedEventV1
from shared.messaging.subjects import STREAM_USER_EVENTS, STREAM_USER_SUBJECT_FILTER, EVENT_USER_CREATED_V1

logger = logging.getLogger("user_service.publisher")


class EventPublisher:
    """Publishes domain events to NATS JetStream."""

    def __init__(self, js: JetStreamContext):
        self.js = js

    async def ensure_stream_exists(self) -> None:
        """Create stream if it doesn't already exist."""
        try:
            await self.js.stream_info(STREAM_USER_EVENTS)
            logger.info(f"JetStream stream '{STREAM_USER_EVENTS}' already exists.")
        except Exception:
            logger.info(f"Creating JetStream stream '{STREAM_USER_EVENTS}' with subjects '{STREAM_USER_SUBJECT_FILTER}'...")
            await self.js.add_stream(
                StreamConfig(
                    name=STREAM_USER_EVENTS,
                    subjects=[STREAM_USER_SUBJECT_FILTER],
                    retention=RetentionPolicy.LIMITS,
                    storage=StorageType.FILE,
                    max_msgs=100000,
                )
            )
            logger.info(f"JetStream stream '{STREAM_USER_EVENTS}' created successfully.")

    async def publish_user_created(self, event: UserCreatedEventV1) -> None:
        """Publish UserCreatedEventV1 to JetStream."""
        payload = event.model_dump_json().encode("utf-8")
        ack = await self.js.publish(
            subject=EVENT_USER_CREATED_V1,
            payload=payload,
            headers={"Nats-Msg-Id": str(event.event_id)},
        )
        logger.info(
            f"Published UserCreated event: event_id={event.event_id}, user_id={event.user_id}, "
            f"stream={ack.stream}, seq={ack.seq}"
        )
