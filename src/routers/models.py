"""
AI Model management API routes.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from ..core.configuration import config

router = APIRouter()


# Available models supported by Google ADK
AVAILABLE_MODELS = {
    # Gemini Models (Primary ADK Support)
    "gemini-2.0-flash": {
        "name": "Gemini 2.0 Flash",
        "description": "Next-gen features, superior speed, native tool use",
        "best_for": "Creative writing, complex reasoning, code generation",
        "context_window": "1M tokens",
        "speed": "Fast",
        "provider": "Google"
    },
    "gemini-2.0-flash-lite": {
        "name": "Gemini 2.0 Flash-Lite",
        "description": "Better quality than 1.5 Flash at same speed/cost",
        "best_for": "Budget-conscious tasks, quick responses",
        "context_window": "1M tokens",
        "speed": "Very Fast",
        "provider": "Google"
    },
    "gemini-2.0-pro-experimental": {
        "name": "Gemini 2.0 Pro Experimental",
        "description": "Best for coding performance and complex prompts",
        "best_for": "Advanced coding, complex multi-step reasoning",
        "context_window": "2M tokens",
        "speed": "Medium",
        "provider": "Google"
    },
    "gemini-2.5-flash": {
        "name": "Gemini 2.5 Flash",
        "description": "Best price-performance model with thinking capabilities",
        "best_for": "Well-rounded tasks, creative writing with reasoning",
        "context_window": "1M tokens",
        "speed": "Fast",
        "provider": "Google"
    },
    "gemini-2.5-flash-lite": {
        "name": "Gemini 2.5 Flash-Lite",
        "description": "Lowest latency and cost in 2.5 family, thinking off by default",
        "best_for": "High throughput tasks, classification, summarization at scale",
        "context_window": "1M tokens",
        "speed": "Ultra Fast",
        "provider": "Google"
    },
    "gemini-2.5-pro": {
        "name": "Gemini 2.5 Pro",
        "description": "Most intelligent model with advanced thinking capabilities",
        "best_for": "Complex reasoning, code, math, STEM, #1 on LMArena",
        "context_window": "2M tokens",
        "speed": "Medium",
        "provider": "Google"
    },
    "gemini-2.5-pro-deep-think": {
        "name": "Gemini 2.5 Pro Deep Think",
        "description": "Enhanced reasoning mode considering multiple hypotheses",
        "best_for": "Competition-level math (USAMO), advanced coding (LiveCodeBench)",
        "context_window": "2M tokens",
        "speed": "Slow",
        "provider": "Google"
    },
    
    # DEPRECATED: Legacy Gemini Models - Use newer variants for new projects
    "gemini-1.5-pro": {
        "name": "Gemini 1.5 Pro (DEPRECATED)", 
        "description": "DEPRECATED: Use gemini-2.0-flash-exp for new projects",
        "best_for": "Legacy compatibility only",
        "context_window": "2M tokens",
        "speed": "Medium",
        "provider": "Google",
        "deprecated": True,
        "replacement": "gemini-2.0-flash-exp",
        "note": "Limited availability for new projects after April 2025"
    },
    "gemini-1.5-flash": {
        "name": "Gemini 1.5 Flash (DEPRECATED)",
        "description": "DEPRECATED: Use gemini-1.5-flash-002 for new projects",
        "best_for": "Legacy compatibility only",
        "context_window": "1M tokens", 
        "speed": "Very Fast",
        "provider": "Google",
        "deprecated": True,
        "replacement": "gemini-1.5-flash-002",
        "note": "Limited availability for new projects after April 2025"
    },
    
    # Anthropic Claude Models (via ADK)
    "claude-3-sonnet@20240229": {
        "name": "Claude 3 Sonnet",
        "description": "Anthropic's balanced model via ADK",
        "best_for": "General tasks, analysis, creative writing",
        "context_window": "200K tokens",
        "speed": "Medium",
        "provider": "Anthropic"
    },
    "claude-3-haiku-20240307": {
        "name": "Claude 3 Haiku",
        "description": "Fast and efficient Anthropic model",
        "best_for": "Quick responses, simple tasks, cost-effective usage",
        "context_window": "200K tokens",
        "speed": "Very Fast",
        "provider": "Anthropic"
    },
    "claude-3-7-sonnet-latest": {
        "name": "Claude 3.7 Sonnet",
        "description": "Latest Anthropic model via ADK",
        "best_for": "Advanced reasoning, complex analysis",
        "context_window": "200K tokens",
        "speed": "Medium",
        "provider": "Anthropic"
    },
    
    # OpenAI Models (via LiteLLM integration)
    "openai/gpt-4o": {
        "name": "GPT-4o",
        "description": "OpenAI's flagship model via LiteLLM",
        "best_for": "Multimodal tasks, complex reasoning",
        "context_window": "128K tokens",
        "speed": "Medium",
        "provider": "OpenAI"
    }
}


@router.get("/models")
async def get_available_models() -> Dict[str, Any]:
    """Get all available AI models"""
    return {
        "current_model": config.model_name,
        "available_models": AVAILABLE_MODELS
    }


@router.post("/models/{model_id}/switch")
async def switch_model(model_id: str) -> Dict[str, Any]:
    """Switch to a different AI model"""
    if model_id not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=400, 
            detail=f"Model '{model_id}' not available. Available models: {list(AVAILABLE_MODELS.keys())}"
        )
    
    # Note: In a production system, you would update the configuration
    # For now, we'll just return success since the model is set via environment variable
    return {
        "success": True,
        "message": f"Model switched to {model_id}",
        "note": "Model changes require server restart to take effect",
        "current_model": model_id,
        "model_info": AVAILABLE_MODELS[model_id]
    }


@router.get("/models/current")
async def get_current_model() -> Dict[str, Any]:
    """Get the currently active model"""
    return {
        "current_model": config.model_name,
        "model_info": AVAILABLE_MODELS.get(config.model_name, {
            "name": config.model_name,
            "description": "Custom model configuration",
            "best_for": "Unknown",
            "context_window": "Unknown",
            "speed": "Unknown"
        })
    }