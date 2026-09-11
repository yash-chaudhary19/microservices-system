import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
import nats.errors

from app.core.config import settings
from app.core.middleware import CorrelationIdMiddleware, RateLimitMiddleware
from app.core.exceptions import (
    validation_exception_handler,
    nats_timeout_exception_handler,
    generic_exception_handler,
)
from app.clients.nats_client import GatewayNATSDispatcher
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.notifications import router as notifications_router
from app.api.health import router as health_router
from shared.messaging.nats_client import NATSManager

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("api_gateway")

nats_manager = NATSManager(
    nats_url=settings.NATS_URL,
    user=settings.NATS_USER,
    password=settings.NATS_PASSWORD,
    name=settings.SERVICE_NAME,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting API Gateway...")
    await nats_manager.connect()
    app.state.nats_manager = nats_manager
    app.state.nats_dispatcher = GatewayNATSDispatcher(nats_manager)
    logger.info("API Gateway successfully connected to NATS and initialized.")
    yield

    # Shutdown
    logger.info("Shutting down API Gateway...")
    await nats_manager.close()


app = FastAPI(
    title="Microservices API Gateway",
    description="""
# Production-Grade Microservices API Gateway

Entry point for client interactions in an asynchronous, event-driven microservices ecosystem.

### Architectural Highlights:
- **Zero Direct Service-to-Service HTTP**: Gateway communicates with downstream services solely through NATS Request/Reply.
- **Asynchronous Event Processing**: User actions emit versioned domain events to NATS JetStream consumed independently by worker services.
- **JWT Security**: Protected endpoints enforce cryptographic signature and expiration checks.
- **Observability**: End-to-end correlation ID injection across HTTP headers and NATS messages.
- **Resilience**: Built-in rate limiting, timeout fallbacks, and sanitized error envelopes.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(nats.errors.TimeoutError, nats_timeout_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Middlewares (Order: RateLimit -> CorrelationId -> CORS)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.RATE_LIMIT_REQUESTS_PER_MINUTE)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(notifications_router)
app.include_router(health_router)
