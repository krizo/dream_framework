from contextlib import contextmanager
from typing import Optional

from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker, scoped_session

from core.logger import Log
from core.test_case import TestCase
from models.base_model import Base
from models.test_case_model import TestCaseModel


class AutomationDatabase:
    def __init__(self, db_url: str, dialect: Optional[str] = None):
        """
        Initialize the AutomationDatabase. This database is used to store test execution data, including test cases,
        their results, metrics, and other test automation artifacts.

        @param db_url: URL of the database to connect to
        @param dialect: Optional dialect to emulate (e.g., 'mssql', 'oracle', 'mysql')
        """
        self._dialect = dialect
        if dialect and db_url.startswith('sqlite'):
            engine_url = f"{db_url}?odbc_dialect={dialect}"
        else:
            engine_url = db_url

        # For SQLite in-memory database, we need to maintain a single connection
        # to preserve the data between operations
        if db_url == 'sqlite:///:memory:':
            self.engine = create_engine(
                engine_url,
                connect_args={'check_same_thread': False},
                poolclass=StaticPool  # Use static pool for in-memory database
            )
        else:
            self.engine = create_engine(engine_url)

        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

        # Create all tables immediately
        Base.metadata.create_all(self.engine)

    @property
    def dialect(self) -> Optional[str]:
        """
        Get the current database dialect.

        @return: Current dialect name or None if not set
        """
        return self._dialect

    def create_tables(self):
        """
        Create all tables in the database.
        """
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope around a series of operations.

        @yield: Database session
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            self.Session.remove()

    def query(self, model):
        """
        Create a query for the given model.

        @param model: The model to query
        @return: Query object for the given model
        """
        return self.Session.query(model)

    def insert(self, obj):
        """
        Insert a new object into the database.

        @param obj: The object to insert
        """
        with self.session_scope() as session:
            session.add(obj)

    def delete(self, obj):
        """
        Delete an object from the database.

        @param obj: The object to delete
        """
        with self.session_scope() as session:
            session.delete(session.merge(obj))

    def update(self, obj):
        """
        Update an object in the database.

        @param obj: The object to update
        """
        with self.session_scope() as session:
            session.merge(obj)

    def insert_test_case(self, test_case: TestCase) -> int:
        """
        Insert a TestCase into the database.

        @param test_case: The TestCase object to insert
        @return: The ID of the inserted TestCase
        """
        with self.session_scope() as session:
            test_case_model = test_case.to_model()
            test_case_model.id = None
            session.add(test_case_model)
            session.flush()
            test_case.id = test_case_model.id
            Log.console(f"Test case saved with ID: {test_case.id}")
            # Commit immediately for in-memory database
            session.commit()
            return test_case_model.id

    def fetch_test_case(self, test_case_id: int) -> Optional[TestCase]:
        """
        Fetch a TestCase from the database by its ID.

        @param test_case_id: The ID of the TestCase to fetch
        @return: TestCase object if found, None otherwise
        """
        Log.console(f"\nAutomationDatabase: fetching test case with ID: {test_case_id}")
        with self.session_scope() as session:
            # Use refresh_expire for in-memory database
            session.expire_all()
            test_case_model = session.query(TestCaseModel).filter_by(id=test_case_id).first()
            if test_case_model:
                Log.console("Test case found in database")
                return TestCase.from_model(test_case_model)
            Log.console("Test case NOT found in database")
        return None

    def update_test_case(self, test_case: TestCase) -> bool:
        """
        Update an existing TestCase in the database.

        @param test_case: The TestCase object to update
        @return: True if the update was successful, False otherwise
        """
        with self.session_scope() as session:
            existing_model = session.query(TestCaseModel).filter_by(id=test_case.id).first()
            if existing_model:
                updated_model = test_case.to_model()
                for key, value in updated_model.__dict__.items():
                    if key != '_sa_instance_state':
                        setattr(existing_model, key, value)
                return True
        return False
