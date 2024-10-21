from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

from models.base_model import Base


class AutomationDatabase:
    def __init__(self, db_url):
        """
        Initialize the AutomationDatabase.

        @param db_url: URL of the database to connect to
        """
        self.engine = create_engine(db_url)
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
