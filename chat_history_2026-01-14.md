# OH Parser - Chat History (January 12-14, 2026)

This document captures the development conversation for the OH Parser project.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Environment Setup](#2-environment-setup)
3. [Initial Pipeline Explanation](#3-initial-pipeline-explanation)
4. [Refactoring: Removing Classes](#4-refactoring-removing-classes)
5. [Detailed Pipeline Deep Dive](#5-detailed-pipeline-deep-dive)

---

## 1. Project Overview

### Summary

The **OH Parser** is a Python library for extracting data from **Occupational Health (OH) profile JSON files** into pandas DataFrames for statistical analysis.

### Key Capabilities

- **Load** JSON profiles from a directory (`load_profiles`)
- **Inspect** profile structure with tree visualization (`inspect_profile`)
- **Extract** data using dot-notation paths:
  - `extract()` → wide-format (one row per subject)
  - `extract_nested()` → long-format (one row per session/date/side)
- **Filter** by subjects, date ranges, groups, or data availability (`create_filters`)

### Data Structure

The OH profiles contain nested JSON with:
- **meta_data** - Subject info
- **questionnaires** - Single-instance and daily surveys
- **sensor_metrics** - EMG, heart rate, posture, noise, etc.

The **EMG data** is particularly complex with a 3-level nesting: `date → session → side`, plus daily/weekly aggregates.

### Project Files

| File | Purpose |
|------|---------|
| `loader.py` | Load OH profile JSONs |
| `path_resolver.py` | Dot-notation path navigation |
| `filters.py` | Subject/date filtering |
| `extract.py` | DataFrame extraction functions |
| `utils.py` | Utility functions |

---

## 2. Environment Setup

### Virtual Environment Creation

```powershell
cd c:\Users\gonba\oh_parser_project
python -m venv oh_parser_venv
```

### Installing Dependencies

```powershell
.\oh_parser_venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Installed packages:**
- pandas 2.3.3
- numpy 2.4.1
- python-dateutil 2.9.0.post0
- pytz 2025.2
- tzdata 2025.3

---

## 3. Initial Pipeline Explanation

### Architecture Overview

```
┌─────────────┐     ┌─────────────────┐     ┌──────────┐     ┌─────────────┐
│   loader    │ ──▶ │  path_resolver  │ ──▶ │ filters  │ ──▶ │   extract   │ ──▶ DataFrame
│  (JSON I/O) │     │ (dot-notation)  │     │ (subset) │     │  (output)   │
└─────────────┘     └─────────────────┘     └──────────┘     └─────────────┘
                            ▲
                            │
                     ┌──────┴──────┐
                     │    utils    │
                     │  (helpers)  │
                     └─────────────┘
```

### Step 1: Loading Profiles (loader.py)

**Flow:**
```
Directory → discover_oh_profiles() → load_profile() → Dict[subject_id, profile]
```

**Functions:**

| Function | Purpose |
|----------|---------|
| `discover_oh_profiles(directory)` | Scans directory for files matching `*_OH_profile.json` |
| `extract_subject_id(filepath)` | Extracts `"103"` from `"103_OH_profile.json"` |
| `load_profile(filepath)` | Reads single JSON file into Python dict |
| `load_profiles(directory)` | **Main entry point** - loads all profiles into `{subject_id: profile_dict}` |

### Step 2: Path Resolution (path_resolver.py)

Navigates **deeply nested JSON** using **dot-notation paths**.

```python
# Instead of:
profile["sensor_metrics"]["emg"]["EMG_weekly_metrics"]["left"]["EMG_apdf"]["active"]["p50"]

# You write:
resolve_path(profile, "sensor_metrics.emg.EMG_weekly_metrics.left.EMG_apdf.active.p50")
```

**Functions:**

| Function | Purpose |
|----------|---------|
| `resolve_path(data, path)` | Navigate to value using dot-notation |
| `path_exists(data, path)` | Check if a path exists (returns `True`/`False`) |
| `list_keys_at_path(data, path)` | Get all keys at a path |
| `expand_wildcards(data, path, level_names)` | **Key function** - expands `*` wildcards in paths |

### Step 3: Filtering (filters.py)

Controls **which subjects and records** are included in extraction.

**`create_filters()` function:**
```python
filters = create_filters(
    subject_ids=["103", "104"],        # Whitelist specific subjects
    exclude_subjects=["999"],          # Blacklist specific subjects
    groups=["control", "treatment"],   # Filter by meta_data.group
    date_range=("2025-10-01", "2025-10-31"),  # Date filter
    require_keys=["sensor_metrics.emg"],      # Must have these paths
    custom_filter=lambda sid, p: True,        # Custom function
)
```

### Step 4: Data Extraction (extract.py)

Three extraction modes:

| Mode | Function | Output Shape | Use Case |
|------|----------|--------------|----------|
| **A** | `extract()` | Wide (1 row/subject) | Specific known paths |
| **B** | `extract_nested()` | Long (1 row/leaf) | Dynamic keys (dates, sessions) |
| **C** | `extract_flat()` | Wide (1 row/subject) | All paths under base |

---

## 4. Refactoring: Removing Classes

### User Request
> "I don't want to use classes, correct that. I'm only using functions"

### Changes Made

#### Before (dataclass):
```python
@dataclass
class ExtractionFilters:
    subject_ids: Optional[List[str]] = None
    exclude_subjects: Optional[List[str]] = None
    groups: Optional[List[str]] = None
    date_range: Optional[Tuple[str, str]] = None
    require_keys: Optional[List[str]] = None
    custom_filter: Optional[Callable[[str, dict], bool]] = None
```

#### After (function returning dict):
```python
def create_filters(
    subject_ids: Optional[List[str]] = None,
    exclude_subjects: Optional[List[str]] = None,
    groups: Optional[List[str]] = None,
    date_range: Optional[Tuple[str, str]] = None,
    require_keys: Optional[List[str]] = None,
    custom_filter: Optional[Callable[[str, dict], bool]] = None,
) -> Dict[str, Any]:
    return {
        "subject_ids": subject_ids,
        "exclude_subjects": exclude_subjects,
        "groups": groups,
        "date_range": date_range,
        "require_keys": require_keys,
        "custom_filter": custom_filter,
    }
```

### Files Modified

1. **filters.py:**
   - Removed `@dataclass` and `ExtractionFilters` class
   - Added `create_filters()` function
   - Updated `apply_subject_filters()` to use `dict.get()` instead of attribute access

2. **extract.py:**
   - Updated all type hints from `ExtractionFilters` to `Dict[str, Any]`
   - Updated `_extract_levels()` to use dict access for `date_range`

3. **__init__.py:**
   - Changed export from `ExtractionFilters` to `create_filters`

4. **OH_PARSER_DOCUMENTATION.md:**
   - Updated all documentation and examples

### Verification

```powershell
python -c "from oh_parser import create_filters; f = create_filters(subject_ids=['103']); print(f)"
# Output: {'subject_ids': ['103'], 'exclude_subjects': None, 'groups': None, 'date_range': None, 'require_keys': None, 'custom_filter': None}
```

### Result
The `oh_parser` module is now **100% function-based** — just pure functions and dictionaries.

---

## 5. Detailed Pipeline Deep Dive

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              OH PARSER PIPELINE                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│   │   LAYER 1    │    │   LAYER 2    │    │   LAYER 3    │    │   LAYER 4    │  │
│   │              │    │              │    │              │    │              │  │
│   │  loader.py   │───▶│   utils.py   │───▶│  filters.py  │───▶│  extract.py  │  │
│   │              │    │              │    │              │    │              │  │
│   │  JSON I/O    │    │   Helpers    │    │   Subset     │    │  DataFrame   │  │
│   └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘  │
│                              │                                                   │
│                              ▼                                                   │
│                     ┌──────────────────┐                                         │
│                     │  path_resolver.py │                                        │
│                     │   Dot-notation    │                                        │
│                     │    Navigation     │                                        │
│                     └──────────────────┘                                         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Module Dependency Graph

```
                    ┌─────────────────┐
                    │    __init__.py   │  ◄── Public API
                    └────────┬────────┘
                             │ imports from
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   loader.py   │   │  extract.py   │   │  filters.py   │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        │                   ▼                   │
        │           ┌───────────────┐           │
        │           │path_resolver.py│◄──────────┘
        │           └───────┬───────┘
        │                   │
        ▼                   ▼
┌─────────────────────────────────────┐
│             utils.py                 │  ◄── Foundation layer
│  safe_get, flatten_dict, is_date_key│
└─────────────────────────────────────┘
```

---

### LAYER 1: Data Loading (loader.py)

#### Purpose
Transform raw JSON files on disk into an in-memory Python dictionary structure.

#### Data Flow
```
Directory on Disk          discover_oh_profiles()         load_profile()            In-Memory Dict
─────────────────          ───────────────────────        ─────────────             ──────────────
                                                          
E:/OH_profiles/            [Path("103_OH_profile.json"),  json.load() for each      {"103": {...},
├── 103_OH_profile.json ──▶ Path("104_OH_profile.json"), ───────────────────────▶   "104": {...},
├── 104_OH_profile.json     Path("105_OH_profile.json")]                            "105": {...}}
└── 105_OH_profile.json
```

#### Function: `discover_oh_profiles(directory)`
```python
def discover_oh_profiles(directory):
    dir_path = Path(directory)
    
    # Step 1: Validate directory exists
    if not dir_path.exists():
        raise FileNotFoundError(...)
    
    # Step 2: Use glob pattern to find matching files
    # Pattern: *_OH_profile.json
    profiles = list(dir_path.glob(f"*{OH_PROFILE_SUFFIX}"))
    
    # Step 3: Sort for consistent ordering
    return sorted(profiles)
```

**Glob matching:**
```
Pattern: *_OH_profile.json

Matches:                      Does NOT match:
✓ 103_OH_profile.json         ✗ 103_profile.json
✓ subject_1_OH_profile.json   ✗ OH_profile.json
✓ ABC_OH_profile.json         ✗ 103_OH_profile.txt
```

#### Function: `extract_subject_id(filepath)`
```python
# Input:  Path("E:/OH_profiles/103_OH_profile.json")
# Output: "103"

filename = "103_OH_profile.json"
suffix = "_OH_profile.json"  # 16 characters

# String slicing: filename[:-16]
subject_id = filename[:-len(suffix)]  # "103"
```

#### Function: `load_profiles(directory, subject_ids, verbose)`

```python
def load_profiles(directory, subject_ids=None, verbose=True):
    # Step 1: Get all profile paths
    profile_paths = discover_oh_profiles(dir_path)
    # → [Path("103_OH_profile.json"), Path("104_OH_profile.json"), ...]
    
    profiles = {}
    errors = []
    
    # Step 2: Iterate and load each
    for path in profile_paths:
        subject_id = extract_subject_id(path)  # "103"
        
        # Step 3: Optional filtering (early exit)
        if subject_ids is not None and subject_id not in subject_ids:
            continue  # Skip this file entirely
        
        # Step 4: Load with error handling
        try:
            profiles[subject_id] = load_profile(path)
        except json.JSONDecodeError as e:
            errors.append(f"{subject_id}: JSON decode error")
        except Exception as e:
            errors.append(f"{subject_id}: {e}")
    
    # Step 5: Report results
    if verbose:
        print(f"[oh_parser] Loaded {len(profiles)} OH profiles")
    
    return profiles
    # → {"103": {full profile dict}, "104": {full profile dict}, ...}
```

---

### LAYER 2: Utility Functions (utils.py)

#### Purpose
Low-level primitives for dictionary manipulation used by all other modules.

#### Function: `safe_get(data, keys, default)`

**Problem it solves:**
```python
# Traditional approach - crashes if any key is missing:
profile["sensor_metrics"]["emg"]["EMG_weekly_metrics"]["left"]
# KeyError: 'emg'  ← if emg doesn't exist

# safe_get approach - returns default instead:
safe_get(profile, ["sensor_metrics", "emg", "EMG_weekly_metrics", "left"], default=None)
# → None (no crash)
```

**Implementation:**
```python
def safe_get(data, keys, default=None):
    current = data  # Start at root
    
    for key in keys:
        # Guard 1: Is current still a dict?
        if not isinstance(current, dict):
            return default
        
        # Guard 2: Does key exist?
        if key not in current:
            return default
        
        # Navigate deeper
        current = current[key]
    
    return current  # Success - return the value
```

**Execution trace:**
```
Input: safe_get({"a": {"b": {"c": 42}}}, ["a", "b", "c"])

Step 1: current = {"a": {"b": {"c": 42}}}
        key = "a"
        current = {"b": {"c": 42}}

Step 2: current = {"b": {"c": 42}}
        key = "b"
        current = {"c": 42}

Step 3: current = {"c": 42}
        key = "c"
        current = 42

Return: 42
```

#### Function: `flatten_dict(data, parent_key, sep, max_depth)`

**Purpose:** Convert deeply nested dicts into flat dicts with dot-notation keys.

```python
# Input (nested):
{
    "EMG_intensity": {
        "mean_percent_mvc": 15.3,
        "max_percent_mvc": 45.2
    },
    "EMG_rest_recovery": {
        "rest_percent": 22.1
    }
}

# Output (flattened):
{
    "EMG_intensity.mean_percent_mvc": 15.3,
    "EMG_intensity.max_percent_mvc": 45.2,
    "EMG_rest_recovery.rest_percent": 22.1
}
```

**Recursion visualization:**
```
flatten_dict({"a": {"b": {"c": 1}, "d": 2}})
│
├─ key="a", value={"b": {"c": 1}, "d": 2}  (is dict → recurse)
│  │
│  ├─ flatten_dict({"b": {"c": 1}, "d": 2}, parent_key="a")
│  │  │
│  │  ├─ key="b", value={"c": 1}  (is dict → recurse)
│  │  │  │
│  │  │  └─ flatten_dict({"c": 1}, parent_key="a.b")
│  │  │     │
│  │  │     └─ key="c", value=1  (not dict → store)
│  │  │        items["a.b.c"] = 1
│  │  │
│  │  └─ key="d", value=2  (not dict → store)
│  │     items["a.d"] = 2
│
└─ Result: {"a.b.c": 1, "a.d": 2}
```

#### Function: `is_date_key(key)`

```python
def is_date_key(key: str) -> bool:
    # Must be exactly 10 characters: YYYY-MM-DD
    if len(key) != 10:
        return False
    
    parts = key.split("-")  # ["2025", "01", "15"]
    if len(parts) != 3:
        return False
    
    try:
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        # Validate ranges
        return 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31
    except ValueError:
        return False
```

**Examples:**
```
is_date_key("2025-01-15") → True
is_date_key("15-01-2025") → False (wrong order)
is_date_key("EMG_weekly_metrics") → False (wrong length)
is_date_key("2025-13-01") → False (month > 12)
```

---

### LAYER 3: Path Resolution (path_resolver.py)

#### Purpose
Navigate nested dictionaries using human-readable dot-notation strings.

#### Function: `resolve_path(data, path, default)`

**Implementation:**
```python
def resolve_path(data, path, default=None):
    if not path:          # Empty path = return root
        return data
    
    keys = path.split(".")  # "a.b.c" → ["a", "b", "c"]
    return safe_get(data, keys, default)  # Delegate to safe_get
```

**Full execution trace:**
```
Input: resolve_path(profile, "sensor_metrics.emg.EMG_weekly_metrics.left.EMG_apdf.active.p50")

Step 1: Split path
        keys = ["sensor_metrics", "emg", "EMG_weekly_metrics", "left", "EMG_apdf", "active", "p50"]

Step 2: Call safe_get(profile, keys)
        
        Iteration 1: current = profile["sensor_metrics"]
        Iteration 2: current = current["emg"]
        Iteration 3: current = current["EMG_weekly_metrics"]
        Iteration 4: current = current["left"]
        Iteration 5: current = current["EMG_apdf"]
        Iteration 6: current = current["active"]
        Iteration 7: current = current["p50"] → 12.5

Return: 12.5
```

#### Function: `path_exists(data, path)`

```python
def path_exists(data, path):
    sentinel = object()  # Unique object that can't exist in data
    result = resolve_path(data, path, default=sentinel)
    return result is not sentinel  # True if we found something else
```

**Why use a sentinel?**
```python
# Problem: What if the actual value is None?
resolve_path({"a": None}, "a", default=None)  # Returns None
# Can't tell if "a" exists with None value, or doesn't exist!

# Solution: Use unique sentinel
sentinel = object()  # New unique object every time
resolve_path({"a": None}, "a", default=sentinel)  # Returns None (not sentinel)
# Now we know "a" exists because we didn't get sentinel back
```

#### Function: `expand_wildcards(data, path, level_names)`

**Purpose:** Iterate over all combinations when you don't know the exact keys.

```python
list(expand_wildcards(profile["sensor_metrics"], "emg.*.*.left", ["date", "session"]))
# Yields:
# ({'date': '2025-01-01', 'session': '10-00-00'}, <data at emg.2025-01-01.10-00-00.left>)
# ({'date': '2025-01-01', 'session': '14-30-00'}, <data at emg.2025-01-01.14-30-00.left>)
# ({'date': '2025-01-02', 'session': '09-00-00'}, <data at emg.2025-01-02.09-00-00.left>)
```

---

### LAYER 4: Filtering (filters.py)

#### Purpose
Control which subjects and records are included in extraction results.

#### Function: `create_filters(...)`

```python
def create_filters(
    subject_ids=None,        # Whitelist: ["103", "104"]
    exclude_subjects=None,   # Blacklist: ["999"]
    groups=None,             # Group filter: ["control", "treatment"]
    date_range=None,         # Date filter: ("2025-01-01", "2025-01-31")
    require_keys=None,       # Must have: ["sensor_metrics.emg"]
    custom_filter=None,      # Function: lambda sid, profile: ...
):
    return {
        "subject_ids": subject_ids,
        "exclude_subjects": exclude_subjects,
        "groups": groups,
        "date_range": date_range,
        "require_keys": require_keys,
        "custom_filter": custom_filter,
    }
```

#### Function: `apply_subject_filters(profiles, filters)`

**Filter chain (ALL conditions must pass):**

```
Subject "103" enters filtering pipeline
        │
        ▼
┌───────────────────────────────────────┐
│ 1. WHITELIST CHECK                    │
│    Is subject_ids set?                │
│    YES → Is "103" in list? ──NO──────▶ SKIP
│    NO  → Continue                     │
└───────────────────┬───────────────────┘
                    │ PASS
                    ▼
┌───────────────────────────────────────┐
│ 2. BLACKLIST CHECK                    │
│    Is exclude_subjects set?           │
│    YES → Is "103" in list? ──YES─────▶ SKIP
│    NO  → Continue                     │
└───────────────────┬───────────────────┘
                    │ PASS
                    ▼
┌───────────────────────────────────────┐
│ 3. GROUP CHECK                        │
│    Is groups set?                     │
│    YES → Get meta_data.group          │
│          Is group in list? ──NO──────▶ SKIP
│    NO  → Continue                     │
└───────────────────┬───────────────────┘
                    │ PASS
                    ▼
┌───────────────────────────────────────┐
│ 4. REQUIRED KEYS CHECK                │
│    Is require_keys set?               │
│    YES → Do ALL paths exist?          │
│          Any missing? ───────YES─────▶ SKIP
│    NO  → Continue                     │
└───────────────────┬───────────────────┘
                    │ PASS
                    ▼
┌───────────────────────────────────────┐
│ 5. CUSTOM FILTER CHECK                │
│    Is custom_filter set?              │
│    YES → Call custom_filter("103", p) │
│          Returns False? ─────────────▶ SKIP
│    NO  → Continue                     │
└───────────────────┬───────────────────┘
                    │ PASS
                    ▼
          ┌─────────────────┐
          │ INCLUDE SUBJECT │
          └─────────────────┘
```

#### Function: `filter_date_keys(keys, date_range)`

```python
# Input keys at emg level:
keys = ["2025-01-01", "2025-01-15", "2025-02-01", "EMG_weekly_metrics"]
date_range = ("2025-01-01", "2025-01-31")

# Output:
["2025-01-01", "2025-01-15", "EMG_weekly_metrics"]
# Note: "EMG_weekly_metrics" kept because it's not a date!
```

#### Function: `exclude_keys(keys, exclude_patterns)`

```python
# Input:
keys = ["2025-01-01", "EMG_daily_metrics", "EMG_weekly_metrics"]
exclude_patterns = ["EMG_*_metrics"]

# Pattern matching using fnmatch:
# "EMG_*_metrics" matches "EMG_daily_metrics" → EXCLUDE
# "EMG_*_metrics" matches "EMG_weekly_metrics" → EXCLUDE
# "EMG_*_metrics" doesn't match "2025-01-01" → KEEP

# Output:
["2025-01-01"]
```

---

### LAYER 5: Extraction (extract.py)

#### Three Extraction Modes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXTRACTION MODES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐           │
│  │    extract()     │  │ extract_nested() │  │  extract_flat()  │           │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────────┤           │
│  │ Wide format      │  │ Long format      │  │ Wide format      │           │
│  │ 1 row/subject    │  │ 1 row/leaf node  │  │ 1 row/subject    │           │
│  │ Specific paths   │  │ Nested iteration │  │ All paths        │           │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘           │
│                                                                              │
│  Use when:            Use when:            Use when:                         │
│  - You know exact     - Data has dynamic   - You want everything             │
│    paths to extract     keys (dates, times)  under a base path              │
│  - Summary stats      - Session-level data - Exploratory analysis            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

#### Mode A: `extract()` — Wide Format Extraction

**Output shape:** One row per subject, one column per extracted value.

```python
extract(profiles, paths={
    "age": "meta_data.age",
    "emg_p50_left": "sensor_metrics.emg.EMG_weekly_metrics.left.EMG_apdf.active.p50",
    "emg_p50_right": "sensor_metrics.emg.EMG_weekly_metrics.right.EMG_apdf.active.p50",
})
```

**Output DataFrame:**
| subject_id | age | emg_p50_left | emg_p50_right |
|------------|-----|--------------|---------------|
| 103        | 32  | 12.5         | 14.2          |
| 104        | 45  | 8.7          | 9.1           |
| 105        | 28  | 15.3         | 16.8          |

---

#### Mode B: `extract_nested()` — Long Format Extraction

**Output shape:** One row per leaf node (e.g., per session × side combination).

**The problem it solves:**
```
sensor_metrics.emg/
├── 2025-01-01/                    ← Dynamic key (date)
│   ├── 10-00-00/                  ← Dynamic key (session time)
│   │   ├── left/                  ← Dynamic key (side)
│   │   │   └── EMG_intensity: {mean_percent_mvc: 15.3, ...}
│   │   └── right/
│   │       └── EMG_intensity: {mean_percent_mvc: 14.8, ...}
│   └── 14-30-00/
│       ├── left/
│       └── right/
├── 2025-01-02/
│   └── ...
└── EMG_weekly_metrics/            ← Should be EXCLUDED
```

**Solution:**
```python
extract_nested(
    profiles,
    base_path="sensor_metrics.emg",
    level_names=["date", "session", "side"],  # 3 levels of nesting
    value_paths=["EMG_intensity.mean_percent_mvc"],
    exclude_patterns=["EMG_*_metrics"],  # Skip aggregates
)
```

**Output DataFrame:**
| subject_id | date | session | side | EMG_intensity.mean_percent_mvc |
|------------|------|---------|------|-------------------------------|
| 103 | 2025-01-01 | 10-00-00 | left | 15.3 |
| 103 | 2025-01-01 | 10-00-00 | right | 14.8 |
| 103 | 2025-01-01 | 14-30-00 | left | 18.2 |
| 103 | 2025-01-01 | 14-30-00 | right | 17.9 |

**Recursion visualization:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    _extract_levels() RECURSION                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Start: data = emg_data, level_idx = 0, context = {"subject_id": "103"}      │
│                                                                              │
│  Level 0 (date):                                                             │
│  ├─ keys = ["2025-01-01", "2025-01-02", "EMG_weekly_metrics"]                │
│  ├─ exclude_keys(keys, ["EMG_*_metrics"]) → ["2025-01-01", "2025-01-02"]     │
│  │                                                                           │
│  ├─ for key = "2025-01-01":                                                  │
│  │   context = {"subject_id": "103", "date": "2025-01-01"}                   │
│  │   │                                                                       │
│  │   Level 1 (session):                                                      │
│  │   ├─ keys = ["10-00-00", "14-30-00", "EMG_daily_metrics"]                 │
│  │   ├─ exclude_keys → ["10-00-00", "14-30-00"]                              │
│  │   │                                                                       │
│  │   ├─ for key = "10-00-00":                                                │
│  │   │   context = {..., "session": "10-00-00"}                              │
│  │   │   │                                                                   │
│  │   │   Level 2 (side):                                                     │
│  │   │   ├─ keys = ["left", "right"]                                         │
│  │   │   │                                                                   │
│  │   │   ├─ for key = "left":                                                │
│  │   │   │   context = {..., "side": "left"}                                 │
│  │   │   │   │                                                               │
│  │   │   │   Level 3 (LEAF - level_idx >= len(level_names)):                 │
│  │   │   │   ├─ Extract value_paths from current data                        │
│  │   │   │   ├─ row = {**context, "EMG_intensity.mean_percent_mvc": 15.3}    │
│  │   │   │   └─ rows.append(row)  ← ROW 1 CREATED                           │
│  │   │   │                                                                   │
│  │   │   └─ for key = "right":                                               │
│  │   │       └─ ... → ROW 2 CREATED                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

#### Mode C: `extract_flat()` — Full Flattening

**Output shape:** One row per subject, ALL nested keys become columns.

```python
extract_flat(profiles, base_path="sensor_metrics.emg.EMG_weekly_metrics")
```

**Output DataFrame:**
| subject_id | left.EMG_apdf.active.p10 | left.EMG_apdf.active.p50 | right.EMG_apdf.active.p10 | ... |
|------------|--------------------------|--------------------------|---------------------------|-----|
| 103        | 5.2                      | 12.5                     | 6.1                       | ... |
| 104        | 3.8                      | 8.7                      | 4.2                       | ... |

---

### Complete Pipeline Example

```python
from oh_parser import load_profiles, extract_nested, create_filters

# STEP 1: Load profiles
profiles = load_profiles("E:/OH_profiles/")
# Returns: {"103": {full dict}, "104": {full dict}, ...}

# STEP 2: Create filters
filters = create_filters(
    subject_ids=["103", "104"],
    date_range=("2025-01-01", "2025-01-15"),
    require_keys=["sensor_metrics.emg"],
)

# STEP 3: Extract nested data
df = extract_nested(
    profiles,
    base_path="sensor_metrics.emg",
    level_names=["date", "session", "side"],
    value_paths=["EMG_intensity.*"],
    exclude_patterns=["EMG_*_metrics"],
    filters=filters,
)

# Result: pandas DataFrame with all session-level EMG data
```

---

## Summary Table

| Module | Primary Functions | Data Flow |
|--------|-------------------|-----------|
| `loader.py` | `load_profiles()`, `discover_oh_profiles()` | Directory → Dict[subject_id, profile] |
| `utils.py` | `safe_get()`, `flatten_dict()`, `is_date_key()` | Dict manipulation primitives |
| `path_resolver.py` | `resolve_path()`, `path_exists()`, `expand_wildcards()` | Dot-notation navigation |
| `filters.py` | `create_filters()`, `apply_subject_filters()`, `exclude_keys()` | Subject/record filtering |
| `extract.py` | `extract()`, `extract_nested()`, `extract_flat()` | Dict → pandas DataFrame |

---

*Chat history exported on January 14, 2026*
