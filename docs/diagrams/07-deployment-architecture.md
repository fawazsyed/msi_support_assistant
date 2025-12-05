# Deployment Architecture

## Development Environment

```mermaid
graph TB
    subgraph "Developer Machine"
        subgraph "Terminal 1"
            IDP[Mock IDP<br/>uvicorn src.auth.mock_idp:app<br/>--port 9400]
        end

        subgraph "Terminal 2"
            TICK[Ticketing MCP<br/>python -m src.mcp.ticketing.server<br/>Port 9000]
        end

        subgraph "Terminal 3"
            ORG[Organizations MCP<br/>python -m src.mcp.organizations.server<br/>Port 9001]
        end

        subgraph "Terminal 4"
            API[FastAPI Server<br/>uvicorn src.api.server:app<br/>--reload --port 8000]
        end

        subgraph "Terminal 5"
            UI[Angular Dev Server<br/>ng serve<br/>Port 4200]
        end

        ENV[.env File<br/>OPENAI_API_KEY]
        VENV[.venv/<br/>Python Dependencies]
        NODE[node_modules/<br/>NPM Dependencies]
    end

    ENV --> API
    VENV --> IDP
    VENV --> TICK
    VENV --> ORG
    VENV --> API
    NODE --> UI

    style IDP fill:#ec4899
    style TICK fill:#f59e0b
    style ORG fill:#f59e0b
    style API fill:#8b5cf6
    style UI fill:#6366f1
```

## Production Architecture (Future)

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[NGINX/Traefik<br/>SSL Termination]
    end

    subgraph "Frontend Tier"
        UI1[Angular UI<br/>Static Files]
        UI2[Angular UI<br/>Static Files]
    end

    subgraph "API Tier"
        API1[FastAPI<br/>Gunicorn Worker 1]
        API2[FastAPI<br/>Gunicorn Worker 2]
        API3[FastAPI<br/>Gunicorn Worker 3]
    end

    subgraph "Auth Tier"
        AUTH[Production IDP<br/>Okta/Auth0/Keycloak]
    end

    subgraph "MCP Tier"
        MCP1[MCP Servers<br/>Container 1]
        MCP2[MCP Servers<br/>Container 2]
    end

    subgraph "Data Tier"
        PGDB[(PostgreSQL<br/>Primary)]
        PGREP[(PostgreSQL<br/>Replica)]
        VECDB[(Vector DB<br/>Weaviate/Pinecone)]
        CACHE[(Redis Cache)]
    end

    subgraph "External Services"
        OPENAI[OpenAI API]
        MONITOR[Monitoring<br/>DataDog/New Relic]
    end

    LB --> UI1
    LB --> UI2
    LB --> API1
    LB --> API2
    LB --> API3

    API1 --> AUTH
    API2 --> AUTH
    API3 --> AUTH

    API1 --> MCP1
    API2 --> MCP1
    API3 --> MCP2

    API1 --> OPENAI
    API2 --> OPENAI
    API3 --> OPENAI

    API1 --> CACHE
    API2 --> CACHE
    API3 --> CACHE

    MCP1 --> PGDB
    MCP2 --> PGDB
    PGDB --> PGREP

    API1 --> VECDB
    API2 --> VECDB
    API3 --> VECDB

    API1 --> MONITOR
    API2 --> MONITOR
    API3 --> MONITOR

    style LB fill:#6366f1
    style AUTH fill:#ec4899
    style OPENAI fill:#10b981
```

## Container Architecture (Docker)

```mermaid
graph TB
    subgraph "Docker Compose Stack"
        subgraph "Frontend Container"
            NGINX[NGINX<br/>Serves Angular build]
        end

        subgraph "API Container"
            API[FastAPI + Gunicorn<br/>3 workers]
        end

        subgraph "Auth Container"
            IDP[Mock IDP<br/>or Keycloak]
        end

        subgraph "MCP Container 1"
            TICK[Ticketing MCP]
        end

        subgraph "MCP Container 2"
            ORG[Organizations MCP]
        end

        subgraph "Database Container"
            POSTGRES[(PostgreSQL)]
        end

        subgraph "Vector DB Container"
            CHROMA[(Chroma Server)]
        end

        VOLUMES[Docker Volumes<br/>- postgres_data<br/>- chroma_data<br/>- app_logs]
    end

    NGINX --> API
    API --> IDP
    API --> TICK
    API --> ORG
    TICK --> POSTGRES
    ORG --> POSTGRES
    API --> CHROMA
    POSTGRES --> VOLUMES
    CHROMA --> VOLUMES
    API --> VOLUMES
```

### Docker Compose File Structure

```yaml
version: '3.8'

