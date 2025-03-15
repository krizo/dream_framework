from typing import Optional

from faker import Faker


class InternetDataFactory:
    """Factory for generating internet-related data"""

    def __init__(self, faker: Faker):
        self.faker = faker

    def email(self, name: Optional[str] = None, domain: Optional[str] = None) -> str:
        """
        Generate a random email address

        Args:
            name: Optional name to use in email (default: random)
            domain: Optional domain to use (default: random)
        """
        if name and domain:
            username = name.lower().replace(' ', '.').replace("'", '')
            return f"{username}@{domain}"
        elif name:
            username = name.lower().replace(' ', '.').replace("'", '')
            return f"{username}@{self.faker.free_email_domain()}"
        else:
            return self.faker.email()

    def domain_name(self) -> str:
        """Generate a random domain name"""
        return self.faker.domain_name()

    def url(self) -> str:
        """Generate a random URL"""
        return self.faker.url()

    def ip_address(self) -> str:
        """Generate a random IP address"""
        return self.faker.ipv4()

    def ipv6_address(self) -> str:
        """Generate a random IPv6 address"""
        return self.faker.ipv6()

    def user_agent(self) -> str:
        """Generate a random user agent string"""
        return self.faker.user_agent()

    def username(self) -> str:
        """Generate a random username"""
        return self.faker.user_name()

    def password(self, length: int = 12, special_chars: bool = True,
                digits: bool = True, upper_case: bool = True) -> str:
        """
        Generate a random password

        Args:
            length: Length of the password
            special_chars: Include special characters
            digits: Include digits
            upper_case: Include uppercase letters
        """
        return self.faker.password(
            length=length,
            special_chars=special_chars,
            digits=digits,
            upper_case=upper_case
        )