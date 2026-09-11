# Cloud Production Deployment Guide (DEPLOYMENT.md)

This guide provides step-by-step instructions for deploying the microservices platform to cloud environments while preserving strict **private networking** for internal services (User Service, Notification Service, PostgreSQL, and NATS) and exposing **only the API Gateway** publicly.

---

## 1. Cloud Architecture Principles

In a production cloud deployment:
1. **Public Ingress**: Only the **API Gateway** has a public URL/load balancer attached (e.g. `https://api.yourdomain.com`).
2. **Private Network (VPC / Service Mesh)**: User Service, Notification Service, NATS, and PostgreSQL run in private subnets with internal DNS resolution.
3. **Secrets Management**: All sensitive values (DB credentials, JWT secrets, NATS passwords) are injected as environment variables from cloud secret managers.

---

## 2. Option A: Deployment via Railway (Recommended - Simplest & Fastest)

Railway supports multi-service projects with automatic private networking, managed PostgreSQL, and zero public exposure for internal containers.

### Step 1: Create a Railway Project
1. Go to [railway.app](https://railway.app/) and sign in with GitHub.
2. Click **New Project** -> **Provision PostgreSQL**.
3. Create the two isolated databases in PostgreSQL query editor:
   ```sql
   CREATE DATABASE users_db;
   CREATE DATABASE notifications_db;
   ```
4. Note the connection URL: `postgresql+asyncpg://postgres:${PGPASSWORD}@${PGHOST}:${PGPORT}`

### Step 2: Deploy NATS with JetStream
1. In the same project canvas, click **New** -> **Docker Image**.
2. Enter: `nats:2.10-alpine`.
3. Set the startup arguments / command:
   ```bash
   -js -m 8222 --user app_user --pass ${NATS_PASSWORD}
   ```
4. Add Environment Variable:
   - `NATS_PASSWORD`: `<generate-a-strong-random-password>`
5. Enable **Private Networking** (do not generate a public domain for NATS).
   Internal address will be `nats.railway.internal:4222`.

### Step 3: Deploy User Service
1. Click **New** -> **GitHub Repo** (select this repository).
2. Settings:
   - **Root Directory**: `.`
   - **Dockerfile Path**: `user-service/Dockerfile`
3. Variables:
   - `DATABASE_URL`: `postgresql+asyncpg://postgres:${PGPASSWORD}@postgres.railway.internal:5432/users_db`
   - `NATS_URL`: `nats://nats.railway.internal:4222`
   - `NATS_USER`: `app_user`
   - `NATS_PASSWORD`: `${{NATS.NATS_PASSWORD}}`
   - `LOG_LEVEL`: `INFO`
4. Do NOT generate a public domain (keep private).

### Step 4: Deploy Notification Service
1. Click **New** -> **GitHub Repo** (select this repository).
2. Settings:
   - **Root Directory**: `.`
   - **Dockerfile Path**: `notification-service/Dockerfile`
3. Variables:
   - `DATABASE_URL`: `postgresql+asyncpg://postgres:${PGPASSWORD}@postgres.railway.internal:5432/notifications_db`
   - `NATS_URL`: `nats://nats.railway.internal:4222`
   - `NATS_USER`: `app_user`
   - `NATS_PASSWORD`: `${{NATS.NATS_PASSWORD}}`
   - `CONSUMER_ACK_WAIT_SECONDS`: `10`
   - `CONSUMER_MAX_DELIVER`: `3`
   - `LOG_LEVEL`: `INFO`
4. Do NOT generate a public domain (keep private).

### Step 5: Deploy API Gateway (Public Service)
1. Click **New** -> **GitHub Repo** (select this repository).
2. Settings:
   - **Root Directory**: `.`
   - **Dockerfile Path**: `gateway/Dockerfile`
3. Variables:
   - `PORT`: `8000`
   - `NATS_URL`: `nats://nats.railway.internal:4222`
   - `NATS_USER`: `app_user`
   - `NATS_PASSWORD`: `${{NATS.NATS_PASSWORD}}`
   - `JWT_SECRET`: `<generate-strong-64-character-random-key>`
   - `JWT_ALGORITHM`: `HS256`
   - `JWT_EXPIRATION_MINUTES`: `60`
   - `RATE_LIMIT_REQUESTS_PER_MINUTE`: `120`
4. Click **Settings** -> **Generate Domain** (e.g. `https://api-gateway-production.up.railway.app`).

---

## 3. Option B: Deployment via Render

Render provides **Private Services** (no public IP) and **Web Services** (public HTTPS ingress).

1. **PostgreSQL**: Create a Managed PostgreSQL instance. Create `users_db` and `notifications_db`.
2. **NATS Server**: Create a **Private Service** using `nats:2.10-alpine` with `-js` flag.
3. **User Service**: Create a **Private Service** building `user-service/Dockerfile`.
4. **Notification Service**: Create a **Private Service** building `notification-service/Dockerfile`.
5. **API Gateway**: Create a **Web Service** building `gateway/Dockerfile` and map port `8000`.

---

## 4. Option C: AWS ECS Fargate with CloudFormation / Terraform

```mermaid
graph TD
    ALB["AWS Application Load Balancer (Public Ingress)"] -->|HTTPS :443 -> :8000| GatewayECS["API Gateway (ECS Fargate Task)"]
    
    subgraph VPC_Private_Subnet["VPC Private Subnet (No Internet Inbound)"]
        GatewayECS -->|NATS Protocol :4222| NATSCluster["NATS Server (ECS Fargate)"]
        UserECS["User Service (ECS Fargate)"] --> NATSCluster
        NotifECS["Notification Service (ECS Fargate)"] --> NATSCluster
        
        UserECS -->|Port 5432| RDS_Users[("Amazon RDS: users_db")]
        NotifECS -->|Port 5432| RDS_Notifs[("Amazon RDS: notifications_db")]
    end
```

---

## 5. Environment Variables Reference

| Variable | Description | Required By | Sample Value |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | Async PostgreSQL connection string | User & Notification Services | `postgresql+asyncpg://user:pass@host:5432/dbname` |
| `NATS_URL` | Connection URL to NATS broker | Gateway, User, Notification | `nats://nats-host:4222` |
| `NATS_USER` | NATS client username | All services | `app_user` |
| `NATS_PASSWORD` | NATS client password | All services | `strong_secret_nats_password` |
| `JWT_SECRET` | 256-bit secret key for signing JWTs | Gateway | `64_char_secure_random_string` |
| `JWT_ALGORITHM` | JWT signing algorithm | Gateway | `HS256` |
| `JWT_EXPIRATION_MINUTES` | Token lifetime | Gateway | `60` |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | Max requests/min per IP | Gateway | `120` |

---

## 6. Live Verification After Deployment

Once deployed, verify your public gateway domain:

```bash
export PROD_URL="https://your-gateway-url.com"

# 1. Health check
curl -s $PROD_URL/health | jq .

# 2. Register
AUTH_DATA=$(curl -s -X POST $PROD_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cloud Admin",
    "email": "admin@cloudtest.io",
    "password": "ProductionPassword123!"
  }')

echo $AUTH_DATA | jq .
TOKEN=$(echo $AUTH_DATA | jq -r .access_token)
USER_ID=$(echo $AUTH_DATA | jq -r .user.id)

# 3. Retrieve notifications created asynchronously
sleep 2
curl -s -X GET $PROD_URL/notifications/$USER_ID \
  -H "Authorization: Bearer $TOKEN" | jq .
```
