# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-24

### Added
- Initial FastAPI backend with health check and items CRUD API
- React + TypeScript + Vite frontend with create/read workflow
- SQLite persistence with SQLAlchemy async
- Pytest backend tests (health + items CRUD) - 6 tests passing
- Vitest frontend tests (component rendering) - 3 tests passing
- Dockerfiles for backend and frontend (non-root users)
- Docker Compose with Keycloak for OIDC authentication
- Keycloak realm export with viewer/operator/admin roles
- .env.example with all configuration options
- Comprehensive README with install/run/test instructions
- MIT LICENSE

### Fixed
- Backend test database initialization (session-scoped fixture)
- Item schema datetime serialization to ISO format strings
- Frontend test setup (vitest expect global, jest-dom dynamic import)
- Frontend TypeScript build (excluded test files from compilation)
