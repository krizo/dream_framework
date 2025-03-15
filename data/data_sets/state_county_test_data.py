import random
from typing import List, Optional

from data.test_data_generator import TestDataGenerator


class StateCountyTestData(TestDataGenerator):
    """
    Test data generator for state and county combinations using fixed data sets
    
    Usage:
        # Create state-county data
        state_county = StateCountyTestData()
        
        # Access properties
        Log.info(state_county.state_code)        # e.g., "MT"
        Log.info(state_county.state_name)        # e.g., "Montana"
        Log.info(state_county.county)            # e.g., "Entire State"
        
        # Force specific state
        state_county = StateCountyTestData()
        state_county.regenerate()  # Reset all values
        state_county._set_state("TX")  # Force Texas
        Log.info(state_county.state_name)  # "Texas"
        Log.info(state_county.county)  # One of the Texas counties
    """
    
    def __init__(self, locale: str = "en_US", seed: Optional[int] = None):
        """Initialize with optional locale and seed"""
        super().__init__(locale, seed)
        self._custom_state = None
    
    def _set_state(self, state_code: str) -> None:
        """
        Set a specific state code for data generation
        
        Args:
            state_code: Two-letter state code
        """
        self._custom_state = state_code
        # Clear county cache since it depends on state
        if 'county' in self._cache:
            del self._cache['county']
    
    @property
    def state_code(self) -> str:
        """State code (2-letter abbreviation)"""
        if self._custom_state:
            return self._custom_state
        return self.factory.address.state_with_counties(abbr=True)
    
    @property
    def state_name(self) -> str:
        """Full state name"""
        return self.factory.address.get_state_name(self.state_code)
    
    @property
    def county(self) -> str:
        """County name based on state"""
        return self.factory.address.county(self.state_code)
    
    @property
    def all_counties(self) -> List[str]:
        """Get all available counties for current state"""
        return self.factory.address.get_counties_for_state(self.state_code)
    
    @property
    def zipcode(self) -> str:
        """Random ZIP code for this state/county"""
        return self.factory.address.zipcode()
    
    def get_random_county(self) -> str:
        """Get a random county from the current state"""
        return random.choice(self.all_counties)
    
    def has_multiple_counties(self) -> bool:
        """Check if current state has multiple counties"""
        return len(self.all_counties) > 1