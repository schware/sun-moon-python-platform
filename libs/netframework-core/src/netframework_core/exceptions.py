"""Shared exception hierarchy. Every service should raise these (or
subclasses) instead of bare Exception/ValueError so its interface layer can
translate them consistently (e.g. DomainError/NotFoundError -> HTTP 4xx)."""


class FrameworkError(Exception):
    """Base for every error raised by netframework-core or a service built on it."""


class DomainError(FrameworkError):
    """Business rule violation raised from inside a domain entity/aggregate."""


class NotFoundError(FrameworkError):
    """A requested entity/aggregate does not exist."""


class ApplicationError(FrameworkError):
    """Use-case-level failure (e.g. invalid command, conflicting state)."""


class ConfigurationError(FrameworkError):
    """Service misconfiguration (bad env var, missing dependency, ...)."""
