# """Tests for core database functionality."""
#
# import pytest
# from sqlalchemy import inspect
#
# from core.automation_database import AutomationDatabase
# from core.automation_database_manager import AutomationDatabaseManager
# from core.test_case import TestCase
# from core.test_execution_record import TestExecutionRecord
# from core.test_result import TestResult
# from core.test_run import TestRun
#
#
# @pytest.fixture
# def test_db(tmp_path):
#     """
#     Provide clean SQLite database for each test.
#     """
#     db_file = tmp_path / "test.db"
#     db = AutomationDatabase(f"sqlite:///{db_file}")
#     db.create_tables()
#
#     # Set as current database instance
#     AutomationDatabaseManager._db_instance = db
#     AutomationDatabaseManager._initialized = True
#
#     yield db
#
#
# @pytest.fixture
# def active_test_run(request):
#     """Provide active test run instance."""
#     TestRun.reset()
#     test_run = TestRun.initialize(
#         owner="test_user",
#         environment="test",
#         test_run_id=f"test_run_{request.node.name}"
#     )
#     yield test_run
#     TestRun.reset()
#
#
# @pytest.fixture
# def base_test_case():
#     """Provide basic test case for database testing."""
#     test_case = TestCase(
#         name="Database Test",
#         description="Test for database operations",
#         test_suite="Database Tests",
#         scope="Unit",
#         component="Database"
#     )
#     return test_case
#
#
# @pytest.fixture
# def prepared_test_case(base_test_case, request):
#     """Provide test case with properly set location."""
#     test_case = TestCase(
#         name=base_test_case.name,
#         description=base_test_case.description,
#         test_suite=base_test_case.test_suite,
#         scope=base_test_case.scope,
#         component=base_test_case.component
#     )
#     # Set unique test location for each test
#     test_case.set_test_location(
#         f"test_module_{request.node.name}.py",
#         f"test_function_{request.node.name}"
#     )
#     return test_case
#
#
# def test_database_initialization(test_db, active_test_run):
#     """Test database initialization and schema creation."""
#     inspector = inspect(test_db.engine)
#     tables = inspector.get_table_names()
#
#     required_tables = {'test_cases', 'test_execution_records', 'custom_metrics', 'test_runs', 'steps'}
#     assert required_tables.issubset(set(tables)), f"Missing required tables. Found: {tables}"
#
#     # Verify required columns in test_cases
#     test_case_columns = {col['name'] for col in inspector.get_columns('test_cases')}
#     required_columns = {
#         'id', 'test_id', 'test_module', 'test_function',
#         'name', 'description', 'test_suite', 'properties'
#     }
#     assert required_columns.issubset(test_case_columns)
#
#
# def test_test_case_operations(test_db, active_test_run, base_test_case):
#     """Test CRUD operations for TestCase."""
#     # Set test location
#     base_test_case.set_test_location("test_module.py", "test_function")
#
#     # Create
#     test_case_id = test_db.insert_test_case(base_test_case)
#     assert test_case_id is not None
#
#     # Read by ID
#     retrieved = test_db.fetch_test_case(test_case_id)
#     assert retrieved is not None
#     assert retrieved.name == base_test_case.name
#     assert retrieved.test_id == base_test_case.test_id
#
#     # Read by test_id
#     retrieved_by_test_id = test_db.fetch_test_case_by_test_id(base_test_case.test_id)
#     assert retrieved_by_test_id is not None
#     assert retrieved_by_test_id.id == test_case_id
#
#     # Update
#     retrieved.description = "Updated Description"
#     update_success = test_db.update_test_case(retrieved)
#     assert update_success is True
#
#     # Verify update
#     updated = test_db.fetch_test_case(test_case_id)
#     assert updated.description == "Updated Description"
#
#
# def test_execution_record_operations(test_db, prepared_test_case):
#     """Test CRUD operations for TestExecutionRecord."""
#     # Create test case first
#     test_case_id = test_db.insert_test_case(prepared_test_case)
#     prepared_test_case.id = test_case_id
#
#     # Create execution record with all required fields
#     execution = TestExecutionRecord(prepared_test_case)
#     execution.initialize()  # Initialize first
#     execution.set_test_location(
#         prepared_test_case.test_module,
#         prepared_test_case.test_function,
#         prepared_test_case.name,
#         prepared_test_case.description
#     )
#     execution.start()
#     execution.add_custom_metric("metric1", "value1")
#     execution.add_custom_metric("metric2", 123)
#
#     # Insert
#     execution_id = test_db.insert_test_execution(execution)
#     assert execution_id is not None
#
#     # Read
#     retrieved = test_db.fetch_test_execution(execution_id)
#     assert retrieved is not None
#     assert retrieved.test_case.id == test_case_id
#     assert retrieved.test_module == prepared_test_case.test_module
#     assert retrieved.test_function == prepared_test_case.test_function
#     assert retrieved.get_metric("metric1") == "value1"
#     assert retrieved.get_metric("metric2") == 123
#
#
# def test_multiple_executions(test_db, prepared_test_case):
#     """Test handling multiple executions of the same test case."""
#     # Create test case first
#     test_case_id = test_db.insert_test_case(prepared_test_case)
#     prepared_test_case.id = test_case_id
#
#     execution_ids = []
#     scenarios = [
#         (TestResult.PASSED, True, None),
#         (TestResult.FAILED, False, "Test failed"),
#         (TestResult.XFAILED, True, "Expected failure")
#     ]
#
#     # Use unique test_run_id for each execution
#     import datetime
#     base_time = datetime.datetime.now()
#
#     for i, (result, expected_success, failure_msg) in enumerate(scenarios):
#         execution = TestExecutionRecord(prepared_test_case)
#         execution.initialize()  # Initialize first
#
#         # Set unique test_run_id and function name for each execution
#         unique_timestamp = (base_time + datetime.timedelta(seconds=i)).strftime("%Y%m%d_%H%M%S_%f")
#         execution.test_run_id = f"test_run_{unique_timestamp}"
#
#         # Set unique test location for each execution
#         test_function = f"{prepared_test_case.test_function}_execution_{i}"
#         execution.set_test_location(
#             prepared_test_case.test_module,
#             test_function,
#             prepared_test_case.name,
#             prepared_test_case.description
#         )
#
#         execution.start()
#         execution.add_custom_metric("iteration", i)
#         execution.add_custom_metric("status", result.value)
#
#         if failure_msg:
#             execution.set_failure(failure_msg, result.value)
#
#         execution.end(result)
#         execution_id = test_db.insert_test_execution(execution)
#         execution_ids.append(execution_id)
#
#     # Fetch all executions
#     executions = test_db.fetch_executions_for_test(test_case_id)
#     assert len(executions) == len(scenarios), \
#         f"Expected {len(scenarios)} executions, got {len(executions)}"
#
#     # Verify execution details
#     success_count = sum(1 for e in executions if e.is_successful)
#     assert success_count == 2  # PASSED and XFAILED are successful
#
#     # Verify each execution
#     for execution, (result, _, failure_msg) in zip(executions, scenarios):
#         assert execution.result == result
#         if failure_msg:
#             assert execution.failure == failure_msg
#
#     # Verify metrics
#     for i, execution in enumerate(executions):
#         assert execution.get_metric("iteration") == i
#         assert execution.get_metric("status") == scenarios[i][0].value
#
#     # Verify all executions have unique combinations of identifiers
#     execution_keys = [
#         (e.id, e.test_run_id, e.test_function)
#         for e in executions
#     ]
#     assert len(set(execution_keys)) == len(execution_keys), \
#         "All executions should have unique combinations of test_case_id, test_run_id, and test_function"
