# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

continue-implementation

## Roadmap

### continue-implementation — Continue implementation and resolve known failures

Status: done

Acceptance:
- Run checks, fix failures, and implement the next planned feature

Implementation: `backend/tests/test_audit.py`, `backend/app/api/v1/audit.py`

Tests: `backend/tests/test_audit.py::test_create_coverage_unit`, `backend/tests/test_audit.py::test_list_coverage_units`, `backend/tests/test_audit.py::test_get_coverage_unit`, `backend/tests/test_audit.py::test_update_coverage_unit`, `backend/tests/test_audit.py::test_delete_coverage_unit`, `backend/tests/test_audit.py::test_create_finding`, `backend/tests/test_audit.py::test_list_findings`, `backend/tests/test_audit.py::test_get_finding`, `backend/tests/test_audit.py::test_update_finding`, `backend/tests/test_audit.py::test_delete_finding`, `backend/tests/test_audit.py::test_export_coverage_ledger`, `backend/tests/test_audit.py::test_export_findings`

### auth-authorization — Add authentication and authorization layer

Status: done

Acceptance:
- Implement JWT token validation middleware
- Add role-based access control (viewer, operator, admin)
- Protect audit endpoints with authentication
- Add OIDC/Keycloak integration tests

Implementation: `backend/app/core/auth.py`, `backend/app/models/auth.py`, `backend/app/schemas/auth.py`, `backend/app/api/v1/auth.py`, `backend/app/api/v1/audit.py`, `backend/app/api/v1/items.py`

Tests: `backend/tests/test_audit.py`, `backend/tests/test_items.py`, `backend/tests/conftest.py`

