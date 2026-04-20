"""
Optional local embedding support via sentence-transformers.
Returns is_available() = False when the dependency is not installed.
"""

try:
    from sentence_transformers import SentenceTransformer as _ST
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False


def is_available() -> bool:
    return _AVAILABLE
