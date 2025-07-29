# Testing Reference

Comprehensive testing reference for BooksWriter's Test-Driven Development (TDD) approach.

## Testing Philosophy

BooksWriter follows strict TDD methodology with comprehensive test coverage across all 54+ components:

1. **RED** - Write failing tests that define requirements
2. **GREEN** - Implement minimal code to pass tests  
3. **REFACTOR** - Improve code while keeping tests green

## Test Structure

### Test Organization
```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_agents/        # Agent-specific tests
│   ├── test_database/      # Database service tests
│   ├── test_tools/         # Tool validation tests
│   └── test_utils/         # Utility function tests
├── integration/            # Integration and system tests
│   ├── test_multi_agent/   # Multi-agent workflow tests
│   ├── test_database_integration/  # Database integration tests
│   └── test_api_integration/       # API endpoint tests
├── fixtures/               # Test data and fixtures
└── conftest.py            # Pytest configuration and shared fixtures
```

### Test Categories

#### Unit Tests
- **Agent Tests**: Individual agent functionality
- **Tool Tests**: Tool validation and execution
- **Database Tests**: Repository and service layer
- **Utility Tests**: Helper functions and validators

#### Integration Tests
- **Multi-Agent Workflows**: End-to-end agent coordination
- **Database Integration**: Cross-table operations
- **API Integration**: HTTP and WebSocket endpoints

#### TDD Test Examples

```python
# Example: Agent TDD Test
def test_plot_generator_creates_valid_plot():
    """Test that PlotGeneratorAgent generates a valid plot structure"""
    # Arrange
    agent = PlotGeneratorAgent()
    user_message = "Create a fantasy novel with dragons"
    
    # Act
    result = await agent.process_message(user_message)
    
    # Assert
    assert "title" in result
    assert "plot_summary" in result
    assert len(result["plot_summary"]) > 100
    assert "fantasy" in result.get("genre", "").lower()

# Example: Database TDD Test
def test_save_plot_validates_required_fields():
    """Test that save_plot tool requires essential fields"""
    # Arrange
    invalid_plot = {"title": "Test"}  # Missing required fields
    
    # Act & Assert
    with pytest.raises(ValidationError):
        save_plot(invalid_plot)

# Example: Integration TDD Test
def test_complete_book_creation_workflow():
    """Test full workflow: plot -> world -> characters -> author"""
    # Arrange
    orchestrator = OrchestratorAgent()
    request = "Create complete book foundation for sci-fi thriller"
    
    # Act
    result = await orchestrator.process_message(request)
    
    # Assert
    assert result["plot_id"] is not None
    assert result["world_id"] is not None
    assert result["characters_created"] > 0
    assert result["author_id"] is not None
```

## Test Configuration

### pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=90
markers =
    unit: Unit tests
    integration: Integration tests
    database: Database tests
    agents: Agent tests
    tools: Tool tests
    slow: Slow running tests
```

### Test Fixtures (conftest.py)
```python
@pytest.fixture
def test_database():
    """Provide clean test database for each test"""
    db = create_test_database()
    yield db
    cleanup_test_database(db)

@pytest.fixture
def mock_vertex_ai():
    """Mock Vertex AI responses for consistent testing"""
    with patch('src.services.vertex_ai_service') as mock:
        mock.generate_content.return_value = "Test AI response"
        yield mock

@pytest.fixture
def sample_plot_data():
    """Provide consistent plot data for testing"""
    return {
        "title": "Test Fantasy Novel",
        "plot_summary": "A young hero discovers magical powers...",
        "genre": "fantasy",
        "subgenre": "epic_fantasy"
    }
```

## Testing Commands

### Basic Test Execution
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m database      # Database tests only
pytest -m agents        # Agent tests only

# Run specific test files
pytest tests/unit/test_plot_generator_agent.py
pytest tests/integration/test_multi_agent_integration.py
```

