from typing import Dict, Any, Optional, Dict
import functools
import random
import time

from data.data_factories.test_data_factory import TestDataFactory


class TestDataGenerator:
    """
    Base class for test data generation

    Each new instance will generate fresh data, but properties will
    return consistent values once accessed.

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
        # Generate a new seed for each instance if not provided
        if seed is None:
            # Use current time and a random component to ensure uniqueness
            seed = int(time.time() * 1000) + random.randint(1, 1000000)

        self.factory = TestDataFactory(locale, seed)
        self._cache = {}
        
        # Apply caching to all properties
        self._wrap_properties()

    def _wrap_properties(self):
        """
        Wrap all property getters with a caching mechanism
        """
        # Get all properties from the class
        for name in dir(self.__class__):
            if name.startswith('_'):
                continue
                
            attr = getattr(self.__class__, name)
            if isinstance(attr, property) and attr.fget:
                # Create a cached version of the property getter
                original_getter = attr.fget
                
                @functools.wraps(original_getter)
                def cached_getter(self_obj, orig_getter=original_getter, prop_name=name):
                    if prop_name not in self_obj._cache:
                        self_obj._cache[prop_name] = orig_getter(self_obj)
                    return self_obj._cache[prop_name]
                
                # Create a new property with the cached getter
                new_prop = property(cached_getter, attr.fset, attr.fdel, attr.__doc__)
                
                # Set the new property on the instance
                setattr(type(self), name, new_prop)

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