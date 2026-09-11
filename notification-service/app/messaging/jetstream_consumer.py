import asyncio
import json
import logging
from nats.js.client import JetStreamContext
from nats.js.api import ConsumerConfig, DeliverPolicy, AckPolicy, StreamConfig, RetentionPolicy, StorageType
from app.core.config import settings
from app.core.database import async_session_factory
from app.services.notification_service import NotificationService
from shared.events.user_events import UserCreatedEventV1
from shared.messaging.subjects import (
    STREAM_USER_EVENTS,
    STREAM_USER_SUBJECT_FILTER,
    CONSUMER_NOTIFICATION_USER_EVENTS,
    EVENT_USER_CREATED_V1,
)

logger = logging.getLogger("notification_service.jetstream")


class JetStreamEventConsumer:
    """Durable NATS JetStream consumer for UserCreated domain events."""

    def __init__(self, js: JetStreamContext):
        self.js = js
        self._running = False
        self._task: asyncio.Task | None = None
        self._sub = None

    async def _ensure_stream_exists(self) -> None:
        """Create stream if it doesn't already exist on NATS broker."""
        try:
            await self.js.stream_info(STREAM_USER_EVENTS)
            logger.info(f"JetStream stream '{STREAM_USER_EVENTS}' already exists.")
        except Exception:
            logger.info(f"Stream '{STREAM_USER_EVENTS}' not found. Creating with subjects '{STREAM_USER_SUBJECT_FILTER}'...")
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

    async def start(self) -> None:
        """Initialize durable consumer and start consumption loop."""
        self._running = True
        logger.info(f"Setting up JetStream durable consumer '{CONSUMER_NOTIFICATION_USER_EVENTS}' on stream '{STREAM_USER_EVENTS}'...")

        # 1. Ensure stream exists so consumer doesn't depend on publisher startup order
        await self._ensure_stream_exists()

        # 2. Configure durable consumer
        consumer_config = ConsumerConfig(
            durable_name=CONSUMER_NOTIFICATION_USER_EVENTS,
            deliver_policy=DeliverPolicy.ALL,
            ack_policy=AckPolicy.EXPLICIT,
            ack_wait=settings.CONSUMER_ACK_WAIT_SECONDS,
            max_deliver=settings.CONSUMER_MAX_DELIVER,
            filter_subject=EVENT_USER_CREATED_V1,
        )

        try:
            # Subscribe to JetStream stream with durable consumer explicitly bound to stream
            self._sub = await self.js.subscribe(
                subject=EVENT_USER_CREATED_V1,
                durable=CONSUMER_NOTIFICATION_USER_EVENTS,
                stream=STREAM_USER_EVENTS,
                config=consumer_config,
                cb=self._handle_message,
                manual_ack=True,
            )
            logger.info(
                f"Successfully registered JetStream consumer '{CONSUMER_NOTIFICATION_USER_EVENTS}' "
                f"listening on subject '{EVENT_USER_CREATED_V1}' on stream '{STREAM_USER_EVENTS}'."
            )
        except Exception as e:
            logger.error(f"Failed to subscribe to JetStream stream: {e}", exc_info=True)
            raise

    async def _handle_message(self, msg) -> None:
        """Handle incoming JetStream message with explicit ACK / retry / error handling."""
        delivery_count = msg.metadata.num_delivered if hasattr(msg, "metadata") and msg.metadata else 1
        stream_seq = msg.metadata.sequence.stream if hasattr(msg, "metadata") and msg.metadata else "unknown"

        logger.info(
            f"Received JetStream message [stream_seq={stream_seq}, delivery={delivery_count}/"
            f"{settings.CONSUMER_MAX_DELIVER}]: subject={msg.subject}"
        )

        try:
            data = json.loads(msg.data.decode("utf-8"))
            event = UserCreatedEventV1.model_validate(data)

            # Process event in dedicated database session
            async with async_session_factory() as session:
                service = NotificationService(session)
                await service.process_user_created_event(event)

            # Explicit acknowledgement to JetStream
            await msg.ack()
            logger.info(f"Message [stream_seq={stream_seq}] acknowledged successfully.")

        except Exception as e:
            logger.error(
                f"Error processing JetStream message [stream_seq={stream_seq}, delivery={delivery_count}]: {e}",
                exc_info=True,
            )
            if delivery_count >= settings.CONSUMER_MAX_DELIVER:
                logger.critical(
                    f"Message [stream_seq={stream_seq}] reached max delivery attempts ({settings.CONSUMER_MAX_DELIVER}). "
                    f"Terminating message to prevent infinite retry loop."
                )
                # Terminate message or route to DLQ
                try:
                    await msg.term()
                except Exception as term_err:
                    logger.error(f"Failed to term message: {term_err}")
            else:
                logger.warning(f"Negative-acknowledging message [stream_seq={stream_seq}] for retry.")
                try:
                    await msg.nak(delay=2)
                except Exception as nak_err:
                    logger.error(f"Failed to nak message: {nak_err}")

    async def stop(self) -> None:
        """Gracefully unsubscribe and stop consumer."""
        self._running = False
        if self._sub:
            logger.info(f"Unsubscribing JetStream consumer '{CONSUMER_NOTIFICATION_USER_EVENTS}'...")
            try:
                await self._sub.unsubscribe()
            except Exception as e:
                logger.warning(f"Error unsubscribing consumer: {e}")
