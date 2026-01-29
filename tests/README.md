# Flask Backend Test Suite

## Running Tests

### Install Test Dependencies
```bash
pip install pytest pytest-flask pytest-cov pytest-mock
```

### Run All Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=tuned --cov-report=html

# Run specific test file
pytest tests/test_auth_routes.py

# Run specific test
pytest tests/test_auth_routes.py::test_user_registration_success
```

### Run Tests by Category
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Auth tests only
pytest tests/test_auth_*
```

## Test Structure

```
tests/
├── conftest.py                    # Pytest fixtures and configuration
├── test_utils_tokens.py          # Token utility tests
├── test_utils_validators.py      # Validator utility tests
├── test_utils_password.py        # Password utility tests
├── test_auth_schemas.py          # Marshmallow schema tests
├── test_auth_routes.py           # Auth route tests
└── test_auth_integration.py      # Full flow integration tests
```

## Coverage Goals

- **Target**: 90%+ code coverage
- **Focus Areas**: Auth routes, utilities, schemas, services
- **Excluded**: Third-party integrations (mocked)

## Test Data

Test fixtures use isolated database and Redis instances to prevent interference with development data.
