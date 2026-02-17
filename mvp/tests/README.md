# Integration Tests - README

## Overview

This directory contains comprehensive integration tests for the Cost-Optimized Supply Chain MVP system.

## Test Files

### test_integration_task16.py
Comprehensive integration tests covering:
- All three personas (Warehouse Manager, Field Engineer, Procurement Specialist)
- System features (caching, memory, cost tracking, authentication)
- End-to-end workflows

**Test Count**: 15 tests  
**Status**: ✅ All Passing

### test_task10_integration.py
Integration tests for Task 10 (Caching and Conversation Memory)

## Running Tests

### Run All Integration Tests

```bash
# Using pytest (recommended)
cd mvp
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_integration_task16.py -v

# Run with output
python -m pytest tests/test_integration_task16.py -v -s
```

### Run Tests Directly

```bash
cd mvp
python tests/test_integration_task16.py
```

## Test Structure

### Task 16 Tests

```
test_integration_task16.py
├── TestWarehouseManagerWorkflows
│   ├── test_sql_query_inventory_data
│   ├── test_inventory_optimization_tools
│   └── test_demand_forecasting
├── TestFieldEngineerWorkflows
│   ├── test_sql_query_order_data
│   ├── test_logistics_optimization_tools
│   └── test_fulfillment_tracking
├── TestProcurementSpecialistWorkflows
│   ├── test_sql_query_purchase_order_data
│   ├── test_supplier_analysis_tools
│   └── test_cost_comparison
├── TestSystemFeatures
│   ├── test_query_caching_identical_queries
│   ├── test_conversation_memory_followup
│   ├── test_cost_tracking_calculations
│   └── test_authentication_and_authorization
└── TestEndToEndIntegration
    ├── test_complete_warehouse_manager_workflow
    └── test_persona_switching_workflow
```

## Test Coverage

### Personas
- ✅ Warehouse Manager workflows
- ✅ Field Engineer workflows
- ✅ Procurement Specialist workflows

### System Features
- ✅ Query caching (LRU + TTL)
- ✅ Conversation memory (10 interactions)
- ✅ Cost tracking (Bedrock + Redshift + Lambda)
- ✅ Authentication (bcrypt)
- ✅ Session management
- ✅ Persona authorization

### Components Tested
- `QueryCache` - Result caching
- `ConversationMemory` - Session history
- `CostTracker` - Cost calculation
- `AuthManager` - User authentication
- `SessionManager` - Session management
- `CalculationTools` - Business calculations

## Expected Output

When all tests pass, you should see:

```
======================================================================
✅ ALL INTEGRATION TESTS PASSED
======================================================================

Task 16 Implementation Verified:
  ✓ 16.1: Warehouse Manager workflows (SQL, optimization, forecasting)
  ✓ 16.2: Field Engineer workflows (orders, logistics, tracking)
  ✓ 16.3: Procurement Specialist workflows (POs, suppliers, costs)
  ✓ 16.4: System features (caching, memory, cost, auth)
  ✓ End-to-end integration workflows
======================================================================
```

## Test Requirements

### Python Packages
- pytest
- bcrypt
- All MVP dependencies (see requirements.txt)

### No External Dependencies
These tests are designed to run without:
- AWS credentials
- Database connections
- External services

All external dependencies are mocked or simulated.

## Troubleshooting

### Import Errors
If you see import errors, ensure you're running from the `mvp` directory:
```bash
cd mvp
python -m pytest tests/test_integration_task16.py -v
```

### Test Failures
If tests fail:
1. Check that all dependencies are installed: `pip install -r requirements.txt`
2. Verify you're using Python 3.11+
3. Check the test output for specific error messages

## Adding New Tests

When adding new integration tests:

1. Follow the existing test structure
2. Use descriptive test names
3. Include print statements for progress tracking
4. Mock external dependencies
5. Clean up resources in teardown
6. Update this README

## Documentation

For detailed test results and coverage, see:
- `TASK_16_INTEGRATION_TEST_SUMMARY.md` - Comprehensive test summary

## Contact

For questions about the tests, refer to:
- Task 16 in `.kiro/specs/cost-optimized-mvp/tasks.md`
- Design document in `.kiro/specs/cost-optimized-mvp/design.md`