### Coverage Testing
```bash
# Generate coverage reports
pytest --cov=src --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=90
```

### Performance Testing
```bash
# Profile test performance
pytest --profile

# Test with timing
pytest --durations=10

# Memory usage testing
pytest --memray
```

## Database Testing

### Test Database Setup
```python
# SQLite test database
TEST_DATABASE_URL = "sqlite:///test_bookswriter.db"

# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean test database after each test"""
    yield
    cleanup_test_data()
```

### Database Test Patterns
```python
def test_database_connection_pooling():
    """Test database connection pool management"""
    pool = DatabaseConnectionPool()
    
    # Test connection acquisition
    conn1 = pool.get_connection()
    conn2 = pool.get_connection()
    
    assert conn1 is not None
    assert conn2 is not None
    assert pool.active_connections == 2
    
    # Test connection release
    pool.release_connection(conn1)
    assert pool.active_connections == 1

def test_migration_rollback():
    """Test database migration rollback functionality"""
    # Apply test migration
    apply_migration("test_migration.sql")
    
    # Verify migration applied
    assert table_exists("test_table")
    
    # Test rollback
    rollback_migration("test_migration.sql")
    assert not table_exists("test_table")
```

## Agent Testing

### Agent Test Patterns
```python
class TestPlotGeneratorAgent:
    """Comprehensive tests for PlotGeneratorAgent"""
    
    @pytest.fixture
    def agent(self):
        return PlotGeneratorAgent()
    
    async def test_generates_fantasy_plot(self, agent):
        """Test fantasy plot generation"""
        message = "Create fantasy plot with dragons"
        result = await agent.process_message(message)
        
        assert result["genre"] == "fantasy"
        assert "dragon" in result["plot_summary"].lower()
    
    async def test_validates_input_parameters(self, agent):
        """Test input validation"""
        with pytest.raises(ValidationError):
            await agent.process_message("")  # Empty message
    
    async def test_handles_ai_service_errors(self, agent, mock_vertex_ai):
        """Test error handling when AI service fails"""
        mock_vertex_ai.generate_content.side_effect = Exception("AI Error")
        
        with pytest.raises(AIServiceError):
            await agent.process_message("Create plot")
```

### Tool Testing
```python
def test_save_plot_tool():
    """Test plot saving tool functionality"""
    plot_data = {
        "title": "Test Plot",
        "plot_summary": "Test summary...",
        "genre": "fantasy"
    }
    
    # Test successful save
    result = save_plot(plot_data)
    assert result["success"] is True
    assert "id" in result
    
    # Test validation
    invalid_data = {"title": ""}  # Invalid title
    with pytest.raises(ValidationError):
        save_plot(invalid_data)
```

## Continuous Integration Testing

### GitHub Actions Workflow
```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run tests
        run: |
          pytest --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Testing Best Practices

### Test Organization
1. **One test per function/feature**
2. **Clear test names describing behavior**
3. **Arrange-Act-Assert pattern**
4. **Independent test execution**
5. **Comprehensive error case testing**

### Mock Usage
```python
# Mock external dependencies
@patch('src.services.vertex_ai_service.VertexAIService')
def test_with_mocked_ai(mock_ai):
    mock_ai.return_value.generate.return_value = "Test response"
    # Test implementation

# Mock database operations
@patch('src.database.supabase_service.SupabaseService')
def test_with_mocked_database(mock_db):
    mock_db.return_value.save_plot.return_value = {"id": "test-id"}
    # Test implementation
```

## Related Documentation

- **[Development Workflow](../guides/development.md)** - Complete TDD workflow
- **[Database Architecture](../architecture/database.md)** - Database testing patterns
- **[Multi-Agent System](../architecture/agents.md)** - Agent testing strategies
- **[Troubleshooting Guide](../guides/troubleshooting.md)** - Test debugging

---

*This reference provides comprehensive testing information for maintaining BooksWriter's high-quality codebase through TDD practices.*