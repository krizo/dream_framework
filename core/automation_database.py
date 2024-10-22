from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

from core.test_case import TestCase
from models.base_model import Base
from models.test_case_model import TestCaseModel


class AutomationDatabase:
    def __init__(self, db_url, dialect=None):
        """
        Initialize the AutomationDatabase.

        @param db_url: URL of the database to connect to
        @param dialect: Optional dialect to emulate (e.g., 'mssql', 'oracle', 'mysql')
        """
        if dialect and db_url.startswith('sqlite'):
            # Emulate specified dialect using SQLite
            engine_url = f"{db_url}?odbc_dialect={dialect}"
        else:
            engine_url = db_url

        self.engine = create_engine(engine_url)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

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

    def fetch_test_case(self, test_case_id: int) -> Optional[TestCase]:
        """
        Fetch a TestCase from the database by its ID.

        @param test_case_id: The ID of the TestCase to fetch
        @return: TestCase object if found, None otherwise
        """
        with self.session_scope() as session:
            test_case_model = session.query(TestCaseModel).filter_by(id=test_case_id).first()
            if test_case_model:
                return TestCase.from_model(test_case_model)
        return None

    def insert_test_case(self, test_case: TestCase) -> int:
        """
        Insert a TestCase into the database.

        @param test_case: The TestCase object to insert
        @return: The ID of the inserted TestCase
        """
        with self.session_scope() as session:
            test_case_model = test_case.to_model()
            test_case_model.id = None  # Ensure we're not trying to insert with a pre-existing ID
            session.add(test_case_model)
            session.flush()  # This will assign a new ID to the model
            test_case.id = test_case_model.id  # Update the TestCase with the new ID
            return test_case_model.id

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
