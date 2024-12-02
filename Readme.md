# 🔬 Test Framework

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](docs/)

## 📋 Table of Contents
- [Overview](#-overview)
- [Key Features](#-key-features)
- [Installation](#-installation)
- [Components](#-components)
- [Getting Started](#-getting-started)
- [Advanced Usage](#-advanced-usage)
- [Analytics](#-analytics)
- [Best Practices](#-best-practices)

## 🔭 Overview

A comprehensive Python testing framework designed for scalable, maintainable, and traceable test automation. Featuring step-by-step execution tracking, detailed logging, and complete test history analysis.

## ✨ Key Features

* 📊 Clear separation between test cases and their executions
* 🔄 Step-by-step test execution tracking
* 📝 Comprehensive logging system
* 💾 Database persistence with multiple dialect support
* 🎯 Custom test properties and metrics
* 📈 Built-in test analytics
* 🔄 Parallel test execution support (pytest-xdist)


## ⚙️ Configuration
The framework uses a flexible configuration system based on config.ini files. Key configuration features include:

### 🔄 wait_until Decorator Settings
```ini
[WAIT_UNTIL]
# Default exceptions to be ignored during wait_until execution
default_exceptions = ["builtins.AssertionError"]
# Default timeout in seconds
default_timeout = 10
# Default interval between retries in seconds
default_interval = 0.5
```

### 🎯 Test Case Properties
```ini
[TEST_CASE]
# Required properties for all test cases
required_properties = ["scope", "component"]
# Valid test scope values
valid_scopes = ["unit", "integration", "e2e", "system"]
```

### The configuration system supports:

* 📖 Readable structure (sections)
* 🔄 Automatic reloading
* 💾 Value caching
* 🛡️ Fallback to defaults
* 🧩 Extensible sections

Example usage with wait_until:
```python
@wait_until(timeout=5, interval=0.1)  # Override defaults
def wait_for_service():
    assert service.is_running, "Service should be running"

@wait_until()  # Use defaults from config
def check_health():
    assert service.is_healthy, "Service should be healthy"
```

## 🧩 Components

### TestCase
Core class for defining test cases with custom properties:

```python
class LoginTest(TestCase):
    def __init__(self):
        super().__init__(
            name="User Authentication Flow",
            description="Verify user login with 2FA",
            test_suite="Authentication",
            scope="E2E",
            component="AuthService"
        )
```

### Steps System

Steps provide a powerful way to track and organize test execution flow. They can be defined in multiple ways, support nesting, and are automatically logged and persisted for later analysis.

#### Step Definition Methods

1. Using context manager:
```python
def test_user_registration(user_test):
    with step_start("Initialize user registration"):
        user_data = load_test_data()
        
        with step_start("Validate input data"):
            with step_start("Check email format"):
                validate_email(user_data["email"])
            
            with step_start("Verify password strength"):
                validate_password(user_data["password"])
        
        with step_start("Create user account"):
            with step_start("Send registration request"):
                response = create_user(user_data)
                user_test.add_custom_metric("user_id", response["id"])
```

2. Using step decorator:
```python
@step(content="Creating user with role {role}")
def create_user_with_role(role: str):
    with step_start("Check role permissions"):
        with step_start("Fetch role details"):
            permissions = get_role_permissions(role)
    
    with step_start("Setup user account"):
        with step_start("Initialize account"):
            user = create_user(role=role)
    
    return user

def test_admin_creation(admin_test):
    admin = create_user_with_role("admin")
    assert admin.role == "admin"
```

#### Log Output

Steps are automatically logged with hierarchical numbering showing the execution structure:

```text
2024-01-15 10:30:42 | STEP     | 1 Initialize user registration
2024-01-15 10:30:42 | STEP     | 1.1   Validate input data
2024-01-15 10:30:42 | STEP     | 1.1.1     Check email format
2024-01-15 10:30:42 | STEP     | 1.1.2     Verify password strength
2024-01-15 10:30:43 | STEP     | 1.2   Create user account
2024-01-15 10:30:43 | STEP     | 1.2.1     Send registration request
2024-01-15 10:30:43 | STEP     | 2 Creating user with role admin
2024-01-15 10:30:43 | STEP     | 2.1   Check role permissions
2024-01-15 10:30:43 | STEP     | 2.1.1     Fetch role details
2024-01-15 10:30:44 | STEP     | 2.2   Setup user account
2024-01-15 10:30:44 | STEP     | 2.2.1     Initialize account
```

#### Database Tracking
Each step is persisted in the database with its:

📝 Hierarchical structure (1, 1.1, 1.1.1, etc.)
⏱️ Execution timing
🔄 Parent-child relationships
✅ Completion status

You can analyze step execution using SQL:

```sql
-- Get step hierarchy for a test execution
SELECT 
    s.hierarchical_number,
    REPEAT('  ', s.indent_level) || s.content as step,
    s.start_time,
    s.completed,
    s.parent_step_id
FROM steps s
WHERE s.execution_record_id = 123
ORDER BY s.sequence_number;

-- Find commonly failing steps
SELECT 
    s.hierarchical_number,
    s.content,
    COUNT(*) as failure_count
FROM steps s
JOIN test_execution_records ter ON s.execution_record_id = ter.id
WHERE ter.result = 'failure'
GROUP BY s.hierarchical_number, s.content
ORDER BY failure_count DESC;
```

Steps provide a clear view of test execution flow and help with:

🔍 Debugging test failures
📊 Performance analysis
📈 Identifying bottlenecks
🎯 Understanding test behavior


### Test Execution Record
The framework automatically manages test execution records through pytest hooks. 
Each test execution record is tracked and stored in the database without manual initialization. 
During test execution, you can add custom metrics:

```python
def test_api_performance(api_test):
    # Test execution record is already initialized by the framework
    
    with step_start("Send request to payment endpoint"):
        start_time = time.time()
        response = requests.post(
            "https://api.example.com/v1/payments",
            json={"amount": 100, "currency": "USD"}
        )
        request_time = time.time() - start_time
        
        # Add performance metrics
        api_test.add_custom_metric("response_time_ms", request_time * 1000)
        api_test.add_custom_metric("response_size_bytes", len(response.content))
        api_test.add_custom_metric("status_code", response.status_code)
    
    with step_start("Process response"):
        data = response.json()
        api_test.add_custom_metric("transaction_id", data["transaction_id"])
        
        # Add business metrics
        api_test.add_custom_metric("payment_method", data["payment_method"])
        api_test.add_custom_metric("processing_fee", data["fee"])
        
    # Framework automatically finalizes and saves the test execution
    assert response.status_code == 200
```




Custom metrics are automatically stored in the database in json format and can be analyzed later for:

📊 API response time tracking
📈 Performance trend monitoring
💰 Processing cost analysis
🔍 Problem investigation



# Test Run Management Implementation 🚀

## Overview
Implementation of a comprehensive test session management system through the `TestRun` class. This is a key framework component that provides a unified way to track and manage test execution.

## Key Features

### 🔄 Singleton Pattern
- Singleton pattern implementation ensuring single TestRun instance per test session
- Safe initialization and state reset
- Multi-worker support in xdist mode

### 📊 Test State Management
- Execution status tracking (STARTED, COMPLETED, CANCELLED, ERROR)
- Execution time measurement and duration calculation
- Automatic CI/local environment detection

### 🌍 Environment Configuration
- Flexible configuration through parameters or config files
- Multiple environment support (dev/staging/prod)
- Automatic CI/CD pipeline detection

### 📝 Logging System
- Hierarchical logging system with timestamps
- Separate logs for each TestRun
- xdist mode logging support
- Enhanced test execution records logging with detailed metrics and status tracking

### 🔁 pytest-xdist Support
- TestRun coordination between workers
- TestRun ID sharing
- Logging synchronization

### 💾 Persistence
- Automatic state persistence to database
- TestExecutionRecord relationships
- Metrics and statistics tracking
- Test run status management (STARTED, COMPLETED, CANCELLED, ERROR)



### 🌍 Environment Configuration

The framework provides a flexible environment configuration system through the `TestEnvironment` class.
Configure different test environments (dev, staging, prod) using YAML configuration:

```python
from core.environments import TestEnvironment

# Direct usage
env = TestEnvironment("production")
hostname = env.get_property("hostname")
db_config = env.get_property("database")

# Or using environment variable
# export TEST_ENVIRONMENT=staging
env = TestEnvironment()  # Uses TEST_ENVIRONMENT value
```

Create strongly-typed configurations:

```python
@dataclass
class DatabaseConfig:
    server: str
    name: str

@dataclass
class AppConfig:
    hostname: str
    database: DatabaseConfig
    
    @classmethod
    def from_environment(cls, env_name: str) -> 'AppConfig':
        env = TestEnvironment(env_name)
        return cls(
            hostname=env.get_property("hostname"),
            database=DatabaseConfig(
                server=env.get_property("database")["server"],
                name=env.get_property("database")["name"]
            )
        )

# Usage
config = AppConfig.from_environment("production")
print(f"Connecting to {config.database.server}...")
```

Configuration file (`config/environments.yml`):
```yaml
production:
  hostname: foo.example.com
  database:
    server: db.example.com
    name: myapp_prod

staging:
  hostname: staging.example.com
  database:
    server: db-staging.example.com
    name: myapp_staging
```

Key features:
- 📁 Central YAML configuration
- 🔄 Auto-detection via `TEST_ENVIRONMENT`
- 🏗️ Support for complex configuration structures
- 🔒 Separation of sensitive datae

## 🚀 Getting Started

1. Create your test case:
```python
class PaymentTest(TestCase):
    def __init__(self):
        super().__init__(
            name="Payment Processing",
            scope="Integration",
            component="PaymentGateway"
        )
```

2. Define test steps:
```python
@step(content="Processing payment {amount}")
def process_payment(amount: float):
    with step_start("Validating amount"):
        validate_amount(amount)
    
    with step_start("Charging card"):
        charge_card(amount)
```

3. Write your test:
```python
def test_payment_flow(payment_test):
    with step_start("Initialize payment"):
        payment = initialize_payment(100.00)
    
    process_payment(payment.amount)
    
    with step_start("Verify completion"):
        assert payment.status == "completed"
```

## 🔧 Advanced Usage

### Custom Properties
Define custom test properties that can be used in all you tests.
Force their usage in all tests by specifying the `required` flag.

```python
class TestCaseProperties(Enum):
    PRIORITY = PropertyInfo(name="PRIORITY", type=int, required=True)
    PLATFORM = PropertyInfo(name="PLATFORM", type=str, required=True)
    TAGS = PropertyInfo(name="TAGS", type=list, required=False)
```


## 📊 Test Reports 

The framework now includes a powerful test reporting system that generates detailed HTML reports after test execution.

### ✨ Features

#### 📝 One Pager Report
- 📊 Complete test run overview
- 📈 Interactive metrics dashboard
- 📋 Test suite summaries
- 📝 Detailed execution records
- 📊 Steps and custom metrics visualization
- 🚀 Support for large test sets

#### 🎨 Themes
Five built-in themes:
- 🌟 Modern (default)
- ⚡ Minimalist  
- 🌙 Dark
- 🎮 Retro
- 📚 Classic

#### ⚙️ Configuration
```ini
[REPORT]
# Report type (one_pager/drilldown)
type = one_pager

# Sections to include
sections = main_summary,test_suite_summary,test_case_summary

# Show charts and logs
show_charts = true
show_logs = true

# Theme selection
css_template = modern
```

#### ⚠️ Known Issues

- 🐛 Step completion status sometimes incorrectly marked (fix coming soon)
- 🎨 Chart colors may have low contrast in dark theme

#### 🔜 Following Steps

- 📊 Drilldown report implementation
- 📈 Interactive charts and visualizations
- 🔍 Enhanced filtering capabilities
- 📥 Report export functionality

## 📊 Analytics

### SQL Analysis Examples

#### Test Execution Statistics
```sql
-- Overall test execution statistics by test case
SELECT 
    tc.name as test_name,
    tc.test_suite,
    COUNT(*) as total_executions,
    SUM(CASE WHEN ter.result = 'passed' THEN 1 ELSE 0 END) as passed,
    SUM(CASE WHEN ter.result = 'failed' THEN 1 ELSE 0 END) as failed,
    AVG(ter.duration) as avg_duration,
    MIN(ter.duration) as min_duration,
    MAX(ter.duration) as max_duration
FROM test_cases tc
JOIN test_execution_records ter ON tc.id = ter.test_case_id
GROUP BY tc.id, tc.name, tc.test_suite
ORDER BY total_executions DESC;

-- Test stability by environment
SELECT 
    tc.name,
    ter.environment,
    COUNT(*) as total_runs,
    ROUND(AVG(CASE WHEN ter.result = 'passed' THEN 100.0 ELSE 0 END), 2) as success_rate,
    AVG(ter.duration) as avg_duration
FROM test_cases tc
JOIN test_execution_records ter ON tc.id = ter.test_case_id
GROUP BY tc.name, ter.environment
ORDER BY success_rate DESC;
```

### Performance Analysis
```sql
-- Performance trends over time with custom metrics
WITH performance_metrics AS (
    SELECT 
        ter.test_case_id,
        ter.start_time::date as test_date,
        ter.environment,
        AVG(CAST(cm.value->>'processing_time_ms' AS FLOAT)) as avg_response_time,
        AVG(CAST(cm.value->>'memory_usage_mb' AS FLOAT)) as avg_memory_usage
    FROM test_execution_records ter
    JOIN custom_metrics cm ON ter.id = cm.test_execution_id
    WHERE cm.name IN ('processing_time_ms', 'memory_usage_mb')
        AND ter.result = 'passed'
    GROUP BY ter.test_case_id, test_date, ter.environment
)
SELECT 
    tc.name,
    pm.test_date,
    pm.environment,
    pm.avg_response_time,
    pm.avg_memory_usage
FROM performance_metrics pm
JOIN test_cases tc ON pm.test_case_id = tc.id
ORDER BY tc.name, pm.environment, pm.test_date;
```

### Python Analysis Examples

#### Test Stability Analysis
```python
def analyze_test_stability(test_case_id: int, period_days: int = 30):
    """Analyze test stability across environments."""
    db = AutomationDatabaseManager.get_database()
    
    with db.session_scope() as session:
        executions = session.query(TestExecutionRecordModel)\
            .filter(
                TestExecutionRecordModel.test_case_id == test_case_id,
                TestExecutionRecordModel.start_time >= datetime.now() - timedelta(days=period_days)
            ).all()
        
        # Group by environment
        env_stats = defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0})
        perf_stats = defaultdict(list)
        
        for execution in executions:
            env = execution.environment
            env_stats[env]["total"] += 1
            env_stats[env]["passed" if execution.result == 'passed' else "failed"] += 1
            
            if execution.result == 'passed':
                # Collect performance metrics for successful runs
                processing_time = next(
                    (m.value for m in execution.custom_metrics 
                     if m.name == 'processing_time_ms'),
                    None
                )
                if processing_time:
                    perf_stats[env].append(float(processing_time))
        
        # Calculate statistics
        results = []
        for env, stats in env_stats.items():
            success_rate = (stats["passed"] / stats["total"]) * 100
            perf_data = perf_stats[env]
            
            results.append({
                "environment": env,
                "total_executions": stats["total"],
                "success_rate": success_rate,
                "avg_processing_time": np.mean(perf_data) if perf_data else None,
                "p95_processing_time": np.percentile(perf_data, 95) if perf_data else None
            })
        
        return results
```

#### Performance Trend Analysis
```python
def analyze_performance_trends(test_case_id: int, metric_name: str = 'processing_time_ms'):
    """Analyze performance trends over time."""
    db = AutomationDatabaseManager.get_database()
    
    with db.session_scope() as session:
        # Get execution records with metrics
        executions = session.query(
            TestExecutionRecordModel,
            CustomMetricModel
        ).join(
            CustomMetricModel
        ).filter(
            TestExecutionRecordModel.test_case_id == test_case_id,
            TestExecutionRecordModel.result == 'passed',
            CustomMetricModel.name == metric_name
        ).order_by(
            TestExecutionRecordModel.start_time
        ).all()
        
        # Group by environment and calculate trends
        env_data = defaultdict(list)
        for execution, metric in executions:
            env_data[execution.environment].append({
                'timestamp': execution.start_time,
                'value': float(metric.value)
            })
        
        # Calculate trends
        trends = {}
        for env, data in env_data.items():
            values = [d['value'] for d in data]
            trends[env] = {
                'mean': np.mean(values),
                'median': np.median(values),
                'p95': np.percentile(values, 95),
                'trend_slope': np.polyfit(range(len(values)), values, 1)[0],
                'samples': len(values)
            }
        
        return trends
```

## 💡 Best Practices

During implementing your tests remember about few things that will help you keep them stable, well-structured and organized: 

1. **Step Organization**
   * Keep steps focused and atomic
   * Use meaningful step descriptions
   * Maintain proper nesting levels
   * Add relevant metrics at each step

2. **Test Structure**
   * Separate test logic from test data
   * Use fixtures for common setup
   * Follow the AAA pattern (Arrange, Act, Assert)
   * Implement proper cleanup

3. **Metrics & Logging**
   * Log meaningful events
   * Add business-relevant metrics
   * Use appropriate log levels
   * Include context in error logs

4. **Analytics & Monitoring**
   * Monitor test stability regularly
   * Track performance trends
   * Analyze failure patterns
   * Set up alerts for degradation

K
I dodaj sekcję do Readme apropos testów - rodzaje, co pokrywają itd


## 🧪 Testing

The framework itself is thoroughly tested using pytest. Test suite covers:

### 🔬 Test Types
* 🧩 **Unit Tests** - individual components testing
* 🔗 **Integration Tests** - component interaction verification
* 🔄 **E2E Tests** - complete workflow validation
* 💾 **Database Tests** - persistence and SQL dialect compatibility

### 📊 Coverage Areas
* 🎯 Core functionality
  * Test case management
  * Execution record handling
  * Test run lifecycle
  * Database operations
* 🔄 Framework features
  * Step system
  * Wait conditions
  * Custom metrics
  * Environment handling
* 📝 Plugins and extensions
  * pytest plugin integration
  * xdist compatibility
  * Logger customization

### ⚙️ Running Tests
```bash
# Run all tests
pytest -v

# Run specific test category
pytest test_test_run.py
pytest test_steps*.py
pytest test_*_e2e.py

## Known Issues 🐛

Running tests with xdist in single worker mode (-n1) causes issues with TestRun initialization and database management. However, using single worker mode with xdist doesn't provide any benefits over standard pytest execution.

