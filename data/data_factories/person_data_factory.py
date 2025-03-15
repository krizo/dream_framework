import random
from typing import Optional

from faker import Faker

class PersonDataFactory:
    """Factory for generating person-related data"""

    def __init__(self, faker: Faker):
        self.faker = faker

    def first_name(self, gender: Optional[str] = None) -> str:
        """Generate a random first name"""
        if gender == "male":
            return self.faker.first_name_male()
        elif gender == "female":
            return self.faker.first_name_female()
        else:
            return self.faker.first_name()

    def last_name(self) -> str:
        """Generate a random last name"""
        return self.faker.last_name()

    def full_name(self, gender: Optional[str] = None) -> str:
        """Generate a random full name"""
        if gender == "male":
            return self.faker.name_male()
        elif gender == "female":
            return self.faker.name_female()
        else:
            return self.faker.name()

    def prefix(self, gender: Optional[str] = None) -> str:
        """Generate a random name prefix"""
        if gender == "male":
            return random.choice(["Mr.", "Dr.", "Prof."])
        elif gender == "female":
            return random.choice(["Mrs.", "Ms.", "Dr.", "Prof."])
        else:
            return random.choice(["Mr.", "Mrs.", "Ms.", "Dr.", "Prof."])

    def suffix(self) -> str:
        """Generate a random name suffix"""
        return random.choice(["Jr.", "Sr.", "III", "IV", "PhD", "MD", "Esq."])

    def ssn(self) -> str:
        """Generate a random SSN"""
        return self.faker.ssn()

    def phone_number(self, format: str = None) -> str:
        """Generate a random phone number"""
        if format:
            # Use placeholder '#' in format string to insert random digits
            result = ""
            for char in format:
                if char == '#':
                    result += str(random.randint(0, 9))
                else:
                    result += char
            return result
        return self.faker.phone_number()

    def gender(self) -> str:
        """Return a random gender"""
        return random.choice(["Male", "Female", "Non-binary"])

    def job_title(self) -> str:
        """Generate a random job title"""
        return self.faker.job()