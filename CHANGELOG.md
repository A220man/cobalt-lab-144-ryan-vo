# Changelog

## 1.4.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.3.0 — work-in-progress checkpoint

### Added
- `preserved_uses` field to Finding model for tracking legitimate uses that must remain functional after remediation (addresses issue #88 from reference product)
- `preserved_uses` support in Finding schemas (create, update, read, export)
- 3 new tests for preserved_uses CRUD operations

### Fixed
- Test database fixture now drops and recreates tables at session start to pick up schema changes

### Tests
- All 21 backend tests passing (15 audit + 3 health + 3 items)
- All 3 frontend tests passing

---

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 — 2026-11-05

### Added
- Comprehensive audit API test suite (12 tests): coverage unit CRUD, finding CRUD, export endpoints
- Filtering support for coverage units (by attack_class, status) and findings (by attack_class, status, severity)

### Fixed
- datetime.utcnow() deprecation warnings in audit export endpoints (use timezone-aware datetime.now(timezone.utc))
- Backend test database now properly registers audit models

### Tests
- All 18 backend tests passing (6 existing + 12 new audit tests)
- All 3 frontend tests passing


## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0/),
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
- Core audit domain engine (coverage ledger, findings, verification)
  - CoverageUnit and Finding models with status enums
  - Pydantic schemas for validation and JSON export
  - REST API endpoints for coverage units and findings CRUD
  - Machine-readable JSON export endpoints (coverage-ledger, findings)
  - Database integration with automatic migrations

### Fixed
- Backend test database initialization (session-scoped fixture)
- Item schema datetime serialization to ISO format strings
- Frontend test setup (vitest expect global, jest-dom dynamic import)
- Frontend TypeScript build (excluded test files from compilation)

