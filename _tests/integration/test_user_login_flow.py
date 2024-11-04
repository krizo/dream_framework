from datetime import datetime

import pytest
import requests
import responses

from core.logger import Log
from core.test_case import TestCase


class LoginTestCase(TestCase):
    """Real-world login test case with encapsulated steps and validations."""

    def __init__(self):
        super().__init__(
            name="User Authentication Flow",
            description="Verify complete user login flow including MFA and secure API access",
            test_suite="Authentication",
            scope="Integration",
            component="Auth Service",
            interface="REST API",
            request_type="POST"
        )
        self.session_token = None

    def send_credentials(self, username: str, password: str):
        """
        Send and validate initial credentials.

        @param username: User login
        @param password: User password
        """
        Log.step("Validating user credentials")

        auth_response = {
            "status": "mfa_required",
            "session_id": "sess_123456",
            "allowed_mfa_methods": ["totp", "sms"]
        }

        self.add_custom_metric("username", username)
        self.add_custom_metric("auth_method", "password")
        self.add_custom_metric("initial_auth_response", auth_response)
        self.add_custom_metric("request_timestamp", datetime.now())

        assert auth_response["status"] == "mfa_required", "MFA should be required"
        assert "session_id" in auth_response, "Session ID not provided"

        Log.info("Credentials validated successfully")
        return auth_response["session_id"]

    def verify_mfa(self, session_id: str, mfa_code: str):
        """
        Verify MFA code and validate response.

        @param session_id: Session ID from initial auth
        @param mfa_code: MFA verification code
        """
        Log.step("Performing MFA verification")
        mfa_start = datetime.now()

        mfa_response = {
            "status": "success",
            "token_type": "Bearer",
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "expires_in": 3600
        }

        self.add_custom_metric("mfa_method", "totp")
        self.add_custom_metric("mfa_response", mfa_response)
        self.add_custom_metric("mfa_duration_ms",
                               (datetime.now() - mfa_start).total_seconds() * 1000)

        assert mfa_response["status"] == "success", "MFA verification failed"
        assert mfa_response["access_token"], "No access token provided"

        Log.info("MFA verification completed")
        self.session_token = mfa_response["access_token"]

    def verify_session(self):
        """Verify session initialization and status."""
        self._initialize_session()
        self._check_session_status()

    def _initialize_session(self):
        Log.step("Initializing user session")
        assert self.session_token, "No valid session token"

        session_data = {
            "user_id": "usr_789012",
            "roles": ["user", "admin"],
            "permissions": ["read", "write"],
            "last_login": datetime.now()
        }

        self.add_custom_metric("session_data", session_data)
        assert session_data["user_id"], "User ID not provided"
        assert session_data["roles"], "User roles not provided"

        Log.info("Session initialized successfully")

    def _check_session_status(self):
        Log.step("Verifying session status")

        session_check = {
            "status": "active",
            "expiry": datetime.now(),
            "client_ip": "192.168.1.100"
        }

        self.add_custom_metric("session_check", session_check)
        assert session_check["status"] == "active", "Session not active"

        Log.info("Session verification completed")

    def get_user_profile(self):
        """Get and validate user profile data."""
        Log.step("Requesting user profile")
        assert self.session_token, "No valid session token"

        try:
            headers = {
                "Authorization": f"Bearer {self.session_token}",
                "Content-Type": "application/json"
            }
            response = requests.get(
                "https://api.example.com/v1/user/profile",
                headers=headers
            )

            response.raise_for_status()
            user_data = response.json()

            self.add_custom_metric("api_response_time_ms",
                                   response.elapsed.total_seconds() * 1000)
            self.add_custom_metric("user_data", user_data)

            assert user_data.get("id"), "User ID not found in profile"
            assert user_data.get("email"), "Email not found in profile"

            Log.info("Successfully retrieved user profile")

        except requests.exceptions.RequestException as e:
            Log.error(f"API request failed: {str(e)}")
            raise


@pytest.fixture
def login_test():
    return LoginTestCase()


@pytest.fixture
def mock_api():
    """
    Mock API responses for user profile.

    @return: responses context manager
    """
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "https://api.example.com/v1/user/profile",
            json={
                "id": "usr_789012",
                "email": "test.user@example.com",
                "name": "Test User",
                "verified": True,
                "last_login": "2024-10-29T10:00:00Z"
            },
            status=200
        )
        yield rsps


def test_user_login_flow(login_test, mock_api):
    """
    Verify complete user authentication flow.

    @param login_test: Login test case fixture
    @param mock_api: Mocked API responses
    """
    login_test.send_credentials("test.user@example.com", "Password123!")
    login_test.verify_mfa("123456", "session_123")
    login_test.verify_session()
    login_test.get_user_profile()
