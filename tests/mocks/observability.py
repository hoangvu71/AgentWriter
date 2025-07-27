"""
Mock observability module for testing without OpenTelemetry dependencies.
"""
from typing import Any, Dict, Optional, List
from contextlib import contextmanager
from unittest.mock import MagicMock


class MockObservability:
    """Mock implementation of observability functionality"""
    
    def __init__(self):
        self.enabled = False
        self.service_name = "test-service"
        self.traces = []
        self.spans = []
    
    @contextmanager
    def trace_agent_execution(self, agent_name: str, operation: str, **kwargs):
        """Mock trace context for agent execution"""
        span = MagicMock()
        span.agent_name = agent_name
        span.operation = operation
        span.attributes = kwargs
        self.spans.append(span)
        
        yield span
    
    @contextmanager
    def trace_llm_interaction(self, model_name: str, operation: str, **kwargs):
        """Mock trace context for LLM interactions"""
        span = MagicMock()
        span.model_name = model_name
        span.operation = operation
        span.attributes = kwargs
        self.spans.append(span)
        
        yield span
    
    @contextmanager
    def trace_tool_execution(self, tool_name: str, operation: str, **kwargs):
        """Mock trace context for tool execution"""
        span = MagicMock()
        span.tool_name = tool_name
        span.operation = operation
        span.attributes = kwargs
        self.spans.append(span)
        
        yield span
    
    def record_agent_metrics(self, agent_name: str, metrics: Dict[str, Any]):
        """Mock recording of agent metrics"""
        pass
    
    def record_performance_metrics(self, operation: str, duration: float, **kwargs):
        """Mock recording of performance metrics"""
        pass
    
    def get_trace_context(self) -> Dict[str, Any]:
        """Mock getting trace context"""
        return {"trace_id": "mock-trace-123", "span_id": "mock-span-456"}


def initialize_observability(config=None) -> MockObservability:
    """Mock initialization function"""
    return MockObservability()


def get_tracer(name: str):
    """Mock tracer"""
    tracer = MagicMock()
    tracer.start_span = MagicMock()
    return tracer


# Mock OpenTelemetry modules
class MockTrace:
    def get_tracer(self, name: str):
        return get_tracer(name)


class MockResource:
    def __init__(self, attributes=None):
        self.attributes = attributes or {}


class MockTracerProvider:
    def __init__(self, resource=None):
        self.resource = resource
    
    def add_span_processor(self, processor):
        pass


class MockBatchSpanProcessor:
    def __init__(self, exporter):
        self.exporter = exporter


class MockOTLPSpanExporter:
    def __init__(self, endpoint=None, **kwargs):
        self.endpoint = endpoint


# Install mocks
import sys

# Create mock modules for OpenTelemetry
mock_otel = MagicMock()
mock_otel.trace = MockTrace()

sys.modules['opentelemetry'] = mock_otel
sys.modules['opentelemetry.trace'] = mock_otel.trace
sys.modules['opentelemetry.sdk'] = MagicMock()
sys.modules['opentelemetry.sdk.trace'] = MagicMock()
sys.modules['opentelemetry.sdk.trace.export'] = MagicMock()
sys.modules['opentelemetry.sdk.resources'] = MagicMock()
sys.modules['opentelemetry.exporter'] = MagicMock()
sys.modules['opentelemetry.exporter.otlp'] = MagicMock()
sys.modules['opentelemetry.exporter.otlp.proto'] = MagicMock()
sys.modules['opentelemetry.exporter.otlp.proto.grpc'] = MagicMock()
sys.modules['opentelemetry.exporter.otlp.proto.grpc.trace_exporter'] = MagicMock()

def install_mocks():
    """Install mocks into sys.modules for imports"""
    import sys
    from unittest.mock import MagicMock
    
    # Mock OpenTelemetry modules
    sys.modules['opentelemetry'] = MagicMock()
    sys.modules['opentelemetry.trace'] = MagicMock()
    sys.modules['opentelemetry.context'] = MagicMock()
    sys.modules['opentelemetry.sdk'] = MagicMock()
    sys.modules['opentelemetry.sdk.resources'] = MagicMock()
    sys.modules['opentelemetry.sdk.trace'] = MagicMock()
    sys.modules['opentelemetry.sdk.trace.export'] = MagicMock()
    sys.modules['opentelemetry.exporter'] = MagicMock()
    sys.modules['opentelemetry.exporter.otlp'] = MagicMock()
    sys.modules['opentelemetry.exporter.otlp.proto'] = MagicMock()
    sys.modules['opentelemetry.exporter.otlp.proto.grpc'] = MagicMock()
    sys.modules['opentelemetry.exporter.otlp.proto.grpc.trace_exporter'] = MagicMock()

    # Set specific mock classes
    sys.modules['opentelemetry.sdk.resources'].Resource = MockResource
    sys.modules['opentelemetry.sdk.trace'].TracerProvider = MockTracerProvider
    sys.modules['opentelemetry.sdk.trace.export'].BatchSpanProcessor = MockBatchSpanProcessor
    sys.modules['opentelemetry.exporter.otlp.proto.grpc.trace_exporter'].OTLPSpanExporter = MockOTLPSpanExporter

# Auto-install when module is imported (for backwards compatibility)
install_mocks()