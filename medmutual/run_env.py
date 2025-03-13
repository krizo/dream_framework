import os

from medmutual.config.mm_test_environment import TestEnvironment
from medmutual.config.user import User


class RunEnvironment:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance') or cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._env: TestEnvironment = TestEnvironment()
        self.user: User = User(name=os.environ.get('TEST_USER') or 'krizBober')

    @property
    def base_url(self):
        return self._env.hostname


