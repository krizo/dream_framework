"""Test case configuration parser."""
import ast
from typing import Optional, Set

from core.logger import Log
from .config_parser import ConfigParser


class TestCaseConfig(ConfigParser):
    """Configuration parser for test case settings."""

    SECTION_NAME = "TEST_CASE"

    @classmethod
    def parse_string_list(cls, value_str: str, name: str) -> Optional[Set[str]]:
        """
        Safely parse list of strings from configuration.
        Returns None if parsing fails to distinguish between empty list and invalid config.

        @param value_str: String to parse
        @param name: Name of the configuration for error messages
        @return: Set of validated strings or None if parsing fails
        """
        try:
            # Parse using safe ast.literal_eval
            parsed_value = ast.literal_eval(value_str)

            # Handle explicit empty list
            if not parsed_value:
                return set()

            # Validate it's a list
            if not isinstance(parsed_value, list):
                Log.error(f"{name} must be a list, got: {type(parsed_value)}")
                return None

            # Validate all elements are strings
            if not all(isinstance(x, str) for x in parsed_value):
                Log.error(f"All {name} must be string values")
                return None

            # Convert to set for unique values
            return set(parsed_value)

        except (ValueError, SyntaxError) as e:
            Log.error(f"Failed to parse {name}: {str(e)}")
            return None

    @classmethod
    def get_valid_scopes(cls) -> Optional[Set[str]]:
        """
        Get set of valid test scopes.
        Returns None when no scopes are defined (all scopes are valid).
        Returns empty set when explicitly defined as empty (no scopes are valid).

        @return: Set of valid scope names or None if all scopes are valid
        """
        try:
            # Check iof section and key exist
            if not cls._get_instance().has_option(cls.SECTION_NAME, 'valid_scopes'):
                Log.debug("No valid_scopes defined - all scopes are valid")
                return None

            value = cls.get_value('valid_scopes')
            if value is None:
                Log.debug("valid_scopes is None - all scopes are valid")
                return None

            scopes = cls.parse_string_list(str(value), "valid_scopes")

            # None means parsing error
            if scopes is None:
                return None

            return scopes

        except Exception as e:
            Log.error(f"Error getting valid scopes: {str(e)}")
            return None

    def validate_scope(self, scope: str) -> bool:
        """
        Validate if given scope is allowed.

        @param scope: Scope to validate
        @return: True if scope is valid, False otherwise
        """
        valid_scopes = self.get_valid_scopes()

        # None means all scopes are valid
        if valid_scopes is None:
            return True

        # empty set means none of the scopes is allowed
        if not valid_scopes:
            return False

        # Check if scope is present in valid ones
        if isinstance(scope, str):
            is_valid = scope.lower() in [s.lower() for s in valid_scopes if isinstance(s, str)]
        else:
            is_valid = scope in valid_scopes
        if not is_valid:
            Log.warning(f"Scope '{scope}' rejected (not in valid scopes: {sorted(valid_scopes)})")
        return is_valid
