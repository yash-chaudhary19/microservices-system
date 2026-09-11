# Technical Interview Demonstration Guide (DEMO.md)

This walkthrough demonstrates the distributed systems capabilities, security model, and asynchronous event-driven resilience of the system to an evaluator or interviewer.

---

## 1. Prerequisites & Starting the System

Run the entire cluster with Docker Compose:

```bash
docker compose up --build -d
```

Check the health of all containers:
```bash
docker compose ps
```

You should see 5 healthy containers:
- `microservices-postgres` (PostgreSQL with `users_db` & `notifications_db`)
- `microservices-nats` (NATS Server with JetStream enabled)
- `microservices-user-service` (Internal User microservice)
- `microservices-notification-service` (Internal Notification microservice)
- `microservices-api-gateway` (Public entry point at port 8000)

---

## 2. Core Architecture Demonstration Walkthrough

### Step A: Verify Only API Gateway is Exposed Publicly
Demonstrate that the internal microservices are isolated on the internal Docker bridge network:
- Public endpoint works: `curl -s http://localhost:8000/health | jq .`
- Direct access to User Service fails (not exposed on host): `curl -s http://localhost:8001/health || echo "Port 8001 is private"`
- Direct access to Notification Service fails: `curl -s http://localhost:8002/health || echo "Port 8002 is private"`

---

### Step B & C: User Registration & Gateway Authentication
Register a new user through the API Gateway:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sarah Connor",
    "email": "sarah@cyberdyne.io",
    "password": "Password123!"
  }' | jq .
```

**Expected Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "e4a2d480-1a77-4c22-b586-353d71217e92",
    "name": "Sarah Connor",
    "email": "sarah@cyberdyne.io"
  }
}
```

Save the `access_token` and `user_id`:
```bash
export TOKEN="<copied_access_token>"
export USER_ID="<copied_user_id>"
```

---

### Step D & E: Verify Inter-Service NATS RPC and JetStream Event Emission
Inspect the logs of `user-service`:
```bash
docker logs microservices-user-service --tail 15
```

**What the logs demonstrate:**
1. User Service received RPC request via NATS on subject `service.user.create.v1`.
2. Password was hashed securely via `bcrypt`.
3. User record was saved to `users_db`.
4. Domain event `UserCreatedEventV1` was published to JetStream subject `events.user.created.v1` with a unique `Nats-Msg-Id`.

---

### Step F, G & H: Verify Asynchronous JetStream Event Consumption
Inspect the logs of `notification-service`:
```bash
docker logs microservices-notification-service --tail 15
```

**What the logs demonstrate:**
1. Durable JetStream consumer `notification-service-user-created` received `events.user.created.v1`.
2. Notification Service validated event schema.
3. Notification record was inserted into `notifications_db`.
4. Notification Service sent an **explicit ACK** (`AckExplicit`) back to JetStream.

---

### Step I: Query Asynchronously Created Notification via Gateway
Use the authenticated JWT token to query the notifications for this user:

```bash
curl -X GET http://localhost:8000/notifications/$USER_ID \
  -H "Authorization: Bearer $TOKEN" | jq .
```

**Expected Response (200 OK):**
```json
{
  "notifications": [
    {
      "id": "7bf3ad38-f9b1-4ee6-857e-7b700ef58896",
      "user_id": "e4a2d480-1a77-4c22-b586-353d71217e92",
      "type": "WELCOME_EMAIL",
      "title": "Welcome!",
      "message": "Welcome to the platform, Sarah Connor.",
      "status": "created",
      "event_id": "99b9cfec-fcf8-4d69-b5f7-66aa08f51a43",
      "created_at": "2026-09-11T09:30:00Z"
    }
  ],
  "total": 1
}
```

---

## 3. Resilience & Crash Recovery Demonstration (The "Showstopper")

This test proves that messaging is truly durable and asynchronous, and that event delivery does not fail if a downstream service crashes.

### Step 1: Simulate Notification Service Outage
Stop the notification service container completely:
```bash
docker stop microservices-notification-service
```
Verify it is down:
```bash
docker ps --filter "name=microservices-notification-service"
```

### Step 2: Register a New User While Notification Service is Down
```bash
RES=$(curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Connor",
    "email": "john@cyberdyne.io",
    "password": "Password123!"
  }')

echo $RES | jq .
export JOHN_TOKEN=$(echo $RES | jq -r .access_token)
export JOHN_ID=$(echo $RES | jq -r .user.id)
```

**Key Observation**: The user registration succeeds instantly with `201 Created` because the User Service is loosely coupled and does not make synchronous calls to the Notification Service! The `UserCreatedEventV1` is safely stored in NATS JetStream disk persistence.

### Step 3: Verify Notifications are not yet processed
```bash
# Query gateway (Notification service is down, so request will time out or return 504 cleanly)
curl -s -X GET http://localhost:8000/notifications/$JOHN_ID \
  -H "Authorization: Bearer $JOHN_TOKEN" | jq .
```

### Step 4: Restart Notification Service & Observe Event Recovery
Start the notification service back up:
```bash
docker start microservices-notification-service
```

Wait 3 seconds and inspect its startup logs:
```bash
docker logs microservices-notification-service --tail 20
```

**Observation**: Upon reconnection, the durable JetStream consumer automatically pulls the unacknowledged `UserCreatedEventV1` message from the stream, creates the notification, and sends the ACK!

### Step 5: Fetch John Connor's Notification
```bash
curl -s -X GET http://localhost:8000/notifications/$JOHN_ID \
  -H "Authorization: Bearer $JOHN_TOKEN" | jq .
```

**Result**: The notification for John Connor appears successfully! Zero event loss.

---

## 4. Idempotency Demonstration

Inspect the `event_id` field in the notification record. If JetStream redelivers the same event due to network latency:
1. `NotificationService` checks `repo.get_by_event_id(event.event_id)`.
2. Finds the existing record and skips inserting a second row.
3. Automatically ACKs to clear JetStream redeliveries.

---

## 5. Teardown

```bash
docker compose down -v
```
