# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

skeleton-fastapi-react

## Roadmap

### skeleton-fastapi-react — Runnable FastAPI + React skeleton with one end-to-end workflow

Status: done

Acceptance:
- FastAPI backend starts and serves /health endpoint
- React frontend builds and loads
- One complete create/read workflow works across HTTP boundary
- pytest backend tests pass
- npm frontend build/test pass
- Dockerfiles build for both services

Implementation: `backend/app/main.py`, `backend/requirements.txt`, `backend/tests/test_health.py`, `frontend/package.json`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/vite.config.ts`, `Dockerfile.backend`, `Dockerfile.frontend`, `compose.yaml`

Tests: `backend/tests/test_health.py`, `frontend/src/App.test.tsx`

### audit-core-domain — Core audit domain engine (coverage ledger, findings, verification)

Status: planned

Acceptance:
- Coverage ledger CRUD with persistence
- Findings schema with validation
- Independent verification phase
- Machine-readable JSON output

### oidc-auth-keycloak — OIDC authentication with Keycloak (authorization code + PKCE)

Status: planned

Acceptance:
- Login/callback flow works
- HttpOnly cookies + CSRF protection
- Role-based authorization on all data endpoints
- Logout works

### llm-adapters — LLM provider adapters (OpenAI-compatible, Anthropic, Gemini, Ollama)

Status: planned

Acceptance:
- Configurable provider/model/endpoint
- Bounded timeouts and redacted errors
- Opt-in advisory explanations

### audit-workflows — Three complete audit workflows (quick/standard/deep profiles)

Status: planned

Acceptance:
- Quick profile: single hunter wave
- Standard profile: two hunter waves + critic
- Deep profile: full verification phase
- Deterministic offline core

