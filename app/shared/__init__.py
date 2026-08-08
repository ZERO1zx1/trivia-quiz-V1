"""Shared utilities used across multiple domains.

This package is intentionally thin: it hosts cross-cutting helpers
(decorators, pagination, validation) and re-exports the canonical
password policy so existing and future code imports from one place.
"""
from app.shared.password_policy import validate_password, password_is_valid, POLICY, MIN_PASSWORD_LENGTH

__all__ = [
    'validate_password',
    'password_is_valid',
    'POLICY',
    'MIN_PASSWORD_LENGTH',
]
