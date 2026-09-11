import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import init_db
from app.messaging.event_publisher import EventPublisher
from app.messaging.nats_handler import UserNATSHandler
from app.api.health import router as health_router
from shared.messaging.nats_client import NATSManager

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("user_service")

nats_manager = NATSManager(
    nats_url=settings.NATS_URL,
    user=settings.NATS_USER,
    password=settings.NATS_PASSWORD,
    name=settings.SERVICE_NAME,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting User Service...")
    await init_db()

    # Connect to NATS
    nc = await nats_manager.connect()
    event_publisher = EventPublisher(nats_manager.js)
    await event_publisher.ensure_stream_exists()

    # Start NATS RPC Handler
    nats_handler = UserNATSHandler(nc, event_publisher)
    await nats_handler.register_subscriptions()

    logger.info("User Service is fully initialized and listening.")
    yield

    # Shutdown
    logger.info("Shutting down User Service...")
    await nats_manager.close()


app = FastAPI(
    title="User Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health_router)
