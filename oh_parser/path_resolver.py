"""
OH Parser Path Resolver.

Functions to navigate nested dictionaries using dot-notation paths with wildcard support.
"""
from __future__ import annotations

import fnmatch
import re
from typing import Any, Dict, Generator, List, Optional, Tuple

from .utils import safe_get, is_date_key, is_time_key


def resolve_path(data: dict, path: str, default: Any = None) -> Any:
    """
    Get value from nested dict using dot-notation path.
    
    :param data: Nested dictionary.
    :param path: Dot-notation path (e.g., "sensor_metrics.emg.EMG_weekly_metrics").
    :param default: Value to return if path doesn't exist.
    :returns: Value at path or default.
    
    Example:
        >>> d = {"a": {"b": {"c": 1}}}
        >>> resolve_path(d, "a.b.c")
        1
    """
    if not path:
        return data
    
    keys = path.split(".")
    return safe_get(data, keys, default)


def path_exists(data: dict, path: str) -> bool:
    """
    Check if a dot-notation path exists in nested dict.
    
    :param data: Nested dictionary.
    :param path: Dot-notation path to check.
    :returns: True if path exists.
    """
    sentinel = object()
    return resolve_path(data, path, default=sentinel) is not sentinel


def expand_wildcards(
    data: dict,
    path: str,
    level_names: Optional[List[str]] = None,
) -> Generator[Tuple[Dict[str, str], Any], None, None]:
    """
    Expand wildcards in a path and yield (context, value) for each match.
    
    Wildcards:
    - "*" matches any single key at that level
    - "**" matches any number of nested levels (not implemented yet)
    
    :param data: Nested dictionary to navigate.
    :param path: Dot-notation path with wildcards (e.g., "emg.*.*.left").
    :param level_names: Names to assign to wildcard levels (e.g., ["date", "session"]).
    :yields: Tuples of (context_dict, value) where context_dict maps level names to matched keys.
    
    Example:
        >>> d = {"emg": {"2025-01-01": {"10-00-00": {"left": 1}}}}
        >>> list(expand_wildcards(d, "emg.*.*.left", ["date", "session"]))
        [({'date': '2025-01-01', 'session': '10-00-00'}, 1)]
    """
    parts = path.split(".")
    level_names = level_names or []
    
    def _expand(current: Any, parts_remaining: List[str], context: Dict[str, str], wildcard_idx: int):
        if not parts_remaining:
            yield context.copy(), current
            return
        
        part = parts_remaining[0]
        rest = parts_remaining[1:]
        
        if not isinstance(current, dict):
            return
        
        if part == "*":
            # Match any key at this level
            level_name = level_names[wildcard_idx] if wildcard_idx < len(level_names) else f"level_{wildcard_idx}"
            for key, value in current.items():
                new_context = context.copy()
                new_context[level_name] = key
                yield from _expand(value, rest, new_context, wildcard_idx + 1)
        else:
            # Exact match
            if part in current:
                yield from _expand(current[part], rest, context, wildcard_idx)
    
    yield from _expand(data, parts, {}, 0)


def list_keys_at_path(data: dict, path: str) -> List[str]:
    """
    List all keys at a given path in the nested dict.
    
    :param data: Nested dictionary.
    :param path: Dot-notation path (empty string for root).
    :returns: List of keys at that path, or empty list if path doesn't exist.
    
    Example:
        >>> d = {"a": {"b": 1, "c": 2}}
        >>> list_keys_at_path(d, "a")
        ["b", "c"]
    """
    target = resolve_path(data, path) if path else data
    if isinstance(target, dict):
        return list(target.keys())
    return []


def get_structure_summary(
    data: dict,
    path: str = "",
    max_depth: int = 4,
    _current_depth: int = 0,
) -> Dict[str, Any]:
    """
    Get a summary of the structure at a path (key names and types, not values).
    
    :param data: Nested dictionary.
    :param path: Starting path.
    :param max_depth: Maximum depth to traverse.
    :param _current_depth: Internal depth counter.
    :returns: Structure summary dict.
    """
    target = resolve_path(data, path) if path else data
    
    if not isinstance(target, dict):
        return {"_type": type(target).__name__, "_value_preview": repr(target)[:50]}
    
    if _current_depth >= max_depth:
        return {"_type": "dict", "_keys": list(target.keys())[:5], "_truncated": True}
    
    result = {}
    for key, value in target.items():
        if isinstance(value, dict):
            result[key] = get_structure_summary(
                value, 
                path="",
                max_depth=max_depth,
                _current_depth=_current_depth + 1,
            )
        else:
            result[key] = {"_type": type(value).__name__}
    
    return result


def find_paths_matching(
    data: dict,
    pattern: str,
    max_depth: int = 10,
) -> List[str]:
    """
    Find all paths in nested dict matching a glob pattern.
    
    :param data: Nested dictionary.
    :param pattern: Glob pattern (e.g., "*.emg.*" or "sensor_metrics.*.EMG_*").
    :param max_depth: Maximum depth to search.
    :returns: List of matching paths.
    """
    from .utils import get_nested_keys
    
    all_paths = get_nested_keys(data, max_depth=max_depth)
    return [p for p in all_paths if fnmatch.fnmatch(p, pattern)]


def infer_level_type(keys: List[str]) -> str:
    """
    Infer the type of keys at a level (date, time, side, or generic).
    
    :param keys: List of keys at a level.
    :returns: Inferred type string.
    """
    if not keys:
        return "empty"
    
    # Check if all are dates
    if all(is_date_key(k) for k in keys):
        return "date"
    
    # Check if all are times
    if all(is_time_key(k) for k in keys):
        return "time"
    
    # Check if side labels
    side_patterns = {"left", "right", "Left", "Right", "LEFT", "RIGHT", "L", "R"}
    if all(k in side_patterns for k in keys):
        return "side"
    
    return "generic"
