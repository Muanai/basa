"""
BASA - Modern NLP for Indonesian and Regional Languages
=======================================================

Top-level package. Re-exports the public API.

Quick start:
    >>> from basa import normalize, quick
    >>> normalize("GW GKKKK NGERTIII BNGTTTT!!!!!")
    'saya tidak mengerti banget!'
    >>> quick("gw gk ngerti bngt sihhhh!!!")
    'saya tidak mengerti banget sih!'
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("basa")
except PackageNotFoundError:
    __version__ = "unknown"

from .core.normalize import normalize
from .core.quick import quick
from .core.slang import slang
from .core.typo import typo

__all__ = [
    "__version__",
    "normalize",
    "quick",
    "typo",
    "slang",
]
