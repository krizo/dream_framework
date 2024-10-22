from core.plugins.test_case_plugin import TestCasePlugin


def pytest_configure(config):
    """ Registering pytest plug-ins """
    config.pluginmanager.register(TestCasePlugin())
