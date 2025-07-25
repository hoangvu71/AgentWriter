"""
Observability and tracing configuration for ADK agents.
Enables comprehensive telemetry, performance monitoring, and debugging.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
# from opentelemetry.instrumentation.logging import LoggingInstrumentor  # Commented out since observability is disabled
from opentelemetry.sdk.resources import Resource

from .logging import get_logger

logger = get_logger("observability")


class ObservabilityConfig:
    """Configuration for observability and tracing"""
    
    def __init__(self):
        # Temporarily disable observability to fix serialization issues
        self.enabled = False  # self._is_tracing_enabled()
        self.service_name = os.getenv("OTEL_SERVICE_NAME", "adk-book-writer")
        self.service_version = os.getenv("OTEL_SERVICE_VERSION", "1.0.0")
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        # Exporter configurations
        self.otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        self.langfuse_enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"
        self.langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        self.langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        
        logger.info(f"Observability config: enabled={self.enabled}, service={self.service_name}")
    
    def _is_tracing_enabled(self) -> bool:
        """Determine if tracing should be enabled"""
        # Enable if explicitly set
        if os.getenv("OTEL_TRACING_ENABLED", "").lower() == "true":
            return True
        
        # Enable if any exporter is configured
        if (os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or 
            os.getenv("LANGFUSE_PUBLIC_KEY")):
            return True
        
        # Enable in development for local debugging
        if os.getenv("ENVIRONMENT", "development") == "development":
            return True
        
        return False


class ADKObservabilityManager:
    """Manages ADK observability, tracing, and performance monitoring"""
    
    def __init__(self, config: ObservabilityConfig):
        self.config = config
        self.tracer_provider = None
        self.tracer = None
        self.performance_metrics = {}
        
        if config.enabled:
            self._setup_tracing()
            self._setup_instrumentation()
            logger.info("ADK observability initialized successfully")
        else:
            logger.info("ADK observability disabled")
    
    def _setup_tracing(self):
        """Initialize OpenTelemetry tracing"""
        try:
            # Create resource with service information
            resource = Resource.create({
                "service.name": self.config.service_name,
                "service.version": self.config.service_version,
                "environment": self.config.environment,
                "telemetry.sdk.name": "opentelemetry",
                "telemetry.sdk.language": "python",
            })
            
            # Create tracer provider
            self.tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(self.tracer_provider)
            
            # Setup exporters
            self._setup_exporters()
            
            # Get tracer for this service
            self.tracer = trace.get_tracer(__name__)
            
            logger.info("OpenTelemetry tracing configured")
            
        except Exception as e:
            logger.error(f"Failed to setup tracing: {e}")
    
    def _setup_exporters(self):
        """Setup trace exporters (OTLP, Langfuse, etc.)"""
        try:
            # OTLP Exporter (for generic observability platforms)
            if self.config.otlp_endpoint:
                otlp_exporter = OTLPSpanExporter(endpoint=self.config.otlp_endpoint)
                otlp_processor = BatchSpanProcessor(otlp_exporter)
                self.tracer_provider.add_span_processor(otlp_processor)
                logger.info(f"OTLP exporter configured: {self.config.otlp_endpoint}")
            
            # Langfuse Exporter (for LLM-specific observability)
            if self.config.langfuse_enabled and self.config.langfuse_public_key:
                self._setup_langfuse_exporter()
            
            # Console exporter for development
            if self.config.environment == "development":
                from opentelemetry.exporter.console import ConsoleSpanExporter
                console_exporter = ConsoleSpanExporter()
                console_processor = BatchSpanProcessor(console_exporter)
                self.tracer_provider.add_span_processor(console_processor)
                logger.info("Console span exporter enabled for development")
                
        except Exception as e:
            logger.error(f"Failed to setup exporters: {e}")
    
    def _setup_langfuse_exporter(self):
        """Setup Langfuse exporter for LLM observability"""
        try:
            # Try to import and configure Langfuse
            from langfuse.opentelemetry import LangfuseSpanExporter
            
            langfuse_exporter = LangfuseSpanExporter(
                public_key=self.config.langfuse_public_key,
                secret_key=self.config.langfuse_secret_key,
                host=self.config.langfuse_host
            )
            langfuse_processor = BatchSpanProcessor(langfuse_exporter)
            self.tracer_provider.add_span_processor(langfuse_processor)
            logger.info("Langfuse exporter configured")
            
        except ImportError:
            logger.warning("Langfuse not installed, skipping Langfuse exporter")
        except Exception as e:
            logger.error(f"Failed to setup Langfuse exporter: {e}")
    
    def _setup_instrumentation(self):
        """Setup automatic instrumentation"""
        try:
            # Auto-instrument logging
            LoggingInstrumentor().instrument(set_logging_format=True)
            
            # Additional instrumentations can be added here
            # - HTTP requests
            # - Database calls
            # - External API calls
            
            logger.info("Automatic instrumentation configured")
            
        except Exception as e:
            logger.error(f"Failed to setup instrumentation: {e}")
    
    def trace_agent_execution(self, agent_name: str, user_id: str, session_id: str, 
                            request_content: str):
        """Create a trace span for agent execution"""
        if not self.tracer:
            return NoOpSpan()
        
        return self.tracer.start_span(
            name=f"agent.{agent_name}.execute",
            attributes={
                "agent.name": agent_name,
                "user.id": user_id,
                "session.id": session_id,
                "request.content_length": len(request_content),
                "request.preview": request_content[:100] + "..." if len(request_content) > 100 else request_content
            }
        )
    
    def trace_llm_interaction(self, agent_name: str, model: str, prompt: str):
        """Create a trace span for LLM interactions"""
        if not self.tracer:
            return NoOpSpan()
        
        return self.tracer.start_span(
            name=f"llm.{model}.completion",
            attributes={
                "llm.model": model,
                "llm.agent": agent_name,
                "llm.prompt_length": len(prompt),
                "llm.prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt
            }
        )
    
    def trace_tool_execution(self, tool_name: str, agent_name: str, parameters: Dict[str, Any]):
        """Create a trace span for tool execution"""
        if not self.tracer:
            return NoOpSpan()
        
        return self.tracer.start_span(
            name=f"tool.{tool_name}.execute",
            attributes={
                "tool.name": tool_name,
                "tool.agent": agent_name,
                "tool.parameters_count": len(parameters),
                "tool.parameters": str(parameters)[:500]  # Truncate large params
            }
        )
    
    def record_performance_metric(self, metric_name: str, value: float, 
                                tags: Optional[Dict[str, str]] = None):
        """Record a performance metric"""
        timestamp = datetime.utcnow().isoformat()
        
        if metric_name not in self.performance_metrics:
            self.performance_metrics[metric_name] = []
        
        metric_entry = {
            "timestamp": timestamp,
            "value": value,
            "tags": tags or {}
        }
        
        self.performance_metrics[metric_name].append(metric_entry)
        
        # Keep only recent metrics (last 1000 entries per metric)
        if len(self.performance_metrics[metric_name]) > 1000:
            self.performance_metrics[metric_name] = self.performance_metrics[metric_name][-1000:]
        
        logger.debug(f"Recorded metric {metric_name}: {value}", **tags or {})
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of performance metrics"""
        summary = {}
        
        for metric_name, entries in self.performance_metrics.items():
            if not entries:
                continue
            
            values = [entry["value"] for entry in entries]
            summary[metric_name] = {
                "count": len(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "recent": values[-10:] if len(values) >= 10 else values
            }
        
        return summary


class NoOpSpan:
    """No-operation span for when tracing is disabled"""
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def set_attribute(self, key: str, value: Any):
        pass
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        pass
    
    def set_status(self, status_code):
        pass


# Global observability manager instance
_observability_manager = None


def get_observability_manager() -> ADKObservabilityManager:
    """Get the global observability manager instance"""
    global _observability_manager
    
    if _observability_manager is None:
        config = ObservabilityConfig()
        _observability_manager = ADKObservabilityManager(config)
    
    return _observability_manager


def initialize_observability():
    """Initialize observability system"""
    return get_observability_manager()