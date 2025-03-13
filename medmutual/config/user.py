"""
User class for defining Med Mutual users
"""
from core.credentials import Credentials
from core.logger import Log


class User:
    _credentials: Credentials = None

    def __init__(self, name: str):
        Log.info(f"Initializing User with name: {name}")
        self.name = name

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_credentials') or cls._credentials is None:
            cls._credentials = Credentials()
        instance = super().__new__(cls)
        return instance

    @property
    def username(self) -> str:
        return self._credentials.get('users', self.name, 'username')

    @property
    def password(self) -> str:
        return self._credentials.get('users', self.name, 'password')
