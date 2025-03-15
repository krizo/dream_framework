import datetime
from typing import Optional

from faker import Faker


class DateTimeDataFactory:
    """Factory for generating date and time related data"""

    def __init__(self, faker: Faker):
        self.faker = faker

    def date(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> datetime.date:
        """
        Generate a random date

        Args:
            start_date: Minimum date (default: -30 years from today)
            end_date: Maximum date (default: today)
        """
        if not start_date:
            start_date = datetime.datetime.now() - datetime.datetime.timedelta(days=365 * 30)
        if not end_date:
            end_date = datetime.datetime.now()

        return self.faker.date_between(start_date=start_date, end_date=end_date)

    def future_date(self, days: int = 365) -> datetime.date:
        """Generate a random date in the future"""
        return self.faker.date_between(start_date='today', end_date=f'+{days}d')

    def past_date(self, days: int = 365) -> datetime.date:
        """Generate a random date in the past"""
        return self.faker.date_between(start_date=f'-{days}d', end_date='today')

    def datetime(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> datetime:
        """Generate a random datetime"""
        if not start_date:
            start_date = datetime.datetime.now() - datetime.timedelta(days=365 * 30)
        if not end_date:
            end_date = datetime.datetime.now()

        return self.faker.date_time_between(start_date=start_date, end_date=end_date)

    def date_string(self, pattern: str = "%Y-%m-%d") -> str:
        """
        Generate a random date string in the specified format

        Args:
            pattern: Date format pattern
        """
        return self.faker.date().strftime(pattern)

    def datetime_string(self, pattern: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Generate a random datetime string in the specified format

        Args:
            pattern: Datetime format pattern
        """
        return self.faker.date_time().strftime(pattern)

    def time_string(self, pattern: str = "%H:%M:%S") -> str:
        """
        Generate a random time string in the specified format

        Args:
            pattern: Time format pattern
        """
        return self.faker.time().strftime(pattern)

    def timestamp(self) -> int:
        """Generate a random Unix timestamp"""
        return int(self.faker.date_time().timestamp())

    def month(self) -> str:
        """Generate a random month name"""
        return self.faker.month_name()

    def day_of_week(self) -> str:
        """Generate a random day of week"""
        return self.faker.day_of_week()
