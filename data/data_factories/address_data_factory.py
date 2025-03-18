import random
from decimal import Decimal
from typing import Optional, List

from faker import Faker


class AddressDataFactory:
    """Factory for generating address-related data"""

    def __init__(self, faker: Faker):
        self.faker = faker

        # US States data (code to full name mapping)
        self.us_states = {
            "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
            "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
            "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
            "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
            "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
            "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
            "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
            "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
            "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
            "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
            "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
            "WI": "Wisconsin", "WY": "Wyoming"
        }

        # Reverse mapping (name to code)
        self.state_names_to_code = {v.lower(): k for k, v in self.us_states.items()}

        # Fixed counties for specific states
        self.counties_by_state = {
            # Montana has only "Entire State"
            "MT": ["Entire State"],

            # Texas counties - limited set
            "TX": ["Harris", "Archer", "Austin", "Bandera", "Bell"],

            # Kentucky counties - limited set
            "KY": ["Bell", "Boyd", "Bath", "Clay", "Floyd"],

            # Ohio counties - limited set
            "OH": ["Adams County", "Athens County", "Lake County", "Darke County", "Miami County"],

            # Virginia counties - limited set
            "VA": ["Hanover County", "Fairfax County", "Hanover County", "Sorry County", "Henrico County"],
        }

        # Sample counties for other states
        self.sample_counties = [
            "Albany", "Bronx", "Broome", "Cattaraugus", "Cayuga", "Chautauqua",
            "Chemung", "Chenango", "Clinton", "Columbia", "Cortland", "Delaware",
            "Dutchess", "Erie", "Essex", "Franklin", "Fulton", "Genesee", "Greene"
        ]

    def street_address(self) -> str:
        """Generate a random street address"""
        return self.faker.street_address()

    def city(self) -> str:
        """Generate a random city name"""
        return self.faker.city()

    def state(self, abbr: bool = False) -> str:
        """
        Generate a random US state

        Args:
            abbr: Whether to return state abbreviation (True) or full name (False)
        """
        if abbr:
            return self.faker.state_abbr()
        else:
            return self.faker.state()

    def state_with_counties(self, abbr: bool = False) -> str:
        """
        Generate a random US state that has defined counties in our dataset

        Args:
            abbr: Whether to return state abbreviation (True) or full name (False)
        """
        state_code = random.choice(list(self.counties_by_state.keys()))
        if abbr:
            return state_code
        else:
            return self.us_states[state_code]

    def zipcode(self) -> str:
        """Generate a random ZIP code"""
        return self.faker.zipcode()

    def country(self) -> str:
        """Generate a random country name"""
        return self.faker.country()

    def county(self, state_code: Optional[str] = None) -> str:
        """
        Generate a county name for the given state

        Args:
            state_code: State code to get county from (required)

        Returns:
            A county name from the specified state or a random one from sample counties
        """
        # If state code provided and we have counties for it
        if state_code and state_code in self.counties_by_state:
            return random.choice(self.counties_by_state[state_code])

        # If state name provided instead of code, try to convert
        if state_code and len(state_code) > 2:
            state_code = self.get_state_code(state_code)
            if state_code in self.counties_by_state:
                return random.choice(self.counties_by_state[state_code])

        # If no state provided or no counties for that state, return random sample county
        return random.choice(self.sample_counties)

    def full_address(self) -> str:
        """Generate a full address"""
        return self.faker.address()

    def latitude(self) -> Decimal:
        """Generate a random latitude"""
        return self.faker.latitude()

    def longitude(self) -> Decimal:
        """Generate a random longitude"""
        return self.faker.longitude()

    def get_state_name(self, state_code: str) -> Optional[str]:
        """Get state name from state code"""
        return self.us_states.get(state_code.upper())

    def get_state_code(self, state_name: str) -> Optional[str]:
        """Get state code from state name"""
        state_name_lower = state_name.lower()
        return self.state_names_to_code.get(state_name_lower)

    def get_counties_for_state(self, state: str) -> List[str]:
        """
        Get all available counties for a state

        Args:
            state: State code or name

        Returns:
            List of counties for the state, or empty list if none available
        """
        # Check if state is a code (2 chars)
        if len(state) == 2:
            state_code = state.upper()
        else:
            # Try to convert state name to code
            state_code = self.get_state_code(state)

        if state_code and state_code in self.counties_by_state:
            return self.counties_by_state[state_code]

        return []
