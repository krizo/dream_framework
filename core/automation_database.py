from contextlib import contextmanager
from typing import Optional, List

from sqlalchemy import create_engine, StaticPool, inspect, MetaData
from sqlalchemy.orm import sessionmaker, scoped_session, joinedload

from core.logger import Log
from core.test_case import TestCase
from core.test_execution_record import TestExecutionRecord
from models.base_model import Base
from models.custom_metric_model import CustomMetricModel
from models.test_case_execution_record_model import TestExecutionRecordModel
from models.test_case_model import TestCaseModel


class AutomationDatabase:
    """
    Main database handler supporting both TestCase and TestExecutionRecord operations.
    Provides schema management and CRUD operations for test automation data.
    """

    def __init__(self, db_url: str, dialect: Optional[str] = None):
        """
        Initialize database connection with optional dialect support.

        @param db_url: Database connection URL
        @param dialect: Optional database dialect to emulate
        """
        self._dialect = dialect
        if dialect and db_url.startswith('sqlite'):
            engine_url = f"{db_url}?odbc_dialect={dialect}"
        else:
            engine_url = db_url

        connect_args = {'check_same_thread': False} if db_url == 'sqlite:///:memory:' else {}
        pool_class = StaticPool if db_url == 'sqlite:///:memory:' else None

        self.engine = create_engine(
            engine_url,
            connect_args=connect_args,
            poolclass=pool_class
        )

        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

        # Create all tables with fresh schema
        self.create_tables()

    @property
    def dialect(self) -> Optional[str]:
        """Get configured dialect name."""
        return self._dialect

    def create_tables(self):
        """Create all tables with proper dependency handling."""
        try:
            from models.test_run_model import TestRunModel
            from models.step_model import StepModel

            import os
            if os.environ.get('PYTEST_XDIST_WORKER'):
                try:
                    inspector = inspect(self.engine)
                    tables = inspector.get_table_names()
                    required_tables = {'test_cases', 'test_execution_records', 'test_runs', 'custom_metrics', 'steps'}
                    if not required_tables.issubset(set(tables)):
                        import time
                        for _ in range(30):  # max 30 attempts
                            time.sleep(0.1)
                            tables = inspector.get_table_names()
                            if required_tables.issubset(set(tables)):
                                return
                        raise Exception("Required tables not found after waiting")
                    return
                except Exception as e:
                    Log.warning(f"Worker {os.environ['PYTEST_XDIST_WORKER']} waiting for tables: {str(e)}")
                    return

            _ = [TestRunModel, TestCaseModel, TestExecutionRecordModel,
                 CustomMetricModel, StepModel]

            try:
                # Drop existing tables
                metadata = MetaData()
                metadata.reflect(bind=self.engine)
                metadata.drop_all(self.engine)

                inspector = inspect(self.engine)
                tables = inspector.get_table_names()
                if not tables:
                    Base.metadata.create_all(self.engine)
                    Log.debug("Database tables created successfully")
                else:
                    Log.debug("Tables already exist, skipping creation")
            except Exception as e:
                if "already exists" in str(e):
                    Log.debug("Tables already exist, continuing")
                else:
                    raise

        except Exception as e:
            Log.error(f"Error managing database schema: {str(e)}")
            if not os.environ.get('PYTEST_XDIST_WORKER'):
                raise

    def verify_schema(self):
        """
        Verify that all required columns exist.

        @raises ValueError: If required columns are missing
        """
        inspector = inspect(self.engine)

        # Check test_cases table
        test_case_columns = {col['name'] for col in inspector.get_columns('test_cases')}
        required_columns = {'id', 'test_id', 'test_module', 'test_function', 'name',
                            'description', 'test_suite', 'scope', 'component'}

        missing_columns = required_columns - test_case_columns
        if missing_columns:
            raise ValueError(f"Missing required columns in test_cases: {missing_columns}")

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            self.Session.remove()

    def insert_test_case(self, test_case: TestCase) -> int:
        """
        Insert a TestCase into the database.

        @param test_case: TestCase instance to persist
        @return: ID of the inserted TestCase
        """
        with self.session_scope() as session:
            test_case_model = test_case.to_model()
            session.add(test_case_model)
            session.flush()
            test_case_id = test_case_model.id
            Log.info(f"Test case inserted. ID: {test_case_id}")
            return test_case_id

    def fetch_test_case(self, test_case_id: int) -> Optional[TestCase]:
        """
        Fetch test case by ID from database.

        @param test_case_id: ID of the test case
        @return: TestCase instance if found, None otherwise
        """
        with self.session_scope() as session:
            session.expire_all()  # Force refresh from database
            model = session.query(TestCaseModel).filter_by(id=test_case_id).first()
            return TestCase.from_model(model) if model else None

    def fetch_test_case_by_test_id(self, test_id: str) -> Optional[TestCase]:
        """
        Find test case by its unique test_id.

        @param test_id: Unique test identifier (module::function)
        @return: TestCase instance if found, None otherwise
        """
        try:
            with self.session_scope() as session:
                session.expire_all()  # Force refresh from database
                model = session.query(TestCaseModel).filter_by(test_id=test_id).first()
                return TestCase.from_model(model) if model else None
        except Exception as e:
            Log.error(f"Error finding test case by ID {test_id}: {str(e)}")
            return None

    def update_test_case(self, test_case: TestCase) -> bool:
        """
        Update an existing test case in the database.

        @param test_case: TestCase instance to update
        @return: True if update was successful, False if test case not found
        """
        with self.session_scope() as session:
            existing = session.query(TestCaseModel).get(test_case.id)
            if not existing:
                Log.warning(f"Test case with ID {test_case.id} not found")
                return False

            # Update model with new values
            updated_model = test_case.to_model()
            for key, value in updated_model.__dict__.items():
                if key != '_sa_instance_state' and key != 'id':
                    setattr(existing, key, value)

            Log.info(f"Updated test case {test_case.id}")
            return True

    def insert_test_execution(self, execution: TestExecutionRecord) -> int:
        """
        Insert a test execution record.

        @param execution: TestExecutionRecord instance to persist
        @return: ID of the inserted record
        """
        with self.session_scope() as session:
            # Ensure test execution is initialized
            if not execution._initialized:
                execution.initialize()

            execution_model = execution.to_model()
            session.add(execution_model)
            session.flush()

            # Update execution ID and log
            execution.id = execution_model.id
            Log.info(f"Test execution record created. ID: {execution.id}")

            return execution.id

    def fetch_test_execution(self, execution_id: int) -> Optional[TestExecutionRecord]:
        """
        Fetch test execution record by ID.

        @param execution_id: Database ID of the execution record
        @return: TestExecutionRecord if found, None otherwise
        """
        try:
            with self.session_scope() as session:
                # Get execution record with test case in single query
                model = session.query(TestExecutionRecordModel) \
                    .join(TestCaseModel) \
                    .options(joinedload(TestExecutionRecordModel.test_case)) \
                    .options(joinedload(TestExecutionRecordModel.custom_metrics)) \
                    .filter(TestExecutionRecordModel.id == execution_id) \
                    .first()

                if model is None:
                    Log.warning(f"Test execution record {execution_id} not found")
                    return None

                if model.test_case is None:
                    Log.warning(f"Associated test case not found for execution {execution_id}")
                    return None

                # Create test case first
                test_case = TestCase.from_model(model.test_case)
                if test_case is None:
                    Log.warning(f"Failed to create test case from model for execution {execution_id}")
                    return None

                # Now create execution record
                record = TestExecutionRecord.from_model(model, test_case)
                if record is None:
                    Log.warning(f"Failed to create execution record from model for ID {execution_id}")
                    return None

                return record

        except Exception as e:
            Log.error(f"Error fetching test execution {execution_id}: {str(e)}")
            return None

    def update_test_execution(self, execution: TestExecutionRecord) -> bool:
        """
        Update existing test execution record.

        @param execution: TestExecutionRecord instance to update
        @return: True if update was successful, False otherwise
        """
        try:
            with self.session_scope() as session:
                existing = session.query(TestExecutionRecordModel) \
                    .filter_by(id=execution.id) \
                    .first()

                if not existing:
                    Log.warning(f"Test execution {execution.id} not found")
                    return False

                # Update base fields
                model = execution.to_model()
                for key, value in model.__dict__.items():
                    if key not in ('_sa_instance_state', 'id', 'custom_metrics'):
                        setattr(existing, key, value)

                # Clear and recreate metrics
                existing.custom_metrics.clear()
                session.flush()

                for metric in execution.get_all_metrics():
                    existing.custom_metrics.append(
                        CustomMetricModel(
                            name=metric['name'],
                            value=metric['value']
                        )
                    )

                Log.info(f"Updated test execution {execution.id}")
                return True

        except Exception as e:
            Log.error(f"Failed to update test execution: {str(e)}")
            return False

    def fetch_executions_for_test(self, test_case_id: int) -> List[TestExecutionRecord]:
        """
        Fetch all executions for a specific test case.

        @param test_case_id: Database ID of the test case
        @return: List of TestExecutionRecord instances
        """
        with self.session_scope() as session:
            executions = []
            models = session.query(TestExecutionRecordModel) \
                .options(joinedload(TestExecutionRecordModel.test_case)) \
                .options(joinedload(TestExecutionRecordModel.custom_metrics)) \
                .filter(TestExecutionRecordModel.test_case_id == test_case_id) \
                .all()

            if not models:
                return executions

            test_case = TestCase.from_model(models[0].test_case)
            if test_case is None:
                return executions

            for model in models:
                execution = TestExecutionRecord.from_model(model, test_case)
                if execution is not None:
                    executions.append(execution)

            return executions
