"""
BASA - Quick API
=================
Zero-config shorthand for the most common normalize() call.

``quick()`` always uses all default settings:
    - lowercase=True
    - apply_slang=True
    - apply_typo=False
    - normalize_punctuation=True
    - normalize_whitespace=True

This is intentionally a thin alias — no new logic lives here.
For fine-grained control use ``normalize()`` directly.

Usage:
    >>> from basa import quick
    >>> quick("GW GKKKK NGERTIII BNGTTTT!!!!!")
    'saya tidak mengerti banget!'
"""

from __future__ import annotations

from .normalize import normalize


def quick(text: str | list[str]) -> str | list[str]:
    """
    Normalize informal Indonesian text with zero configuration.

    A convenience alias for ``normalize()`` with all defaults applied.
    Accepts a single string or a list of strings.

    Args:
        text: Input string or list of strings.

    Returns:
        Normalized string or list of normalized strings.

    Examples:
        >>> from basa import quick
        >>> quick("gw gk ngerti bngt sihhhh!!!")
        'saya tidak mengerti banget sih!'

        >>> quick(["gw mkan", "dia mnum"])
        ['saya makan', 'dia minum']
    """
    return normalize(text)
