import os

from core.environments import BaseTestEnvironment

class TestEnvironment(BaseTestEnvironment):
    current_env = None

    def __init__(self, environment_name: str):
        super().__init__(os.environ.get('TEST_ENVIRONMENT') or 'dev')

    @property
    def hostname(self):
        return self.get_property('hostname')

