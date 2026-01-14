"""
OH Parser Filters.

Functions and data structures for filtering subjects and records.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from .path_resolver import path_exists, resolve_path
from .utils import is_date_key


def create_filters(
    subject_ids: Optional[List[str]] = None,
    exclude_subjects: Optional[List[str]] = None,
    groups: Optional[List[str]] = None,
    date_range: Optional[Tuple[str, str]] = None,
    require_keys: Optional[List[str]] = None,
    custom_filter: Optional[Callable[[str, dict], bool]] = None,
) -> Dict[str, Any]:
    """
    Create a filters dictionary for controlling extraction.
    
    :param subject_ids: Include only these subject IDs (None = all).
    :param exclude_subjects: Exclude these subject IDs.
    :param groups: Include only subjects in these groups (from meta_data.group).
    :param date_range: (start, end) date strings in YYYY-MM-DD format.
    :param require_keys: Only include subjects that have all these paths.
    :param custom_filter: Callable(subject_id, profile) -> bool for custom logic.
    :returns: Filters dictionary.
    """
    return {
        "subject_ids": subject_ids,
        "exclude_subjects": exclude_subjects,
        "groups": groups,
        "date_range": date_range,
        "require_keys": require_keys,
        "custom_filter": custom_filter,
    }


def apply_subject_filters(
    profiles: Dict[str, dict],
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, dict]:
    """
    Filter profiles dictionary based on filters dict.
    
    :param profiles: Dictionary mapping subject_id -> OH profile dict.
    :param filters: Filters dictionary (None = no filtering).
    :returns: Filtered profiles dictionary.
    """
    if filters is None:
        return profiles
    
    result = {}
    
    for subject_id, profile in profiles.items():
        # Check subject_ids whitelist
        if filters.get("subject_ids") is not None:
            if subject_id not in filters["subject_ids"]:
                continue
        
        # Check exclude_subjects blacklist
        if filters.get("exclude_subjects") is not None:
            if subject_id in filters["exclude_subjects"]:
                continue
        
        # Check groups
        if filters.get("groups") is not None:
            subject_group = resolve_path(profile, "meta_data.group")
            if subject_group not in filters["groups"]:
                continue
        
        # Check required keys
        if filters.get("require_keys") is not None:
            has_all_keys = all(path_exists(profile, key) for key in filters["require_keys"])
            if not has_all_keys:
                continue
        
        # Check custom filter
        if filters.get("custom_filter") is not None:
            if not filters["custom_filter"](subject_id, profile):
                continue
        
        result[subject_id] = profile
    
    return result


def filter_date_keys(
    keys: List[str],
    date_range: Optional[Tuple[str, str]] = None,
) -> List[str]:
    """
    Filter a list of date keys by date range.
    
    :param keys: List of keys (some may be dates in YYYY-MM-DD format).
    :param date_range: (start, end) date strings, inclusive.
    :returns: Filtered list of keys.
    """
    if date_range is None:
        return keys
    
    start_str, end_str = date_range
    
    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_str, "%Y-%m-%d")
    except ValueError:
        # Invalid date format, return all keys
        return keys
    
    result = []
    for key in keys:
        if not is_date_key(key):
            # Not a date key, include it (could be "EMG_weekly_metrics" etc.)
            result.append(key)
            continue
        
        try:
            key_date = datetime.strptime(key, "%Y-%m-%d")
            if start_date <= key_date <= end_date:
                result.append(key)
        except ValueError:
            # Can't parse as date, include it
            result.append(key)
    
    return result


def matches_pattern(key: str, patterns: List[str]) -> bool:
    """
    Check if a key matches any of the given patterns.
    
    Patterns can be:
    - Exact match: "EMG_weekly_metrics"
    - Prefix match: "EMG_*" (matches anything starting with "EMG_")
    - Suffix match: "*_metrics" (matches anything ending with "_metrics")
    - Contains: "*daily*" (matches anything containing "daily")
    
    :param key: Key to check.
    :param patterns: List of patterns.
    :returns: True if key matches any pattern.
    """
    import fnmatch
    return any(fnmatch.fnmatch(key, p) for p in patterns)


def exclude_keys(keys: List[str], exclude_patterns: List[str]) -> List[str]:
    """
    Filter out keys matching exclusion patterns.
    
    :param keys: List of keys.
    :param exclude_patterns: Patterns to exclude (supports wildcards).
    :returns: Keys not matching any exclusion pattern.
    """
    return [k for k in keys if not matches_pattern(k, exclude_patterns)]


def include_keys(keys: List[str], include_patterns: List[str]) -> List[str]:
    """
    Keep only keys matching inclusion patterns.
    
    :param keys: List of keys.
    :param include_patterns: Patterns to include (supports wildcards).
    :returns: Keys matching at least one inclusion pattern.
    """
    return [k for k in keys if matches_pattern(k, include_patterns)]
