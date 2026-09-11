import json
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.messaging.jetstream_consumer import JetStreamEventConsumer
from shared.events.user_events import UserCreatedEventV1

pytestmark = pytest.mark.asyncio


def create_mock_msg(data_dict: dict, delivery_count: int = 1):
    msg = AsyncMock()
    msg.data = json.dumps(data_dict).encode("utf-8")
    msg.subject = "events.user.created.v1"
    msg.ack = AsyncMock()
    msg.nak = AsyncMock()
    msg.term = AsyncMock()

    metadata = MagicMock()
    metadata.num_delivered = delivery_count
    metadata.sequence.stream = 100
    msg.metadata = metadata
    return msg


async def test_handle_valid_message_ack():
    mock_js = MagicMock()
    consumer = JetStreamEventConsumer(mock_js)

    event = UserCreatedEventV1(
        user_id=uuid.uuid4(),
        email="test@example.com",
        name="Test User",
    )
    msg = create_mock_msg(event.model_dump(mode="json"), delivery_count=1)

    with patch("app.messaging.jetstream_consumer.async_session_factory") as mock_session_factory, \
         patch("app.messaging.jetstream_consumer.NotificationService") as mock_service_cls:

        mock_service_instance = AsyncMock()
        mock_service_cls.return_value = mock_service_instance
        mock_service_instance.process_user_created_event = AsyncMock()

        await consumer._handle_message(msg)

        assert mock_service_instance.process_user_created_event.call_count == 1
        assert msg.ack.call_count == 1
        assert msg.nak.call_count == 0
        assert msg.term.call_count == 0


async def test_handle_error_message_retry_nak():
    mock_js = MagicMock()
    consumer = JetStreamEventConsumer(mock_js)

    event = UserCreatedEventV1(
        user_id=uuid.uuid4(),
        email="test@example.com",
        name="Test User",
    )
    # 1st attempt out of 3
    msg = create_mock_msg(event.model_dump(mode="json"), delivery_count=1)

    with patch("app.messaging.jetstream_consumer.async_session_factory") as mock_session_factory:
        mock_session_factory.side_effect = RuntimeError("Database connection lost")

        await consumer._handle_message(msg)

        assert msg.ack.call_count == 0
        assert msg.nak.call_count == 1
        assert msg.term.call_count == 0


async def test_handle_poison_message_max_deliveries_term():
    mock_js = MagicMock()
    consumer = JetStreamEventConsumer(mock_js)

    # 3rd attempt (max_deliver = 3)
    msg = create_mock_msg({"invalid": "data"}, delivery_count=3)

    await consumer._handle_message(msg)

    assert msg.ack.call_count == 0
    assert msg.term.call_count == 1


async def test_consumer_start_ensures_stream():
    mock_js = AsyncMock()
    mock_js.stream_info = AsyncMock(side_effect=Exception("Stream not found"))
    mock_js.add_stream = AsyncMock()
    mock_js.subscribe = AsyncMock()

    consumer = JetStreamEventConsumer(mock_js)
    await consumer.start()

    assert mock_js.add_stream.call_count == 1
    assert mock_js.subscribe.call_count == 1