services:
  # Angular UI (production build)
  ui:
    build: ./ai-assistant-ui
    ports:
      - "80:80"
    depends_on:
      - api

  # FastAPI Server
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=postgresql://user:pass@db:5432/msi
      - CHROMA_URL=http://chroma:8000
    depends_on:
      - db
      - chroma
      - mock-idp
      - mcp-ticketing
      - mcp-organizations

  # Mock IDP (or real auth provider)
  mock-idp:
    build:
      context: .
      dockerfile: Dockerfile.idp
    ports:
      - "9400:9400"

  # MCP Servers
  mcp-ticketing:
    build:
      context: .
      dockerfile: Dockerfile.mcp
      args:
        MCP_SERVER: ticketing
    ports:
      - "9000:9000"
    depends_on:
      - db
      - mock-idp

  mcp-organizations:
    build:
      context: .
      dockerfile: Dockerfile.mcp
      args:
        MCP_SERVER: organizations
    ports:
      - "9001:9001"
    depends_on:
      - db
      - mock-idp

  # PostgreSQL Database
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: msi_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: msi_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Chroma Vector Database
  chroma:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma

volumes:
  postgres_data:
  chroma_data:
```

## Cloud Deployment Options

### Option 1: Heroku

```mermaid
graph LR
    subgraph "Heroku Platform"
        WEB[Web Dyno<br/>FastAPI + Angular]
        WORKER[Worker Dyno<br/>Background Tasks]
        POSTGRES[(Heroku Postgres)]
        REDIS[(Heroku Redis)]
    end

    subgraph "Add-ons"
        PAPER[Papertrail<br/>Logging]
        NEWRELIC[New Relic<br/>Monitoring]
    end

    WEB --> POSTGRES
    WEB --> REDIS
    WORKER --> POSTGRES
    WEB --> PAPER
    WEB --> NEWRELIC

    style WEB fill:#8b5cf6
```

**Procfile:**
```
web: uvicorn src.api.server:app --host 0.0.0.0 --port $PORT
```

### Option 2: AWS

```mermaid
graph TB
    subgraph "AWS Cloud"
        subgraph "Compute"
            ECS[ECS Fargate<br/>Containers]
            LAMBDA[Lambda Functions<br/>Serverless]
        end

        subgraph "Data"
            RDS[(RDS PostgreSQL)]
            S3[(S3 Buckets<br/>Static Files)]
        end

        subgraph "Networking"
            ALB[Application Load Balancer]
            CF[CloudFront CDN]
            R53[Route 53 DNS]
        end

        subgraph "Security"
            COGNITO[Cognito<br/>Authentication]
            SM[Secrets Manager]
        end

        subgraph "Monitoring"
            CW[CloudWatch Logs]
            XRAY[X-Ray Tracing]
        end
    end

    R53 --> CF
    CF --> S3
    CF --> ALB
    ALB --> ECS
    ECS --> RDS
    ECS --> SM
    ECS --> COGNITO
    ECS --> CW
    ECS --> XRAY

    style ECS fill:#8b5cf6
    style RDS fill:#6366f1
```

### Option 3: Google Cloud Platform

```mermaid
graph TB
    subgraph "GCP"
        subgraph "Compute"
            RUN[Cloud Run<br/>Containers]
        end

        subgraph "Data"
            CLOUD_SQL[(Cloud SQL<br/>PostgreSQL)]
            GCS[(Cloud Storage)]
        end

        subgraph "AI/ML"
            VERTEX[Vertex AI<br/>Embeddings]
        end

        subgraph "Security"
            IAP[Identity-Aware Proxy]
            SM[Secret Manager]
        end

        subgraph "Monitoring"
            LOGGING[Cloud Logging]
            TRACE[Cloud Trace]
        end
    end

    RUN --> CLOUD_SQL
    RUN --> GCS
    RUN --> VERTEX
    RUN --> SM
    RUN --> LOGGING
    RUN --> TRACE
    IAP --> RUN

    style RUN fill:#8b5cf6
```

## Scaling Considerations

### Horizontal Scaling

```mermaid
graph TB
    subgraph "Auto-Scaling Group"
        API1[API Instance 1]
        API2[API Instance 2]
        API3[API Instance 3]
        APIX[API Instance N]
    end

    LB[Load Balancer] --> API1
    LB --> API2
    LB --> API3
    LB --> APIX

    API1 --> SHARED[Shared Services]
    API2 --> SHARED
    API3 --> SHARED
    APIX --> SHARED

    subgraph "Shared Services"
        DB[(Database<br/>Connection Pool)]
        CACHE[(Redis Cache<br/>Shared State)]
        QUEUE[(Task Queue<br/>Background Jobs)]
    end

    style LB fill:#6366f1
    style DB fill:#8b5cf6
