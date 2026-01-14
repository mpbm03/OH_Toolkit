# OH Parser - Documentation

**Purpose:** Extract data from Occupational Health (OH) profile JSON files into pandas DataFrames for statistical analysis.

---

## Table of Contents

1. [Overview](#overview)
2. [OH Profile JSON Structure](#oh-profile-json-structure)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [API Reference](#api-reference)
6. [Usage Examples](#usage-examples)
7. [Path Syntax](#path-syntax)
8. [EMG Data Reference](#emg-data-reference)

---

## Overview

The `oh_parser` module is a **standalone, generic parser** for OH profile JSON files. It provides:

- **Loading**: Discover and load all `*_OH_profile.json` files from a directory
- **Inspection**: Explore profile structure without knowing the schema in advance
- **Extraction**: Pull specific data into pandas DataFrames using dot-notation paths
- **Filtering**: Filter by subjects, date ranges, groups, or data availability

### Key Design Principles

1. **Generic**: Works with any nested JSON structure, not tied to specific domains
2. **Flexible**: Supports wildcards for iterating over dynamic keys (dates, sessions)
3. **Independent**: Only depends on pandas + Python standard library
4. **Functional**: Pure functions, no classes required

---

## OH Profile JSON Structure

Each subject has one OH profile file named `{subject_id}_OH_profile.json`.

### Top-Level Structure

```json
{
  "meta_data": { ... },
  "single_instance_questionnaires": {
    "personal": { ... },
    "biomechanical": { ... },
    "psychosocial": { ... },
    "environmental": { ... }
  },
  "daily_questionnaires": {
    "workload": { "YYYY-MM-DD": { ... }, ... },
    "pain": { "YYYY-MM-DD": { ... }, ... }
  },
  "sensor_metrics": {
    "sensor_timeline": { ... },
    "human_activities": { ... },
    "heart_rate": { ... },
    "posture": { ... },
    "noise": { ... },
    "emg": { ... },
    "wrist_activities": { ... }
  }
}
```

### EMG Nested Structure

The EMG data has a deeply nested structure:

```
sensor_metrics.emg/
├── {date: DD-MM-YYYY}/              # Each recording day
│   ├── {session: HH-MM-SS}/         # Each recording session (start time)
│   │   ├── left/                    # Left side measurements
│   │   │   ├── EMG_session/         # Session metadata
│   │   │   ├── EMG_intensity/       # Intensity metrics
│   │   │   ├── EMG_apdf/            # APDF percentiles
│   │   │   ├── EMG_rest_recovery/   # Rest/recovery metrics
│   │   │   └── EMG_relative_bins/   # Relative intensity bins
│   │   └── right/                   # Right side measurements
│   │       └── ... (same structure)
│   └── EMG_daily_metrics/           # Aggregated daily metrics
│       ├── left/ { ... }
│       └── right/ { ... }
└── EMG_weekly_metrics/              # Aggregated weekly metrics
    ├── left/ { ... }
    └── right/ { ... }
```

---

## Installation

The module is self-contained. Copy the `oh_parser/` folder to your project:

```
your_project/
├── oh_parser/
│   ├── __init__.py
│   ├── loader.py
│   ├── path_resolver.py
│   ├── filters.py
│   ├── extract.py
│   └── utils.py
└── your_analysis.py
```

**Dependencies:** `pandas` (only external dependency)

---

## Quick Start

```python
from oh_parser import load_profiles, list_subjects, inspect_profile, extract, extract_nested

# 1. Load all profiles from a directory
profiles = load_profiles("path/to/OH_profiles/")

# 2. See available subjects
subjects = list_subjects(profiles)  # ['103', '104', '105', ...]

# 3. Inspect a profile's structure
inspect_profile(profiles['103'], max_depth=4)

# 4. Extract specific values (one row per subject)
df = extract(profiles, paths={
    "emg_p50_left": "sensor_metrics.emg.EMG_weekly_metrics.left.EMG_apdf.active.p50",
    "emg_p50_right": "sensor_metrics.emg.EMG_weekly_metrics.right.EMG_apdf.active.p50",
})

# 5. Extract nested data (one row per session)
df = extract_nested(
    profiles,
    base_path="sensor_metrics.emg",
    level_names=["date", "session", "side"],
    value_paths=["EMG_intensity.mean_percent_mvc", "EMG_rest_recovery.rest_percent"],
    exclude_patterns=["EMG_daily_metrics", "EMG_weekly_metrics"],
)
```

---

## API Reference

### Loading Functions

#### `load_profiles(directory, subject_ids=None, verbose=True)`

Load all OH profile JSON files from a directory.

| Parameter | Type | Description |
|-----------|------|-------------|
| `directory` | `str \| Path` | Path to directory containing OH profiles |
| `subject_ids` | `List[str]` | Optional: only load specific subjects |
| `verbose` | `bool` | Print loading progress |

**Returns:** `Dict[str, dict]` - Dictionary mapping subject_id → profile dict

```python
profiles = load_profiles("E:/OH_profiles/")
profiles = load_profiles("E:/OH_profiles/", subject_ids=["103", "104"])
```

#### `list_subjects(profiles)`

Get sorted list of subject IDs.

**Returns:** `List[str]`

#### `get_profile(profiles, subject_id)`

Get a single profile by subject ID.

**Returns:** `dict | None`

---

### Inspection Functions

#### `inspect_profile(profile, base_path="", max_depth=4, show_values=False)`

Pretty-print the structure of a profile as a tree.

```python
inspect_profile(profiles['103'])
inspect_profile(profiles['103'], base_path="sensor_metrics.emg", max_depth=3)
```

#### `get_available_paths(profile, base_path="", max_depth=6)`

Get all dot-notation paths available in a profile.

**Returns:** `List[str]`

```python
paths = get_available_paths(profiles['103'])
# ['meta_data', 'single_instance_questionnaires.personal', ...]
```

#### `summarize_profiles(profiles, check_paths=None)`

Generate a summary DataFrame showing data availability across subjects.

**Returns:** `pd.DataFrame` with columns: `subject_id`, `has_meta_data`, `has_emg`, etc.

---

### Extraction Functions

#### `extract(profiles, paths, filters=None, include_subject_id=True)`

Extract specific paths into a **wide-format DataFrame** (one row per subject).

| Parameter | Type | Description |
|-----------|------|-------------|
| `profiles` | `Dict[str, dict]` | Loaded profiles |
| `paths` | `Dict[str, str]` | Mapping of output column names → dot-notation paths |
| `filters` | `dict` | Optional filters dictionary (from `create_filters`) |
| `include_subject_id` | `bool` | Include subject_id column |

**Returns:** `pd.DataFrame`

```python
df = extract(profiles, paths={
    "age": "meta_data.age",
    "emg_p50": "sensor_metrics.emg.EMG_weekly_metrics.left.EMG_apdf.active.p50",
})
# Output: subject_id | age | emg_p50
```

#### `extract_nested(profiles, base_path, level_names, value_paths=None, filters=None, exclude_patterns=None, flatten_values=True)`

Extract nested structures into a **long-format DataFrame** (one row per leaf node).

| Parameter | Type | Description |
|-----------|------|-------------|
| `profiles` | `Dict[str, dict]` | Loaded profiles |
| `base_path` | `str` | Starting path (e.g., `"sensor_metrics.emg"`) |
| `level_names` | `List[str]` | Names for nesting levels (e.g., `["date", "session", "side"]`) |
| `value_paths` | `List[str]` | Paths to extract relative to leaf (supports `*` wildcard) |
| `exclude_patterns` | `List[str]` | Patterns to skip (e.g., `["EMG_*_metrics"]`) |
| `filters` | `dict` | Optional filters dictionary (from `create_filters`) |
| `flatten_values` | `bool` | Flatten nested value dicts into columns |

**Returns:** `pd.DataFrame`

```python
# Extract all EMG sessions
df = extract_nested(
    profiles,
    base_path="sensor_metrics.emg",
    level_names=["date", "session", "side"],
    value_paths=["EMG_intensity.*", "EMG_rest_recovery.*"],
    exclude_patterns=["EMG_daily_metrics", "EMG_weekly_metrics"],
)
# Output: subject_id | date | session | side | EMG_intensity.mean_percent_mvc | ...
```

#### `extract_flat(profiles, base_path, filters=None, max_depth=10)`

Extract all values under a base path into a fully flattened wide-format DataFrame.

**Returns:** `pd.DataFrame` with one row per subject, all nested keys as columns.

---

### Path Resolution Functions

#### `resolve_path(data, path, default=None)`

Get value from nested dict using dot-notation.

```python
value = resolve_path(profile, "sensor_metrics.emg.EMG_weekly_metrics.left.EMG_apdf.active.p50")
```

#### `path_exists(data, path)`

Check if a path exists.

**Returns:** `bool`

#### `list_keys_at_path(data, path)`

List all keys at a given path.

**Returns:** `List[str]`

```python
dates = list_keys_at_path(profile, "sensor_metrics.emg")
# ['13-10-2025', '14-10-2025', ..., 'EMG_weekly_metrics']
```

---

### Filtering

#### `create_filters(...)`

Create a filters dictionary for controlling extraction.

| Parameter | Type | Description |
|-----------|------|-------------|
| `subject_ids` | `List[str]` | Include only these subjects |
| `exclude_subjects` | `List[str]` | Exclude these subjects |
| `groups` | `List[str]` | Filter by meta_data.group |
| `date_range` | `Tuple[str, str]` | `(start, end)` dates in YYYY-MM-DD format |
| `require_keys` | `List[str]` | Only include subjects with these paths |
| `custom_filter` | `Callable` | Custom `(subject_id, profile) -> bool` function |

```python
from oh_parser import create_filters

filters = create_filters(
    subject_ids=["103", "104", "105"],
    require_keys=["sensor_metrics.emg.EMG_weekly_metrics"],
    date_range=("2025-10-01", "2025-10-31"),
)

df = extract_nested(profiles, ..., filters=filters)
```

---

## Usage Examples

### Example 1: Weekly EMG Summary

```python
from oh_parser import load_profiles, extract

profiles = load_profiles("E:/OH_profiles/")

df = extract(profiles, paths={
    # Left side
    "active_p10_L": "sensor_metrics.emg.EMG_weekly_metrics.left.EMG_apdf.active.p10",
    "active_p50_L": "sensor_metrics.emg.EMG_weekly_metrics.left.EMG_apdf.active.p50",
    "active_p90_L": "sensor_metrics.emg.EMG_weekly_metrics.left.EMG_apdf.active.p90",
    "rest_pct_L": "sensor_metrics.emg.EMG_weekly_metrics.left.EMG_rest_recovery.rest_percent",
    # Right side
    "active_p10_R": "sensor_metrics.emg.EMG_weekly_metrics.right.EMG_apdf.active.p10",
    "active_p50_R": "sensor_metrics.emg.EMG_weekly_metrics.right.EMG_apdf.active.p50",
    "active_p90_R": "sensor_metrics.emg.EMG_weekly_metrics.right.EMG_apdf.active.p90",
    "rest_pct_R": "sensor_metrics.emg.EMG_weekly_metrics.right.EMG_rest_recovery.rest_percent",
})
```

### Example 2: All Session-Level Data

```python
from oh_parser import load_profiles, extract_nested

profiles = load_profiles("E:/OH_profiles/")

df = extract_nested(
    profiles,
    base_path="sensor_metrics.emg",
    level_names=["date", "session", "side"],
    value_paths=[
        "EMG_session.*",
        "EMG_intensity.*",
        "EMG_apdf.active.*",
        "EMG_rest_recovery.*",
    ],
    exclude_patterns=["EMG_daily_metrics", "EMG_weekly_metrics"],
)
# Columns: subject_id, date, session, side, EMG_session.duration_s, ...
```

### Example 3: Daily Aggregates Only

```python
df = extract_nested(
    profiles,
    base_path="sensor_metrics.emg",
    level_names=["date", "side"],
    value_paths=["EMG_intensity.*", "EMG_rest_recovery.*"],
    exclude_patterns=["EMG_weekly_metrics"],
)
# Only matches paths containing EMG_daily_metrics
```

### Example 4: Filter by Data Availability

```python
from oh_parser import create_filters, summarize_profiles

# First, check which subjects have EMG data
summary = summarize_profiles(profiles)
print(summary[summary['has_EMG_weekly_metrics'] == True])

# Then filter to only those subjects
filters = create_filters(
    require_keys=["sensor_metrics.emg.EMG_weekly_metrics.left"],
)
df = extract(profiles, paths={...}, filters=filters)
```

---

## Path Syntax

### Dot Notation

Navigate nested structures with dots:

```
sensor_metrics.emg.EMG_weekly_metrics.left.EMG_apdf.active.p50
```

### Wildcards in `value_paths`

Use `.*` to extract all keys under a path:

```python
value_paths=["EMG_intensity.*"]
# Extracts: EMG_intensity.mean_percent_mvc, EMG_intensity.max_percent_mvc, ...
```

### Wildcards in `base_path` (via level_names)

The `level_names` parameter implicitly creates wildcards:

```python
base_path="sensor_metrics.emg"
level_names=["date", "session", "side"]
# Expands to: sensor_metrics.emg.{date}.{session}.{side}
```

### Exclusion Patterns

Glob-style patterns to skip certain keys:

```python
exclude_patterns=["EMG_*_metrics"]  # Skips EMG_daily_metrics, EMG_weekly_metrics
exclude_patterns=["*_aggregate"]    # Skips anything ending in _aggregate
```

---

## EMG Data Reference

### Metric Groups

#### `EMG_session` - Session Metadata

| Key | Type | Unit | Description |
|-----|------|------|-------------|
| `duration_s` | float | seconds | Total recording duration |
| `mvc_peak` | float | mV | MVC value used for normalization |
| `active_duration_s` | float | seconds | Time above rest threshold |

#### `EMG_intensity` - Intensity Metrics

| Key | Type | Unit | Description |
|-----|------|------|-------------|
| `mean_percent_mvc` | float | %MVC | Mean amplitude |
| `max_percent_mvc` | float | %MVC | Peak amplitude |
| `min_percent_mvc` | float | %MVC | Minimum amplitude |
| `iemg_percent_seconds` | float | %MVC·s | Integrated EMG (area under curve) |

#### `EMG_apdf` - Amplitude Probability Distribution Function

Nested structure with `full` (all samples) and `active` (samples ≥ 0.5% MVC):

| Key | Type | Unit | Description |
|-----|------|------|-------------|
| `full.p10` | float | %MVC | 10th percentile (all samples) |
| `full.p50` | float | %MVC | 50th percentile / median |
| `full.p90` | float | %MVC | 90th percentile |
| `active.p10` | float | %MVC | 10th percentile (active only) |
| `active.p50` | float | %MVC | 50th percentile (active only) |
| `active.p90` | float | %MVC | 90th percentile (active only) |

#### `EMG_rest_recovery` - Rest/Recovery Metrics

| Key | Type | Unit | Description |
|-----|------|------|-------------|
| `rest_percent` | float | % | Time below 0.5% MVC threshold |
| `gap_frequency_per_minute` | float | gaps/min | Micro-break frequency |
| `max_sustained_activity_s` | float | seconds | Longest continuous active period |
| `gap_count` | int | count | Total number of rest gaps |

#### `EMG_relative_bins` - Relative Intensity Distribution

Percentage of active time in each intensity bin (relative to subject's weekly baseline):

| Key | Type | Unit | Description |
|-----|------|------|-------------|
| `below_usual_pct` | float | % | Time below weekly P10 |
| `typical_low_pct` | float | % | Time between P10-P50 |
| `typical_high_pct` | float | % | Time between P50-P90 |
| `high_for_you_pct` | float | % | Time above weekly P90 |

### Aggregation Levels

| Level | Location | Description |
|-------|----------|-------------|
| **Session** | `emg.{date}.{session}.{side}` | Per-recording metrics |
| **Daily** | `emg.{date}.EMG_daily_metrics.{side}` | Duration-weighted daily average |
| **Weekly** | `emg.EMG_weekly_metrics.{side}` | Duration-weighted weekly average |

---

## Utility Functions

### `flatten_dict(data, sep=".", max_depth=None)`

Flatten nested dict to single-level with dot-notation keys.

### `safe_get(data, keys, default=None)`

Safely navigate nested dict with list of keys.

### `print_tree(data, max_depth=4, show_values=False)`

Pretty-print dict as tree structure.

---

## Notes

- **Date format**: Dates in EMG paths use `DD-MM-YYYY` format
- **Time format**: Session times use `HH-MM-SS` format
- **Null values**: Some metrics may be `null`/`None` (e.g., relative bins at weekly level)
- **Sides**: EMG data has separate entries for `left` and `right` sides

---

*Generated for oh_parser module - PrevOccupAI+ Project*
