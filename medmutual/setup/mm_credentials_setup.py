"""Example script showing how to use the simple Credentials class."""
import yaml
from pathlib import Path

from core.common_paths import CONFIG_DIR
from core.credentials import Credentials
from core.logger import Log


def setup_credentials():
    """
    Set up credentials encoding for the first time.
    This would typically be run once during initial setup.
    """
    # Create credentials instance
    creds = Credentials()

    # Create unencoded source file
    source_file = Path(CONFIG_DIR / "credentials.yml")
    if not source_file.exists():
        source_file.touch()

    # Sample credentials
    credentials_data = {
        "users": {
            "krizBober": {
                "username": "userBober",
                "password": "password"
            },
            "bp3sa1": {
                "username": "bp3sa1",
                "password": "password"
            },
            "bp3sa3": {
                "username": "bp3sa1",
                "password": "password"
            }
        }
    }

    # Write unencoded file temporarily
    with open(source_file, "w") as f:
        yaml.dump(credentials_data, f)

    # Encode the file
    creds.encode_file(source_file)

    # Remove unencoded source file
    # source_file.unlink()

    print(f"Credentials encoded and saved to: {creds.credentials_path}")


def use_credentials():
    """
    Example of using credentials in an application.
    """
    # Create credentials instance
    creds = Credentials()

    # Retrieve database credentials
    bp3sa1_user = creds.get("users", "bp3sa1", "username")
    bp3sa1_pass = creds.get("users", "bp3sa1", "password")

def show_encoding_example():
    """
    Show a simple example of encoding and decoding.
    """
    # Sample value
    original = "my_secret_value"

    # Encode
    encoded = Credentials.encode(original)

    # Decode
    decoded = Credentials.decode(encoded)

    # Show results
    print("\nEncoding Example:")
    print(f"  Original: {original}")
    print(f"  Encoded:  {encoded}")
    print(f"  Decoded:  {decoded}")


if __name__ == "__main__":
    print("This script demonstrates how to use the simple Credentials class.")

    # Show encoding example
    # setup_credentials()

    # print("\nUncomment the functions below to run them.")

    use_credentials()

    # WARNING: Only run setup_credentials() once to create your credentials file!
    # After running it, comment it out again to avoid overwriting your credentials.

    # Uncomment to demonstrate using credentials
    # use_credentials()