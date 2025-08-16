"""
Centralized model configuration for Pydantic AI agents.
"""

import os
from typing import Any
from dotenv import load_dotenv

load_dotenv()


def get_smart_model() -> Any:
    """
    Get the configured LLM model for Pydantic AI agents.
    
    Returns:
        Configured model instance based on environment variables.
    """
    # Get provider preference
    llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
    llm_choice = os.getenv("LLM_CHOICE", "gpt-4o-mini")
    
    # Provider-specific configuration
    if llm_provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model_name = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    elif llm_provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("LLM_API_KEY")
        base_url = None
        model_name = os.getenv("ANTHROPIC_MODEL", "claude-4-sonnet")
    elif llm_provider == "perplexity":
        api_key = os.getenv("PERPLEXITY_API_KEY") or os.getenv("LLM_API_KEY")
        base_url = os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai")
        model_name = os.getenv("PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online")
    else:
        # Fallback to generic configuration
        api_key = os.getenv("LLM_API_KEY")
        base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        model_name = llm_choice
    
    if not api_key:
        raise ValueError(f"API key required for {llm_provider}. Set {llm_provider.upper()}_API_KEY or LLM_API_KEY environment variable.")
    
    # Import here to avoid circular imports
    try:
        if llm_provider == "openai" or "gpt" in model_name.lower():
            from pydantic_ai.models.openai import OpenAIModel
            return OpenAIModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url if base_url != "https://api.openai.com/v1" else None
            )
        elif llm_provider == "anthropic" or "claude" in model_name.lower():
            from pydantic_ai.models.anthropic import AnthropicModel
            # Use environment variable for API key (pydantic-ai will pick it up automatically)
            return AnthropicModel(model_name)
        elif llm_provider == "groq" or "groq" in model_name.lower():
            from pydantic_ai.models.groq import GroqModel
            return GroqModel(
                model_name=model_name,
                api_key=api_key
            )
        elif llm_provider == "perplexity" or "sonar" in model_name.lower():
            # Perplexity uses OpenAI-compatible API
            from pydantic_ai.models.openai import OpenAIModel
            return OpenAIModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url
            )
        else:
            # Default to OpenAI-compatible for unknown providers
            from pydantic_ai.models.openai import OpenAIModel
            return OpenAIModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url
            )
    except ImportError as e:
        raise ImportError(f"Required model library not installed for {llm_provider}: {e}")


def get_embedding_model() -> Any:
    """
    Get the configured embedding model.
    
    Returns:
        Configured embedding model instance.
    """
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    api_key = os.getenv("EMBEDDING_API_KEY") or os.getenv("LLM_API_KEY")
    base_url = os.getenv("EMBEDDING_BASE_URL", "https://api.openai.com/v1")
    
    if not api_key:
        raise ValueError("EMBEDDING_API_KEY or LLM_API_KEY environment variable is required")
    
    # Return configuration dict for now
    return {
        "model": embedding_model,
        "api_key": api_key,
        "base_url": base_url
    }