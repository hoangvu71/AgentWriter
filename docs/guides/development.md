# Development Workflow Guide

This guide outlines BooksWriter's Test-Driven Development (TDD) methodology and development practices.

## 🎯 Development Philosophy

BooksWriter follows strict TDD methodology with these core principles:

1. **RED** - Write failing tests that define requirements
2. **GREEN** - Implement minimal code to pass tests  
3. **REFACTOR** - Improve code while keeping tests green
4. **QUALITY** - All 54+ components have comprehensive test coverage
5. **SIMPLICITY** - No overengineering or unnecessary complexity

## 🏗️ TDD Methodology

### The RED-GREEN-REFACTOR Cycle

#### 1. RED Phase: Write Failing Tests
```python
# Example: test_plot_generator_agent.py
def test_plot_generator_creates_valid_plot():
    """Test that PlotGeneratorAgent generates a valid plot structure"""
    # Arrange
    agent = PlotGeneratorAgent(config)
    request = AgentRequest(
        session_id="test-session",
        user_id="test-user",
        content="Create a fantasy plot"
    )
    
    # Act
    response = await agent.process_request(request)
    
    # Assert
    assert response.success is True
    assert "title" in response.content
    assert "plot_summary" in response.content
    assert len(response.content["plot_summary"]) > 100
```

#### 2. GREEN Phase: Make Tests Pass
```python
# Minimal implementation to make test pass
class PlotGeneratorAgent(BaseAgent):
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        # Minimal implementation
        return AgentResponse(
            success=True,
            content={
                "title": "Basic Fantasy Plot",
                "plot_summary": "A hero embarks on a quest to save the kingdom from an ancient evil, facing many challenges and growing stronger along the way."
            }
        )
```

#### 3. REFACTOR Phase: Improve Code Quality
```python
# Enhanced implementation with proper logic
class PlotGeneratorAgent(BaseAgent):
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        # Parse request parameters
        parameters = self._extract_plot_parameters(request.content)
        
        # Generate plot using AI
        plot_data = await self._generate_plot_content(parameters)
        
        # Validate and format response
        validated_plot = self._validate_plot_structure(plot_data)
        
        # Save to database using tools
        await self._save_plot_to_database(validated_plot, request)
        
        return AgentResponse(success=True, content=validated_plot)
```

## 🧪 Testing Strategy

### Test Types and Coverage

#### 1. Unit Tests (`tests/unit/`)
Test individual components in isolation:

```python
# test_base_agent.py
class TestBaseAgent:
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        
    def test_prepare_message_async(self):
        """Test _prepare_message method is async"""
        
    def test_conversation_context_loading(self):
        """Test conversation context is loaded properly"""
```

#### 2. Integration Tests (`tests/integration/`)
Test component interactions:

```python
# test_multi_agent_workflows.py
class TestMultiAgentWorkflows:
    async def test_plot_to_author_workflow(self):
        """Test plot generation followed by author creation"""
        
    async def test_database_integration(self):
        """Test agents save data to database correctly"""
```

#### 3. End-to-End Tests (`tests/e2e/`)
Test complete user workflows:

```python
# test_agent_workflows.py
class TestAgentWorkflows:
    async def test_complete_book_creation_workflow(self):
        """Test full workflow: plot → author → world → characters"""
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/ -v                    # Unit tests
pytest tests/integration/ -v             # Integration tests  
pytest tests/e2e/ -v                     # End-to-end tests

# Run tests for specific components
pytest tests/unit/test_plot_generator_agent.py -v
pytest tests/unit/test_base_repository.py -v
pytest tests/unit/test_connection_pool.py -v

# Run tests with coverage
pytest --cov=src --cov-report=html
```

## 🏛️ Code Architecture Patterns

### Agent Development Pattern

1. **Inherit from BaseAgent**:
   ```python
   class NewAgent(BaseAgent):
       def __init__(self, config: Configuration):
           super().__init__(config)
           # Agent-specific initialization
   ```

2. **Implement _prepare_message (async)**:
   ```python
   async def _prepare_message(self, request: AgentRequest) -> str:
       # Load conversation context
       context = await self._conversation_manager.get_conversation_context(
           request.session_id, request.user_id
       )
       
       # Prepare agent-specific message
       message = f"You are a {self.agent_name} agent..."
       
       return message
   ```

