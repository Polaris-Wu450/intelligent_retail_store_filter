# Tests - Quick Guide

## 🚀 Run Tests

```bash
./test.sh
```

Or:

```bash
make test-local
```

## 📁 Test Files

```
tests/
├── conftest.py                              # Shared fixtures (test data)
├── unit/
│   └── test_customer_duplicate_detection.py # 17 unit tests
└── integration/
    ├── test_feedback_api.py                 # 10 integration tests
    └── test_error_handling.py               # 16 error handling tests

Total: 43 tests ✅
Coverage: 49%
```

## 📝 Test Coverage

### Unit Tests (17)
- Customer duplicate detection logic
- All scenarios: reuse, warnings, conflicts

### Integration Tests (26)
- Complete feedback API workflow
- Error handling (400, 409, 200 with warnings)
- Database operations

## 🔧 Configuration

- `pytest.ini` - Pytest configuration
- `conftest.py` - Shared test data
- `test.sh` - Simple test runner
- `Makefile` - Convenient commands

## 🎯 Quick Commands

```bash
./test.sh              # Run all tests
./test.sh tests/unit/  # Run unit tests only
make test-local        # Run with make
make clean             # Clean test artifacts
```

## ✅ Status

- 43 tests passing
- 49% coverage
- All duplicate detection logic tested
- All error handling tested

Done! 🎉
