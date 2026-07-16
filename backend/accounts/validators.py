"""
KSP Insight AI — Module 1: Identity & Administration
Custom field validators for accounts app.
"""

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

# Indian mobile numbers: optional +91, then 10 digits starting 6-9
phone_validator = RegexValidator(
    regex=r'^(\+91)?[6-9]\d{9}$',
    message="Enter a valid Indian phone number (10 digits, optionally prefixed with +91)."
)

# Badge number: letters/digits/hyphens only, no spaces
badge_number_validator = RegexValidator(
    regex=r'^[A-Za-z0-9\-]+$',
    message="Badge number can only contain letters, numbers, and hyphens."
)


def validate_hierarchy_level(value):
    """Rank hierarchy level must be between 1 (DGP) and 10 (Constable)."""
    if not (1 <= value <= 10):
        raise ValidationError(
            "hierarchy_level must be between 1 (most senior) and 10 (least senior)."
        )