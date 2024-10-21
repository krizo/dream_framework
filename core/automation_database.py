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

    def refresh(self, obj):
        """
                Refresh the state of the given instance from the database.

        This method synchronizes the state of the object in memory with its current state in the database.
        It's useful when the database might have been modified by another process or transaction.

        The method first merges the object with the current session (to ensure it's associated with this session),
        then refreshes it from the database.

        @param obj: The object to refresh
        @note: This operation will overwrite any local changes that haven't been committed to the database.
        @warning: This can be expensive for large objects or complex relationships.
        """
        with self.session_scope() as session:
            session.refresh(session.merge(obj))
