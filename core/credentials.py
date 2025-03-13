"""Simple credentials management module with base64 encoding."""
import base64
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union

from core.common_paths import CONFIG_DIR
from core.logger import Log


class Credentials:
    """
    Very simple credentials manager for storing and retrieving sensitive data.

    This class uses basic base64 encoding to obfuscate credentials - it is not
    meant for high security, but rather to avoid credentials being visible in plaintext.

    Usage example:
        # Initialize credentials
        creds = Credentials()

        # Retrieve a credential
        db_password = creds.get("database", "password")

        # Use the credential
        db_connection = connect_to_db(password=db_password)
    """

    # Default path
    DEFAULT_CREDENTIALS_PATH = CONFIG_DIR / 'credentials.yml'

    def __init__(self, credentials_path: Optional[Union[str, Path]] = None):
        """
        Initialize credentials manager.

        Args:
            credentials_path: Path to the credentials YAML file
        """
        self.credentials_path = Path(credentials_path) if credentials_path else self.DEFAULT_CREDENTIALS_PATH

        # Load credentials
        self._credentials = {}
        self._load_credentials()

    def _load_credentials(self) -> None:
        """
        Load and decode credentials from YAML file.
        """
        if not self.credentials_path.exists():
            Log.info(f"Credentials file not found at: {self.credentials_path}")
            return

        try:
            with open(self.credentials_path, 'r') as file:
                self._credentials = yaml.safe_load(file) or {}

            Log.info(f"Successfully loaded credentials from: {self.credentials_path}")
        except Exception as e:
            Log.error(f"Error loading credentials: {str(e)}")

    def get(self, category: str, name: str, *nested_keys) -> Optional[str]:
        """
        Get a credential value by category and name, with support for nested properties.

        Args:
            category: Category of the credential (e.g., "database", "api")
            name: Name of the credential (e.g., "password", "key")
            *nested_keys: Optional nested keys for accessing nested dictionary structures

        Returns:
            The credential value or None if not found

        Examples:
            # Simple key access
            password = creds.get("database", "password")

            # Nested key access
            # For structure: {"users": {"user1": {"username": "name1", "password": "pass1"}}}
            user1_password = creds.get("users", "user1", "password")
        """
        try:
            # Get category
            category_data = self._credentials.get(category)
            if not category_data:
                return None

            # Get encoded value
            encoded_value = category_data.get(name)
            if encoded_value is None:
                return None

            # If there are no nested keys, decode and return
            if not nested_keys:
                try:
                    decoded = self._decode(encoded_value)
                    return decoded
                except Exception as e:
                    Log.error(f"Error decoding credential {category}.{name}: {str(e)}")
                    return None

            # For nested keys, decode first, then parse
            try:
                # Decode and parse as YAML
                decoded_value = self._decode(encoded_value)
                parsed_value = yaml.safe_load(decoded_value)

                if not isinstance(parsed_value, dict):
                    return None

                # Navigate through nested keys
                current = parsed_value
                for key in nested_keys:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        return None

                return current
            except Exception as e:
                Log.error(f"Error accessing nested credential: {str(e)}")
                return None

        except Exception as e:
            Log.error(f"Error retrieving credential: {str(e)}")
            return None

    @staticmethod
    def _encode(value: str) -> str:
        """Internal method to encode a value using base64."""
        try:
            return base64.b64encode(value.encode('utf-8')).decode('utf-8')
        except Exception as e:
            Log.error(f"Encoding error: {str(e)}")
            return value

    @staticmethod
    def _decode(encoded_value: str) -> str:
        """Internal method to decode a base64 encoded value."""
        try:
            return base64.b64decode(encoded_value.encode('utf-8')).decode('utf-8')
        except Exception as e:
            Log.error(f"Decoding error: {str(e)}")
            return encoded_value

    @classmethod
    def encode(cls, value: str) -> str:
        """
        Encode a value using base64.

        Args:
            value: Plain text value to encode

        Returns:
            Base64 encoded value
        """
        return cls._encode(value)

    @classmethod
    def decode(cls, encoded_value: str) -> str:
        """
        Decode a base64 encoded value.

        Args:
            encoded_value: Base64 encoded value

        Returns:
            Decoded plain text value
        """
        return cls._decode(encoded_value)

    def encode_file(self, source_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> None:
        """
        Encode a credentials YAML file.

        Args:
            source_path: Path to the plain text YAML file
            output_path: Path to save the encoded file (defaults to self.credentials_path)

        This method should be called once to encode your credentials file.
        The source file should be in the format:

        ```yaml
        database:
          username: admin
          password: secretpassword
        api:
          key: api_secret_key
        ```
        """
        source_path = Path(source_path)
        if not source_path.exists():
            Log.error(f"Source file not found: {source_path}")
            return

        output_path = Path(output_path) if output_path else self.credentials_path

        try:
            # Load source file
            with open(source_path, 'r') as file:
                source_data = yaml.safe_load(file) or {}

            # Encode all values
            encoded_data = {}
            for category, creds in source_data.items():
                encoded_data[category] = {}
                for name, value in creds.items():
                    if isinstance(value, dict):
                        # For nested dictionaries, convert to YAML string and then encode
                        yaml_str = yaml.dump(value)
                        encoded_value = self._encode(yaml_str)
                    else:
                        # For simple values, just encode as string
                        encoded_value = self._encode(str(value))

                    encoded_data[category][name] = encoded_value

            # Save encoded file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as file:
                yaml.dump(encoded_data, file, default_flow_style=False)

            Log.info(f"Encoded credentials saved to: {output_path}")
        except Exception as e:
            Log.error(f"Failed to encode credentials file: {str(e)}")