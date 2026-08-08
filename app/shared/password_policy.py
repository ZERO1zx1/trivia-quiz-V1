"""Password Policy & Validation (shared validator)

Enforces FIX-023: a single canonical password policy used by every
registration / password-change endpoint, so no route can drift to a weaker
rule (e.g. the old 6-character minimum).
"""
import re

# Policy defaults: can be overridden per-environment via config.
POLICY = {
    'min_length': 8,
    'max_length': 128,
    'require_uppercase': True,
    'require_lowercase': True,
    'require_digit': True,
    'require_special': True,
    'special_chars': set('!@#$%^&*()_+-=[]{}|;:,.<>?'),
}

MIN_PASSWORD_LENGTH = POLICY['min_length']  # legacy compat alias


def validate_password(password):
    """Validate a password against the canonical policy.

    Returns a list of human-readable error strings (empty == valid).
    """
    errors = []
    if password is None:
        return ['Password is required.']
    if len(password) < POLICY['min_length']:
        errors.append(
            f"Password must be at least {POLICY['min_length']} characters.")
    if len(password) > POLICY['max_length']:
        errors.append(
            f"Password must be at most {POLICY['max_length']} characters.")
    if POLICY['require_uppercase'] and not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter.')
    if POLICY['require_lowercase'] and not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter.')
    if POLICY['require_digit'] and not re.search(r'[0-9]', password):
        errors.append('Password must contain at least one digit.')
    if POLICY['require_special']:
        if not any(ch in POLICY['special_chars'] for ch in password):
            errors.append(
                'Password must contain at least one special character '
                f"({''.join(sorted(POLICY['special_chars']))}).")
    return errors


def password_is_valid(password):
    """Return True if the password satisfies the policy."""
    return len(validate_password(password)) == 0
