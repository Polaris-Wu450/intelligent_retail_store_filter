"""
LLM Service abstraction layer
Provides unified interface for different LLM providers
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any
import logging
import os

logger = logging.getLogger(__name__)


class BaseLLMService(ABC):
    """
    Abstract base class for LLM service providers
    All concrete implementations must inherit from this class
    """
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text completion from the LLM
        
        Args:
            prompt: Input prompt text
            **kwargs: Provider-specific parameters (max_tokens, temperature, etc.)
        
        Returns:
            str: Generated text response
        
        Raises:
            Exception: If API call fails
        """
        pass
    
    @abstractmethod
    def generate_with_messages(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate text using conversation format
        
        Args:
            messages: List of message dicts with 'role' and 'content'
                     e.g., [{"role": "user", "content": "Hello"}]
            **kwargs: Provider-specific parameters
        
        Returns:
            str: Generated text response
        
        Raises:
            Exception: If API call fails
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the current model name
        
        Returns:
            str: Model identifier
        """
        pass


class ClaudeService(BaseLLMService):
    """
    Claude AI service implementation (Anthropic)
    """
    
    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize Claude service
        
        Args:
            api_key: Anthropic API key (defaults to settings.RETAILOPS_API_KEY)
            model: Model name (defaults to claude-sonnet-4-5-20250929)
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )
        
        from django.conf import settings
        
        self.api_key = api_key or settings.RETAILOPS_API_KEY
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model or "claude-sonnet-4-5-20250929"
        
        logger.info(f"[CLAUDE_SERVICE] Initialized with model: {self.model}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Claude API with single prompt
        """
        max_tokens = kwargs.get('max_tokens', 1000)
        temperature = kwargs.get('temperature', 1.0)
        
        logger.info(f"[CLAUDE_SERVICE] Generating with prompt length: {len(prompt)}")
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response = message.content[0].text
        logger.info(f"[CLAUDE_SERVICE] ✅ Generated {len(response)} characters")
        
        return response
    
    def generate_with_messages(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate text using Claude API with conversation messages
        """
        max_tokens = kwargs.get('max_tokens', 1000)
        temperature = kwargs.get('temperature', 1.0)
        
        logger.info(f"[CLAUDE_SERVICE] Generating with {len(messages)} messages")
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages
        )
        
        response = message.content[0].text
        logger.info(f"[CLAUDE_SERVICE] ✅ Generated {len(response)} characters")
        
        return response
    
    def get_model_name(self) -> str:
        """Get Claude model name"""
        return self.model


class OpenAIService(BaseLLMService):
    """
    OpenAI service implementation
    """
    
    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize OpenAI service
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name (defaults to gpt-4)
        """
        try:
            import openai
        except ImportError:
            raise ImportError(
                "openai package not installed. "
                "Install with: pip install openai"
            )
        
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = model or "gpt-4"
        
        logger.info(f"[OPENAI_SERVICE] Initialized with model: {self.model}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using OpenAI API with single prompt
        """
        max_tokens = kwargs.get('max_tokens', 1000)
        temperature = kwargs.get('temperature', 1.0)
        
        logger.info(f"[OPENAI_SERVICE] Generating with prompt length: {len(prompt)}")
        
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = response.choices[0].message.content
        logger.info(f"[OPENAI_SERVICE] ✅ Generated {len(result)} characters")
        
        return result
    
    def generate_with_messages(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate text using OpenAI API with conversation messages
        """
        max_tokens = kwargs.get('max_tokens', 1000)
        temperature = kwargs.get('temperature', 1.0)
        
        logger.info(f"[OPENAI_SERVICE] Generating with {len(messages)} messages")
        
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages
        )
        
        result = response.choices[0].message.content
        logger.info(f"[OPENAI_SERVICE] ✅ Generated {len(result)} characters")
        
        return result
    
    def get_model_name(self) -> str:
        """Get OpenAI model name"""
        return self.model


# ============================================================================
# LLM Service Factory
# ============================================================================

_LLM_SERVICE_REGISTRY = {
    'claude': ClaudeService,
    'openai': OpenAIService,
}


def register_llm_service(provider: str, service_class: type):
    """
    Register a new LLM service provider
    
    Args:
        provider: Provider identifier (e.g., 'claude', 'openai', 'local')
        service_class: Service class (must inherit from BaseLLMService)
    """
    if not issubclass(service_class, BaseLLMService):
        raise ValueError(f"{service_class} must inherit from BaseLLMService")
    
    _LLM_SERVICE_REGISTRY[provider] = service_class
    logger.info(f"[LLM_FACTORY] Registered service: {provider} -> {service_class.__name__}")


def get_llm_service(provider: str = None, **kwargs) -> BaseLLMService:
    """
    Get LLM service instance based on provider
    
    Args:
        provider: Provider name ('claude', 'openai', or None for default)
                 If None, reads from LLM_PROVIDER env var (defaults to 'claude')
        **kwargs: Additional parameters to pass to service constructor
    
    Returns:
        BaseLLMService: LLM service instance
    
    Raises:
        ValueError: If provider is not registered
    
    Example:
        # Use default provider (claude)
        llm = get_llm_service()
        response = llm.generate("Your prompt here")
        
        # Use specific provider
        llm = get_llm_service('openai')
        response = llm.generate("Your prompt here")
        
        # Use with custom model
        llm = get_llm_service('claude', model='claude-3-opus-20240229')
    """
    if provider is None:
        provider = os.getenv('LLM_PROVIDER', 'claude').lower()
        logger.info(f"[LLM_FACTORY] Using provider from env: {provider}")
    
    service_class = _LLM_SERVICE_REGISTRY.get(provider)
    
    if service_class is None:
        available = ', '.join(_LLM_SERVICE_REGISTRY.keys())
        raise ValueError(
            f"Unknown LLM provider: '{provider}'. "
            f"Available providers: {available}"
        )
    
    logger.info(f"[LLM_FACTORY] Creating {service_class.__name__} instance")
    return service_class(**kwargs)
