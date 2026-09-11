import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import init_db
from app.messaging.jetstream_consumer import JetStreamEventConsumer
from app.messaging.nats_handler import NotificationNATSHandler
from app.api.health import router as health_router
from shared.messaging.nats_client import NATSManager

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("notification_service")

nats_manager = NATSManager(
    nats_url=settings.NATS_URL,
    user=settings.NATS_USER,
    password=settings.NATS_PASSWORD,
    name=settings.SERVICE_NAME,
)

consumer: JetStreamEventConsumer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer
    # Startup
    logger.info("Starting Notification Service...")
    await init_db()

    # Connect to NATS & JetStream
    nc = await nats_manager.connect()

    # Start RPC Handler
    rpc_handler = NotificationNATSHandler(nc)
    await rpc_handler.register_subscriptions()

    # Start JetStream Durable Consumer
    consumer = JetStreamEventConsumer(nats_manager.js)
    await consumer.start()

    logger.info("Notification Service is fully initialized and consuming events.")
    yield

    # Shutdown
    logger.info("Shutting down Notification Service...")
    if consumer:
        await consumer.stop()
    await nats_manager.close()


app = FastAPI(
    title="Notification Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health_router)