3. **Use Tools for Database Operations**:
   ```python
   # Use tools instead of direct database calls
   plot_data = {
       "title": "Generated Title",
       "plot_summary": "Generated summary..."
   }
   
   # Save using tool
   tool_result = await self.use_tool("save_plot", plot_data)
   ```

### Repository Pattern

```python
class PlotRepository(BaseRepository):
    async def create_plot(self, plot_data: dict) -> str:
        """Create a new plot with validation"""
        # Validate input
        validated_data = self._validate_plot_data(plot_data)
        
        # Execute database operation
        plot_id = await self._execute_insert("plots", validated_data)
        
        return plot_id
    
    async def get_plots_with_authors_batch(self, user_id: str) -> List[dict]:
        """Get plots with authors to avoid N+1 queries"""
        query = """
        SELECT p.*, a.author_name, a.pen_name
        FROM plots p
        LEFT JOIN authors a ON p.id = a.plot_id
        WHERE p.user_id = $1
        ORDER BY p.created_at DESC
        """
        return await self._execute_query(query, [user_id])
```

### Service Layer Pattern

```python
class ContentSavingService:
    def __init__(self, database_adapter, validation_service):
        self.database = database_adapter
        self.validator = validation_service
    
    async def save_plot(self, plot_data: dict, session_info: dict) -> dict:
        """Save plot with comprehensive validation"""
        # Validate input
        validated_plot = await self.validator.validate_plot(plot_data)
        
        # Add metadata
        plot_record = {
            **validated_plot,
            "user_id": session_info["user_id"],
            "session_id": session_info["session_id"],
            "created_at": datetime.utcnow()
        }
        
        # Save to database
        result = await self.database.save_plot(plot_record)
        
        return result
```

## 🛠️ Development Tools and Scripts

### Database Management
```bash
# Create new migration
python scripts/setup/create_migration.py "description_of_changes"

# Check database tables
python scripts/database/check_tables.py

# Verify migration status
python scripts/maintenance/verify_migration.py
```

### Code Quality
```bash
# TDD compliance report
python scripts/maintenance/tdd_compliance_report.py

# Run TDD enforcement framework
python scripts/maintenance/TDD_ENFORCEMENT_FRAMEWORK.py

# Validate GitHub Actions
python -m pytest tests/unit/test_github_actions_validation.py
```

### Development Environment
```bash
# Start development server
python main.py

# Start with specific configuration
ADK_SERVICE_MODE=development python main.py

# Debug mode with detailed logging
LOG_LEVEL=DEBUG python main.py
```

## 🔧 Adding New Features

### Step-by-Step Process

#### 1. Write Tests First (RED)
```python
# tests/unit/test_new_feature.py
def test_new_feature_functionality():
    """Test new feature works as expected"""
    # Test should fail initially
    assert new_feature_function() == expected_result
```

#### 2. Create Minimal Implementation (GREEN)
```python  
# src/new_feature.py
def new_feature_function():
    """Minimal implementation to make test pass"""
    return expected_result  # Hardcoded initially
```

#### 3. Refactor and Enhance (REFACTOR)
```python
def new_feature_function():
    """Proper implementation with full logic"""
    # Real implementation here
    result = complex_processing()
    return result
```

#### 4. Add Integration Tests
```python
# tests/integration/test_new_feature_integration.py
async def test_new_feature_with_database():
    """Test feature works with database"""
    # Test database integration
```

#### 5. Update Documentation
- Update relevant documentation files
- Add inline code documentation  
- Update API documentation if needed
- Ensure CLAUDE.md reflects architecture changes

### Adding New Agents

1. **Create Agent Class**:
   ```python
   # src/agents/new_agent.py
   class NewAgent(BaseAgent):
       async def _prepare_message(self, request: AgentRequest) -> str:
           # Implementation
   ```

2. **Add to AgentFactory**:
   ```python
   # src/agents/agent_factory.py
   def create_agent(agent_type: str, config: Configuration) -> BaseAgent:
       if agent_type == "new_agent":
           return NewAgent(config)
   ```

3. **Create TDD Tests**:
   ```python
   # tests/unit/test_new_agent.py
   class TestNewAgent:
       def test_agent_initialization(self):
           """Test agent initializes correctly"""
   ```

