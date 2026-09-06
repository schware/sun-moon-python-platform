from __future__ import annotations

from netframework_ai_agent.base import LLMProvider
from netframework_ai_agent.providers.echo_provider import EchoProvider
from netframework_core.exceptions import ConfigurationError


def build_provider(provider: str, *, model: str = "claude-sonnet-5", api_key: str | None = None) -> LLMProvider:
    """Takes plain values (not a service's Settings object) so this lib
    stays independent of any one service's config shape."""
    if provider == "echo":
        return EchoProvider()
    if provider == "anthropic":
        from netframework_ai_agent.providers.anthropic_provider import AnthropicProvider

        if not api_key:
            raise ConfigurationError("provider is 'anthropic' but no API key was given")
        return AnthropicProvider(api_key=api_key, model=model)
    raise ConfigurationError(f"unknown ai agent provider: {provider!r}")
