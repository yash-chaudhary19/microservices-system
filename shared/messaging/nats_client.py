import json
import logging
import asyncio
from typing import Any
import nats
from nats.aio.client import Client as NATSClient
from nats.js.client import JetStreamContext
from pydantic import BaseModel

logger = logging.getLogger("shared.messaging")


class NATSManager:
    """Manages resilient NATS connection and JetStream context."""

    def __init__(
        self,
        nats_url: str,
        user: str | None = None,
        password: str | None = None,
        name: str = "microservice",
    ):
        self.nats_url = nats_url
        self.user = user
        self.password = password
        self.name = name
        self.nc: NATSClient | None = None
        self.js: JetStreamContext | None = None

    async def connect(self) -> NATSClient:
        """Connect to NATS server with authentication and reconnect handlers."""
        options: dict[str, Any] = {
            "servers": [self.nats_url],
            "name": self.name,
            "max_reconnect_attempts": -1,  # Reconnect indefinitely
            "reconnect_time_wait": 2,
            "disconnected_cb": self._on_disconnected,
            "reconnected_cb": self._on_reconnected,
            "error_cb": self._on_error,
            "closed_cb": self._on_closed,
        }

        if self.user and self.password:
            options["user"] = self.user
            options["password"] = self.password

        logger.info(f"Connecting to NATS at {self.nats_url} as {self.name}...")
        self.nc = await nats.connect(**options)
        self.js = self.nc.jetstream()
        logger.info(f"Successfully connected to NATS & JetStream initialized as {self.name}.")
        return self.nc

    async def close(self) -> None:
        """Gracefully close NATS connection."""
        if self.nc and not self.nc.is_closed:
            logger.info(f"Closing NATS connection for {self.name}...")
            await self.nc.drain()
            await self.nc.close()
            logger.info(f"NATS connection closed for {self.name}.")

    async def request(
        self,
        subject: str,
        payload: dict[str, Any] | BaseModel if "BaseModel" in globals() else Any,
        timeout: float = 5.0,
    ) -> dict[str, Any]:
        """Send a Request/Reply message and return the parsed JSON response."""
        if not self.nc or self.nc.is_closed:
            raise RuntimeError("NATS client is not connected.")

        if hasattr(payload, "model_dump_json"):
            data = payload.model_dump_json().encode("utf-8")
        elif isinstance(payload, dict):
            data = json.dumps(payload).encode("utf-8")
        elif isinstance(payload, bytes):
            data = payload
        else:
            data = str(payload).encode("utf-8")

        response_msg = await self.nc.request(subject, data, timeout=timeout)
        return json.loads(response_msg.data.decode("utf-8"))

    async def _on_disconnected(self) -> None:
        logger.warning(f"NATS disconnected for {self.name}.")

    async def _on_reconnected(self) -> None:
        logger.info(f"NATS reconnected for {self.name}.")

    async def _on_error(self, e: Exception) -> None:
        logger.error(f"NATS error in {self.name}: {e}")

    async def _on_closed(self) -> None:
        logger.info(f"NATS connection closed for {self.name}.")