4. **Update Orchestrator** (if needed):
   ```python
   # Add routing logic for new agent
   # Update tool coordination if needed
   ```

## 🔍 Code Quality Standards

### Python Code Style
- Follow PEP 8 for Python code
- Use type hints for all function parameters and returns
- Async functions for I/O operations
- Comprehensive error handling with logging

### Example of Well-Structured Code
```python
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ExampleService:
    """Example service following project standards"""
    
    def __init__(self, config: Configuration) -> None:
        self.config = config
        self._initialized = False
    
    async def process_data(
        self, 
        input_data: Dict[str, Any], 
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Process input data with validation and error handling.
        
        Args:
            input_data: The data to process
            user_id: User identifier for logging
            
        Returns:
            Processed data or None if processing fails
            
        Raises:
            ValidationError: If input data is invalid
        """
        try:
            # Validate input
            validated_data = self._validate_input(input_data)
            
            # Process data
            logger.info(f"Processing data for user {user_id}")
            result = await self._async_processing(validated_data)
            
            return result
            
        except ValidationError as e:
            logger.error(f"Validation failed for user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing data: {e}")
            return None
    
    def _validate_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data structure"""
        # Validation logic
        return data
    
    async def _async_processing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform async processing"""
        # Async processing logic
        return data
```

### Documentation Standards
- All public methods have docstrings
- Type hints for parameters and return values
- Clear descriptions of purpose and behavior
- Examples for complex functions

## 🔄 Git Workflow

### Commit Message Format
Follow conventional commit format:
```
type(scope): description

feat(agents): add new character development agent
fix(database): resolve connection pool timeout issue
docs(guides): update development workflow documentation
test(integration): add multi-agent workflow tests
refactor(repositories): optimize batch operations
```

### Branch Naming
```
feature/agent-enhancement
fix/database-connection-issue
docs/reorganize-documentation
test/add-integration-tests
```

### Development Process
1. Create feature branch from main
2. Write tests first (TDD)
3. Implement feature
4. Ensure all tests pass
5. Update documentation
6. Create pull request
7. Code review
8. Merge to main

## 🚨 Common Development Issues

### 1. Async Method Issues
**Problem**: Forgetting to make agent methods async
**Solution**: All agent `_prepare_message` methods must be async

```python
# Wrong
def _prepare_message(self, request: AgentRequest) -> str:
    return "message"

# Correct  
async def _prepare_message(self, request: AgentRequest) -> str:
    context = await self._load_context()
    return "message"
```

### 2. Tool Interface Misalignment
**Problem**: Agent instructions don't match tool parameters
**Solution**: Ensure parameter names and types match exactly

```python
# Tool definition
@tool
def save_plot(title: str, plot_summary: str, genre: str) -> dict:
    """Save plot with required parameters"""

# Agent must use matching parameters
plot_data = {
    "title": generated_title,
    "plot_summary": generated_summary, 
    "genre": extracted_genre
}
```

### 3. Database Schema Consistency
**Problem**: SQLite and Supabase schemas differ
**Solution**: Keep schemas synchronized using migrations

### 4. UUID Format Errors
**Problem**: Mixing UUID strings and objects
**Solution**: Use string UUIDs consistently

```python
# Correct
user_id = str(uuid.uuid4())

# Wrong
user_id = uuid.uuid4()  # UUID object
```

## 📚 Resources and References

### Internal Documentation
- [Architecture Overview](../architecture/overview.md) - System design
- [Multi-Agent System](../architecture/agents.md) - Agent coordination  
- [Database Architecture](../architecture/database.md) - Database design
- [Testing Philosophy](../reference/testing.md) - Testing approaches

### External Resources
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Google ADK Documentation](https://developers.google.com/vertex-ai/docs/agent-builder)

## 🎯 Key Takeaways

1. **Always write tests first** - This is non-negotiable
2. **Keep it simple** - Avoid overengineering
3. **Ask for clarification** - Never assume requirements
4. **Focus on root causes** - Fix core issues, not symptoms
5. **Maintain test coverage** - All components must have tests
6. **Follow patterns** - Use established architectural patterns
7. **Document changes** - Update documentation with code changes

---

This development workflow ensures high code quality, maintainability, and reliability while supporting rapid development of new features and agents in the BooksWriter system.