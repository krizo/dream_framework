from typing import Dict, Any, Optional

from data.data_factories.test_data_factory import TestDataFactory


class TestDataGenerator:
    """
    Base class for test data generation

    Usage:
        class UserTestData(TestDataGenerator):
            @property
            def first_name(self):
                return self.factory.person.first_name()

            @property
            def last_name(self):
                return self.factory.person.last_name()

            @property
            def email(self):
                return self.factory.internet.email(
                    f"{self.first_name} {self.last_name}"
                )
    """

    def __init__(self, locale: str = "en_US", seed: Optional[int] = None):
        """
        Initialize test data generator

        Args:
            locale: Locale for data generation
            seed: Optional seed for reproducible data
        """
        self.factory = TestDataFactory(locale, seed)
        self._cache = {}

    def __getattr__(self, name):
        """
        Implement caching of property values by default

        This ensures consistency when accessing properties multiple times
        (first_name will be the same each time it's accessed)
        """
        # First, check in cache
        if name in self._cache:
            return self._cache[name]

        # Try to get the property value
        if name in dir(self.__class__):
            attr = getattr(self.__class__, name)
            if isinstance(attr, property):
                # Get the property value and cache it
                value = attr.__get__(self, self.__class__)
                self._cache[name] = value
                return value

        # Attribute not found
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    def regenerate(self, *fields):
        """
        Regenerate specific fields or all fields

        Args:
            *fields: Names of fields to regenerate (or none for all)
        """
        if not fields:
            # Regenerate all fields
            self._cache.clear()
        else:
            # Regenerate specific fields
            for field in fields:
                if field in self._cache:
                    del self._cache[field]

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert all properties to a dictionary
        """
        result = {}

        for name in dir(self.__class__):
            if name.startswith('_'):
                continue

            attr = getattr(self.__class__, name)
            if isinstance(attr, property):
                result[name] = getattr(self, name)

        return result
