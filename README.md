# Production-Grade Event-Driven Microservices Platform

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![NATS JetStream](https://img.shields.io/badge/NATS-JetStream-27AAE1.svg)](https://nats.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-Pytest%20Passing-brightgreen.svg)]()

A clean, realistic, interview-quality distributed microservices system designed with **FastAPI**, **NATS JetStream**, **PostgreSQL (database-per-service)**, and **Docker Compose**.

---

## 📑 Table of Contents

- [1. Architecture & Design Principles](#1-architecture--design-principles)
- [2. Technology Stack](#2-technology-stack)
- [3. Repository Structure](#3-repository-structure)
- [4. Quick Start (Run Locally)](#4-quick-start-run-locally)
- [5. Automated Test Suite](#5-automated-test-suite)
- [6. API Reference & Swagger Documentation](#6-api-reference--swagger-documentation)
- [7. Step-by-Step API Walkthrough (cURL)](#7-step-by-step-api-walkthrough-curl)
- [8. Distributed Systems & Resilience Features](#8-distributed-systems--resilience-features)
- [9. Additional Documentation](#9-additional-documentation)

---

## 1. Architecture & Design Principles

```mermaid
flowchart TD
    Client["Client / Frontend"] -->|HTTP / REST + JWT| Gateway["API Gateway (:8000)"]
    
    subgraph Private_Network["Private Microservices Network (No External Exposure)"]
        Gateway -->|NATS RPC: service.user.*| UserService["User Service (:8001)"]
        Gateway -->|NATS RPC: service.notification.*| NotifService["Notification Service (:8002)"]
        
        UserService -->|Publish: events.user.created.v1| JetStream[("NATS JetStream (USER_EVENTS Stream)")]
        JetStream -->|Durable Push/Pull (Explicit ACK)| NotifService
        
        UserService --- UserDB[("PostgreSQL: users_db")]
        NotifService --- NotifDB[("PostgreSQL: notifications_db")]
    end
```

### Key Architectural Tenets:
1. **Zero Direct Inter-Service HTTP / WebSockets**: The User Service and Notification Service do **not** invoke each other over REST/HTTP or WebSockets. All communication is routed through **NATS Request/Reply (RPC)** or **NATS JetStream (Events)**.
2. **Database-per-Service**: User Service exclusively owns `users_db`; Notification Service exclusively owns `notifications_db`.
3. **Decoupled Asynchronous Processing**: When a user registers, the User Service emits a `UserCreatedEventV1` to JetStream and immediately completes the user creation. Notification creation happens asynchronously.
4. **Edge-Only Exposure**: Only the API Gateway is exposed to the public network (`8000:8000`). All microservices, databases, and message brokers remain strictly private.
5. **Idempotent Message Processing**: The Notification Service deduplicates incoming events using `event_id` unique constraints, preventing duplicate notifications upon network redelivery.

---

## 2. Technology Stack

- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
- **Data Validation & Settings**: [Pydantic v2](https://docs.pydantic.dev/) & Pydantic-Settings
- **ORM & Database Driver**: [SQLAlchemy 2.x (Async)](https://www.sqlalchemy.org/) + [asyncpg](https://github.com/MagicStack/asyncpg)
- **Database**: [PostgreSQL 16](https://www.postgresql.org/) (Multi-database isolated schemas)
- **Messaging & Streaming**: [NATS Server](https://nats.io/) + [NATS JetStream](https://docs.nats.io/nats-concepts/jetstream)
- **Security & Cryptography**: [PyJWT](https://pyjwt.readthedocs.io/) (HS256) & [Bcrypt](https://pypi.org/project/bcrypt/) (Cost 12)
- **Containerization**: [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)
- **Testing**: [Pytest](https://docs.pytest.org/), [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio), [httpx](https://www.python-httpx.org/)

---

## 3. Repository Structure

```
microservices-system/
├── docker-compose.yml              # Cluster orchestration with health checks
├── .env.example                    # Environment template
├── .env                            # Local development environment configuration
├── .gitignore
├── README.md                       # Main documentation & quickstart
├── architecture.md                 # In-depth system design & Mermaid diagrams
├── DEMO.md                         # Interview demonstration script & resilience test
├── DEPLOYMENT.md                   # Cloud deployment guide (Railway, Render, AWS)
├── pytest.ini                      # Pytest configuration
├── scripts/
│   ├── init-db.sql                 # Postgres multi-database initialization script
│   └── run_tests.sh                # Automated test runner script
├── shared/                         # Shared contracts across services
│   ├── events/
│   │   └── user_events.py          # UserCreatedEventV1 Pydantic model
│   ├── schemas/
│   │   ├── common.py               # ServiceResponse / ServiceError models
│   │   ├── user.py                 # User RPC request & DTO models
│   │   └── notification.py         # Notification RPC request & DTO models
│   └── messaging/
│       ├── subjects.py             # NATS subjects & stream constants
│       └── nats_client.py          # Resilient NATS connection manager
├── gateway/                        # API Gateway (Public Ingress)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── api/                    # /auth, /users, /notifications, /health
│   │   ├── clients/nats_client.py  # NATS RPC dispatcher
│   │   ├── core/                   # Security, Middleware, Exceptions
│   │   ├── schemas/                # HTTP request/response DTOs
│   │   └── main.py                 # FastAPI application
│   └── tests/                      # Gateway unit & API tests
├── user-service/                   # User Microservice
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── api/                    # /health, /ready
│   │   ├── core/                   # Config, Database (users_db), Security
│   │   ├── models/user.py          # SQLAlchemy User model
│   │   ├── repositories/           # Async UserRepository
│   │   ├── services/user_service.py# Business logic & event emission
│   │   ├── messaging/              # NATS RPC & JetStream Publisher
│   │   └── main.py
│   └── tests/                      # User Service unit tests
└── notification-service/           # Notification Microservice
    ├── Dockerfile
    ├── requirements.txt
    ├── app/
    │   ├── api/                    # /health, /ready
    │   ├── core/                   # Config, Database (notifications_db)
    │   ├── models/notification.py  # SQLAlchemy Notification model
    │   ├── repositories/           # Async NotificationRepository
    │   ├── services/               # Idempotent NotificationService
    │   ├── messaging/              # JetStream Durable Consumer & RPC
    │   └── main.py
    └── tests/                      # Notification Service & Consumer tests
```

---

## 4. Quick Start (Run Locally)

### Step 1: Clone and Inspect Environment
```bash
git clone <repo-url>
cd microservices-system
cp .env.example .env
```

### Step 2: Start the System with Docker Compose
```bash
docker compose up --build -d
```

### Step 3: Check Container Status & Health
```bash
docker compose ps
```
All 5 containers (`postgres`, `nats`, `user-service`, `notification-service`, `api-gateway`) should report `healthy`.

---

## 5. Automated Test Suite

To run all unit and integration tests across all microservices:

```bash
chmod +x scripts/run_tests.sh
./scripts/run_tests.sh
```

Or run via pytest directly inside a virtualenv:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r user-service/requirements.txt -r notification-service/requirements.txt -r gateway/requirements.txt
pytest user-service/tests notification-service/tests gateway/tests -v
```

---

## 6. API Reference & Swagger Documentation

Once started, the interactive OpenAPI / Swagger UI is available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Public Endpoints Summary:
| Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | None | Gateway liveness probe |
| `GET` | `/ready` | None | Gateway readiness probe (checks NATS) |
| `POST` | `/auth/register` | None | Registers a new user & returns JWT access token |
| `POST` | `/auth/login` | None | Authenticates credentials & returns JWT access token |
| `POST` | `/users` | `Bearer JWT` | Creates user profile via NATS RPC |
| `GET` | `/users/{user_id}` | `Bearer JWT` | Retrieves user profile by UUID |
| `GET` | `/notifications/{user_id}` | `Bearer JWT` | Retrieves asynchronous notifications for user |

---

## 7. Step-by-Step API Walkthrough (cURL)

### 1. Register a New User
```bash
AUTH_RESP=$(curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alex Mercer",
    "email": "alex.mercer@prototype.io",
    "password": "SecurePassword123!"
  }')

echo $AUTH_RESP | jq .

# Extract JWT token and user ID
export TOKEN=$(echo $AUTH_RESP | jq -r .access_token)
export USER_ID=$(echo $AUTH_RESP | jq -r .user.id)
```

### 2. Verify User Profile (Protected)
```bash
curl -s -X GET http://localhost:8000/users/$USER_ID \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### 3. Fetch Asynchronously Created Welcome Notification
```bash
curl -s -X GET http://localhost:8000/notifications/$USER_ID \
  -H "Authorization: Bearer $TOKEN" | jq .
```

**Output:**
```json
{
  "notifications": [
    {
      "id": "cb1c3f25-8321-43ef-bfa8-01127027c006",
      "user_id": "e4a2d480-1a77-4c22-b586-353d71217e92",
      "type": "WELCOME_EMAIL",
      "title": "Welcome!",
      "message": "Welcome to the platform, Alex Mercer.",
      "status": "created",
      "event_id": "87c4f4a3-1ea8-4cf1-88ae-416dfbfa2da0",
      "created_at": "2026-09-11T09:30:15.123456Z"
    }
  ],
  "total": 1
}
```

---

## 8. Distributed Systems & Resilience Features

### 1. Asynchronous Event Processing & Crash Recovery
If the Notification Service crashes or is temporarily offline:
- User registration continues smoothly without latency or failure.
- `UserCreatedEventV1` messages are safely buffered in NATS JetStream durable file storage.
- When the Notification Service restarts, its **durable consumer** (`notification-service-user-created`) automatically processes all pending events from the exact stream sequence.

*See [DEMO.md](file:///Users/ashm1isingh/.gemini/antigravity-ide/scratch/microservices-system/DEMO.md) for step-by-step instructions on performing this crash test live during an interview.*

### 2. Idempotent Consumer
To prevent duplicate notifications upon network redeliveries:
- The `notifications` table enforces a `UNIQUE` constraint on `event_id`.
- If an event with an existing `event_id` is received, the consumer safely acknowledges the message without creating a duplicate record.

### 3. Rate Limiting & Correlation ID
- In-memory rate limiting protects public Gateway endpoints (default 120 req/min per IP).
- `X-Correlation-ID` headers are injected on all inbound HTTP requests and propagated through all NATS RPC messages and JetStream event headers for end-to-end distributed traceability.

---

## 9. Additional Documentation

- 📐 **[architecture.md](file:///Users/ashm1isingh/.gemini/antigravity-ide/scratch/microservices-system/architecture.md)**: Deep dive into architectural design, sequence diagrams, and scalability.
- 🎯 **[DEMO.md](file:///Users/ashm1isingh/.gemini/antigravity-ide/scratch/microservices-system/DEMO.md)**: Script for presenting the project in a technical interview (including failure simulation).
- 🚀 **[DEPLOYMENT.md](file:///Users/ashm1isingh/.gemini/antigravity-ide/scratch/microservices-system/DEPLOYMENT.md)**: Step-by-step instructions for deploying to Railway, Render, or AWS ECS.