```

### Performance Optimization

| Layer | Strategy | Implementation |
|-------|----------|----------------|
| **API** | Response caching | Redis cache for repeated queries |
| **LLM** | Prompt caching | OpenAI prompt caching (future) |
| **RAG** | Vector indexing | Pre-compute embeddings |
| **Database** | Connection pooling | SQLAlchemy pool |
| **Static Assets** | CDN | CloudFront/Cloudflare |

## Security Hardening

### Production Checklist

```mermaid
graph TD
    START[Deploy to Production] --> CHECK1{HTTPS Enabled?}
    CHECK1 -->|No| FIX1[Enable SSL/TLS]
    CHECK1 -->|Yes| CHECK2{Auth Provider?}

    CHECK2 -->|Mock IDP| FIX2[Replace with<br/>Real Provider]
    CHECK2 -->|Production| CHECK3{Secrets Managed?}

    CHECK3 -->|No| FIX3[Use Secret Manager]
    CHECK3 -->|Yes| CHECK4{Rate Limiting?}

    CHECK4 -->|No| FIX4[Add Rate Limits]
    CHECK4 -->|Yes| CHECK5{Monitoring?}

    CHECK5 -->|No| FIX5[Add Logging/Alerts]
    CHECK5 -->|Yes| CHECK6{Backups?}

    CHECK6 -->|No| FIX6[Configure Backups]
    CHECK6 -->|Yes| READY[Ready for Production]

    FIX1 --> CHECK2
    FIX2 --> CHECK3
    FIX3 --> CHECK4
    FIX4 --> CHECK5
    FIX5 --> CHECK6
    FIX6 --> READY

    style READY fill:#10b981
    style FIX1 fill:#f59e0b
    style FIX2 fill:#f59e0b
    style FIX3 fill:#f59e0b
    style FIX4 fill:#f59e0b
    style FIX5 fill:#f59e0b
    style FIX6 fill:#f59e0b
```

### Environment Variables

**Development (`.env`):**
```bash
OPENAI_API_KEY=sk-...
DATABASE_URL=sqlite:///data/databases/
ENVIRONMENT=development
DEBUG=true
```

**Production:**
```bash
OPENAI_API_KEY=<from-secret-manager>
DATABASE_URL=postgresql://prod-db:5432/msi
ENVIRONMENT=production
DEBUG=false
ALLOWED_ORIGINS=https://msi-assistant.com
RATE_LIMIT_REQUESTS=10
```

## Monitoring & Observability

### Logging Architecture

```mermaid
graph LR
    subgraph "Application Logs"
        API[FastAPI Logs]
        MCP[MCP Server Logs]
        IDP[IDP Logs]
    end

    subgraph "Log Aggregation"
        COLLECT[Log Collector<br/>Fluentd/Filebeat]
    end

    subgraph "Storage & Analysis"
        ELASTIC[Elasticsearch]
        KIBANA[Kibana Dashboard]
    end

    API --> COLLECT
    MCP --> COLLECT
    IDP --> COLLECT
    COLLECT --> ELASTIC
    ELASTIC --> KIBANA

    style KIBANA fill:#10b981
```

### Metrics to Monitor

| Metric | Purpose | Alert Threshold |
|--------|---------|-----------------|
| **Response Time** | User experience | > 3 seconds |
| **Error Rate** | System health | > 5% |
| **OpenAI API Calls** | Cost control | > budget |
| **Token Usage** | Cost control | > budget |
| **Database Connections** | Resource limits | > 80% pool |
| **Memory Usage** | Resource limits | > 85% |
| **CPU Usage** | Resource limits | > 80% |

## Backup & Recovery

### Backup Strategy

```mermaid
graph TB
    subgraph "Data Sources"
        PGDB[(PostgreSQL)]
        VECDB[(Vector Store)]
        DOCS[/Documents/]
    end

    subgraph "Backup Process"
        DAILY[Daily Backups<br/>3:00 AM UTC]
        WEEKLY[Weekly Full<br/>Sunday 2:00 AM]
    end

    subgraph "Storage"
        S3[(S3 Backup Bucket<br/>Versioned<br/>30-day retention)]
    end

    PGDB --> DAILY
    VECDB --> DAILY
    DOCS --> WEEKLY

    DAILY --> S3
    WEEKLY --> S3

    S3 --> RESTORE[Restore Process<br/>< 1 hour RTO]

    style S3 fill:#6366f1
    style RESTORE fill:#10b981
```

### Disaster Recovery

**Recovery Time Objective (RTO):** < 1 hour
**Recovery Point Objective (RPO):** < 24 hours

**DR Runbook:**
1. Provision new infrastructure
2. Restore database from S3 backup
3. Restore vector store from backup
4. Deploy latest application code
5. Update DNS to new endpoints
6. Verify functionality
