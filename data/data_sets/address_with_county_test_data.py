from data.data_format import DataFormat
from data.data_sets.state_county_test_data import StateCountyTestData
from data.test_data_generator import TestDataGenerator


class AddressWithCountyTestData(TestDataGenerator):
    """
    Test data generator for addresses with proper county information

    Usage:
        # Create address with valid county data
        address = AddressWithCountyTestData()

        # Access properties
        print(address.full_name)
        print(address.state_name)  # Full state name
        print(address.county)      # Valid county for the state
    """

    @property
    def full_name(self) -> str:
        """Person full name"""
        return self.factory.person.full_name()

    @property
    def street_address(self) -> str:
        """Street address"""
        return self.factory.address.street_address()

    @property
    def city(self) -> str:
        """City name in uppercase"""
        city = self.factory.address.city()
        return self.factory.format_value(city, DataFormat.UPPER)

    @property
    def state_county(self) -> StateCountyTestData:
        """State and county information"""
        # Create a state-county combination with consistent seed
        return StateCountyTestData(seed=hash(self.full_name))

    @property
    def state_code(self) -> str:
        """State code (2-letter abbreviation)"""
        return self.state_county.state_code

    @property
    def state_name(self) -> str:
        """Full state name"""
        return self.state_county.state_name

    @property
    def county(self) -> str:
        """County name valid for the state"""
        return self.state_county.county

    @property
    def zip_code(self) -> str:
        """ZIP/Postal code"""
        return self.factory.address.zipcode()

    @property
    def phone(self) -> str:
        """Contact phone number"""
        return self.factory.person.phone_number()

    @property
    def email(self) -> str:
        """Contact email"""
        return self.factory.internet.email(self.full_name)