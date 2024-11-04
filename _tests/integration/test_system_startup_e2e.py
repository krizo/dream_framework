"""Test module for system startup verification with wait conditions."""
import random
import time
from dataclasses import dataclass

import pytest

from core.logger import Log
from core.step import step_start
from core.test_case import TestCase
from helpers.decorators import step, wait_until


@dataclass
class ServiceStatus:
    """Represents service health status."""
    name: str
    is_running: bool = False
    is_healthy: bool = False
    connection_count: int = 0
    error_rate: float = 0.0
    response_time: float = 0.0

    def simulate_improvement(self):
        """Simulate service metrics improvement."""
        if not self.is_running:
            self.is_running = random.random() > 0.3
        elif not self.is_healthy:
            self.is_healthy = random.random() > 0.3
            self.error_rate = random.uniform(0.0, 0.1)
            self.response_time = random.uniform(50, 150)

        if self.is_running and self.is_healthy:
            self.connection_count = min(100, self.connection_count + random.randint(10, 25))


class SystemStartupTest(TestCase):
    """Test case for verifying system startup sequence."""

    def __init__(self):
        super().__init__(
            name="System Startup Verification",
            description="Verify complete system startup sequence and health checks",
            test_suite="System E2E Tests",
            scope="E2E",
            component="System"
        )
        self._services = {}
        self._startup_time = 0

    def _simulate_service_startup(self, service_name: str) -> None:
        """Simulate service startup process."""
        if service_name not in self._services:
            self._services[service_name] = ServiceStatus(name=service_name)

        service = self._services[service_name]
        time.sleep(0.1)  # Simulate work
        service.simulate_improvement()

    @step(content="Initialize {service_name}")
    @wait_until(timeout=2, interval=0.1, reset_logs=True)
    def init_service(self, service_name: str) -> None:
        """Initialize service and wait for it to start."""
        self._simulate_service_startup(service_name)
        service = self._services[service_name]

        assert service.is_running, f"Service {service_name} should be running"
        Log.info(f"Service {service_name} is now running")

        self.add_custom_metric(f"{service_name}_startup_time", time.time() - self._startup_time)

    @step(content="Health check {service_name}")
    @wait_until(timeout=10, interval=0.5, reset_logs=True)
    def check_service_health(self, service_name: str) -> None:
        """Verify service health metrics."""
        self._simulate_service_startup(service_name)
        service = self._services[service_name]

        with step_start("Verify core metrics"):
            assert service.is_healthy, f"Service {service_name} should be healthy"
            assert service.error_rate < 0.1, \
                f"Error rate {service.error_rate:.2f} too high for {service_name}"
            assert service.response_time < 150, \
                f"Response time {service.response_time:.2f}ms too high for {service_name}"
            with step_start("All core metrics OK"):
                pass

        with step_start("Verify connections"):
            assert service.connection_count >= 50, \
                f"Too few connections ({service.connection_count}) for {service_name}"
            with step_start("All connection OK"):
                pass

        # Record metrics
        self.add_custom_metric(f"{service_name}_health_error_rate", service.error_rate)
        self.add_custom_metric(f"{service_name}_health_response_time", service.response_time)
        self.add_custom_metric(f"{service_name}_health_connections", service.connection_count)

    @step
    @wait_until(timeout=3, interval=0.2, reset_logs=True)
    def verify_system_health(self) -> None:
        """Verify system-wide health."""
        with step_start("System health check"):
            for name, service in self._services.items():
                assert service.is_healthy, f"Service {name} not healthy"
                assert service.connection_count >= 50, \
                    f"Service {name} has too few connections ({service.connection_count})"
                with step_start("System health OK"):
                    pass

            self.add_custom_metric("healthy_services", len(self._services))


@pytest.fixture
def system_test():
    """Fixture providing system test instance."""
    return SystemStartupTest()


def test_system_startup_sequence(system_test):
    """
    Test complete system startup sequence.
    Verifies services start up properly and establish required connections.
    """
    system_test._startup_time = time.time()
    services = ["database", "cache", "api", "worker"]

    # Initialize services
    for service in services:
        system_test.init_service(service)

    # Check health of each service
    for service in services:
        system_test.check_service_health(service)

    # Final system verification
    system_test.verify_system_health()

    # Record final metrics
    total_time = time.time() - system_test._startup_time
    Log.info(f"System startup completed in {total_time:.2f} seconds")

    final_metrics = {
        service.name: {
            "error_rate": service.error_rate,
            "response_time": service.response_time,
            "connections": service.connection_count
        }
        for service in system_test._services.values()
    }

    system_test.add_custom_metric("final_system_state", final_metrics)
    system_test.add_custom_metric("total_startup_time", total_time)


def test_service_recovery(system_test):
    """Test system recovery from service issues."""
    system_test._startup_time = time.time()

    # Start database first
    system_test.init_service("database")
    system_test.check_service_health("database")

    # Start API with retries
    @wait_until(timeout=5, interval=0.5, reset_logs=True)
    def start_api_service():
        with step_start("Starting API layer"):
            system_test.init_service("api")
            system_test.check_service_health("api")

    start_api_service()

    # Verify final state
    system_test.verify_system_health()
