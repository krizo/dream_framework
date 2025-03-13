import os

import pytest

from medmutual.run_env import RunEnvironment


@pytest.fixture(scope="session")
def test_env() -> RunEnvironment:
    return RunEnvironment()

