"""Tests for simple base64 Credentials management module."""
import pytest
import tempfile
import yaml
from pathlib import Path

from core.credentials import Credentials


@pytest.fixture
def temp_credentials_dir():
    """Create a temporary directory for test credentials."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def credentials(temp_credentials_dir):
    """Create test credentials instance with temporary files."""
    credentials_path = temp_credentials_dir / 'test_credentials.yml'

    yield Credentials(
        credentials_path=credentials_path
    )


def test_basic_encoding_decoding():
    """Test basic encoding and decoding functionality."""
    plain_text = "secret_password"
    encoded = Credentials.encode(plain_text)

    # Encoded value should be different from plain text
    assert encoded != plain_text

    # Decode back
    decoded = Credentials.decode(encoded)
    assert decoded == plain_text


def test_encode_file(credentials, temp_credentials_dir):
    """Test encoding a credentials file."""
    # Create a source file
    source_path = temp_credentials_dir / 'source_credentials.yml'
    source_data = {
        'database': {
            'username': 'admin',
            'password': 'db_password'
        },
        'api': {
            'key': 'api_secret_key'
        }
    }

    with open(source_path, 'w') as file:
        yaml.dump(source_data, file)

    # Encode the file
    credentials.encode_file(source_path)

    # Verify the encoded file exists
    assert credentials.credentials_path.exists()

    # Verify the encoded file has different content
    with open(credentials.credentials_path, 'r') as file:
        encoded_data = yaml.safe_load(file)

    # Structure should be the same, but values should be different
    assert 'database' in encoded_data
    assert 'api' in encoded_data
    assert 'username' in encoded_data['database']
    assert 'password' in encoded_data['database']
    assert 'key' in encoded_data['api']

    # Values should be encoded
    assert encoded_data['database']['username'] != 'admin'
    assert encoded_data['database']['password'] != 'db_password'
    assert encoded_data['api']['key'] != 'api_secret_key'


def test_get_credentials(credentials, temp_credentials_dir):
    """Test retrieving credentials."""
    # Create and encode a source file
    source_path = temp_credentials_dir / 'source_credentials.yml'
    source_data = {
        'database': {
            'username': 'admin',
            'password': 'db_password'
        },
        'api': {
            'key': 'api_secret_key'
        },
        'users': {
            'user1': {
                'username': 'name1',
                'password': 'pass1'
            },
            'user2': {
                'username': 'name2',
                'password': 'pass2'
            }
        }
    }

    with open(source_path, 'w') as file:
        yaml.dump(source_data, file)

    credentials.encode_file(source_path)

    # Create a new credentials instance to load the encoded file
    new_credentials = Credentials(
        credentials_path=credentials.credentials_path
    )

    # Verify simple values can be retrieved
    assert new_credentials.get('database', 'username') == 'admin'
    assert new_credentials.get('database', 'password') == 'db_password'
    assert new_credentials.get('api', 'key') == 'api_secret_key'

    # Verify nested values can be retrieved
    assert new_credentials.get('users', 'user1', 'username') == 'name1'
    assert new_credentials.get('users', 'user1', 'password') == 'pass1'
    assert new_credentials.get('users', 'user2', 'username') == 'name2'
    assert new_credentials.get('users', 'user2', 'password') == 'pass2'

    # Non-existent values should return None
    assert new_credentials.get('database', 'nonexistent') is None
    assert new_credentials.get('nonexistent', 'key') is None
    assert new_credentials.get('users', 'nonexistent', 'username') is None
    assert new_credentials.get('users', 'user1', 'nonexistent') is None