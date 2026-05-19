"""Canonical runtime safety helpers — null-safe coercion for all metric comparisons."""

import math
from typing import Any

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def safe_float(v: Any, default: float = 0.0) -> float:
    """Null-safe float coercion. Use BEFORE any numeric comparison.
    Rejects None, dict, list, NaN, Inf — always returns a safe float."""
    try:
        if v is None:
            return default
        if isinstance(v, dict):
            return default
        if isinstance(v, (list, tuple)):
            return default
        if HAS_NUMPY and isinstance(v, (np.floating,)):
            v = float(v)
        x = float(v)
        if math.isnan(x) or math.isinf(x):
            return default
        return x
    except Exception:
        return default


def safe_bool(v: Any) -> bool:
    """Null-safe bool coercion, handles numpy.bool_."""
    try:
        if HAS_NUMPY and isinstance(v, np.bool_):
            return bool(v)
        return bool(v)
    except Exception:
        return False


def safe_int(v: Any, default: int = 0) -> int:
    """Null-safe int coercion."""
    try:
        return int(v)
    except Exception:
        return default


def sanitize_json(obj: Any) -> Any:
    """Recursively convert numpy scalars to Python primitives for JSON serialization."""
    if isinstance(obj, dict):
        return {str(k): sanitize_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_json(v) for v in obj]
    if HAS_NUMPY:
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return sanitize_json(obj.tolist())
    return obj
