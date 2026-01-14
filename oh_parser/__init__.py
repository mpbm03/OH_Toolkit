"""
OH Parser - Extract data from Occupational Health profile JSON files.

This package provides functions to load OH profiles and extract specific
data into pandas DataFrames for statistical analysis.

Main Functions:
    load_profiles(directory) - Load all OH profiles from a directory
    list_subjects(profiles) - Get list of subject IDs
    inspect_profile(profile) - Pretty-print profile structure
    get_available_paths(profile) - List all extractable paths
    extract(profiles, paths) - Extract specific paths (wide format)
    extract_nested(profiles, base_path, level_names) - Extract nested data (long format)
    extract_flat(profiles, base_path) - Flatten nested structure

Example:
    >>> from oh_parser import load_profiles, extract, extract_nested
    >>> 
    >>> # Load all profiles
    >>> profiles = load_profiles("E:/OH_profiles/")
    >>> 
    >>> # Extract specific values (one row per subject)
    >>> df = extract(profiles, paths={
    ...     "emg_p50": "sensor_metrics.emg.EMG_weekly_metrics.left.EMG_apdf.active.p50",
    ...     "age": "meta_data.age",
    ... })
    >>> 
    >>> # Extract nested EMG sessions (one row per session)
    >>> df = extract_nested(
    ...     profiles,
    ...     base_path="sensor_metrics.emg",
    ...     level_names=["date", "session", "side"],
    ...     value_paths=["EMG_intensity.*", "EMG_rest_recovery.*"],
    ...     exclude_patterns=["EMG_daily_metrics", "EMG_weekly_metrics"],
    ... )
"""
from __future__ import annotations

# Loader functions
from .loader import (
    discover_oh_profiles,
    load_profile,
    load_profiles,
    list_subjects,
    get_profile,
)

# Path resolution
from .path_resolver import (
    resolve_path,
    path_exists,
    expand_wildcards,
    list_keys_at_path,
    find_paths_matching,
)

# Filtering
from .filters import (
    create_filters,
    apply_subject_filters,
    filter_date_keys,
)

# Extraction functions
from .extract import (
    extract,
    extract_nested,
    extract_flat,
    get_available_paths,
    inspect_profile,
    summarize_profiles,
)

# Utilities
from .utils import (
    safe_get,
    flatten_dict,
    unflatten_dict,
    get_nested_keys,
    print_tree,
)


__all__ = [
    # Loader
    "discover_oh_profiles",
    "load_profile",
    "load_profiles",
    "list_subjects",
    "get_profile",
    # Path resolution
    "resolve_path",
    "path_exists",
    "expand_wildcards",
    "list_keys_at_path",
    "find_paths_matching",
    # Filtering
    "create_filters",
    "apply_subject_filters",
    "filter_date_keys",
    # Extraction
    "extract",
    "extract_nested",
    "extract_flat",
    "get_available_paths",
    "inspect_profile",
    "summarize_profiles",
    # Utilities
    "safe_get",
    "flatten_dict",
    "unflatten_dict",
    "get_nested_keys",
    "print_tree",
]
