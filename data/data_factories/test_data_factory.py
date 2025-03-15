import random
from typing import Optional, Union

from faker import Faker

from data.data_factories.address_data_factory import AddressDataFactory
from data.data_factories.company_data_factory import CompanyDataFactory
from data.data_factories.date_time_data_factory import DateTimeDataFactory
from data.data_factories.internet_data_factory import InternetDataFactory
from data.data_factories.person_data_factory import PersonDataFactory
from data.data_factories.text_data_factory import TextDataFactory
from data.data_format import DataFormat


class TestDataFactory:
    """
    Main factory for generating test data with specialized sub-factories
    """

    def __init__(self, locale: str = "en_US", seed: Optional[int] = None):
        """
        Initialize the test data factory

        Args:
            locale: Locale for data generation
            seed: Optional seed for reproducible data
        """
        self.faker = Faker(locale)
        if seed is not None:
            self.faker.seed_instance(seed)
            random.seed(seed)

        # Initialize sub-factories
        self.person = PersonDataFactory(self.faker)
        self.address = AddressDataFactory(self.faker)
        self.datetime = DateTimeDataFactory(self.faker)
        self.company = CompanyDataFactory(self.faker)
        self.internet = InternetDataFactory(self.faker)
        self.text = TextDataFactory(self.faker)

    def format_value(self, value: str, format_type: Union[DataFormat, str]) -> str:
        """
        Format a string value according to the specified format

        Args:
            value: The string to format
            format_type: The format to apply

        Returns:
            Formatted string
        """
        if isinstance(format_type, str):
            try:
                format_type = DataFormat(format_type)
            except ValueError:
                format_type = DataFormat.DEFAULT

        if format_type == DataFormat.UPPER:
            return value.upper()
        elif format_type == DataFormat.LOWER:
            return value.lower()
        elif format_type == DataFormat.TITLE:
            return value.title()
        elif format_type == DataFormat.SNAKE_CASE:
            # Convert spaces and hyphens to underscores, make lowercase
            result = value.replace(' ', '_').replace('-', '_').lower()
            # Remove any non-alphanumeric characters except underscores
            result = ''.join(c for c in result if c.isalnum() or c == '_')
            return result
        elif format_type == DataFormat.CAMEL_CASE:
            # First, convert to snake case
            snake = self.format_value(value, DataFormat.SNAKE_CASE)
            # Then convert to camel case
            components = snake.split('_')
            return components[0] + ''.join(x.title() for x in components[1:])
        elif format_type == DataFormat.PASCAL_CASE:
            # First, convert to snake case
            snake = self.format_value(value, DataFormat.SNAKE_CASE)
            # Then convert to pascal case
            components = snake.split('_')
            return ''.join(x.title() for x in components)
        elif format_type == DataFormat.KEBAB_CASE:
            # Convert spaces and underscores to hyphens, make lowercase
            result = value.replace(' ', '-').replace('_', '-').lower()
            # Remove any non-alphanumeric characters except hyphens
            result = ''.join(c for c in result if c.isalnum() or c == '-')
            return result
        else:
            return value
