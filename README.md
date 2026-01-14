# OH Parser

A generic parser for extracting data from Occupational Health (OH) profile JSON files into pandas DataFrames for statistical analysis.

## Features

- **Load** OH profile JSON files from a directory
- **Inspect** profile structure without knowing the schema
- **Extract** data using flexible dot-notation paths
- **Filter** by subjects, date ranges, or data availability
- **Wildcard support** for iterating over dynamic keys (dates, sessions, sides)

## Installation

```bash
pip install -r requirements.txt
```

Or simply:
```bash
pip install pandas
```

## Quick Start

```python
from oh_parser import load_profiles, extract, extract_nested

# Load all profiles
profiles = load_profiles("path/to/OH_profiles/")

# Extract specific values (one row per subject)
df = extract(profiles, paths={
    "emg_p50_left": "sensor_metrics.emg.EMG_weekly_metrics.left.EMG_apdf.active.p50",
    "emg_p50_right": "sensor_metrics.emg.EMG_weekly_metrics.right.EMG_apdf.active.p50",
})

# Extract nested data (one row per session)
df = extract_nested(
    profiles,
    base_path="sensor_metrics.emg",
    level_names=["date", "session", "side"],
    value_paths=["EMG_intensity.*", "EMG_rest_recovery.*"],
    exclude_patterns=["EMG_daily_metrics", "EMG_weekly_metrics"],
)
```

## Documentation

See [oh_parser/OH_PARSER_DOCUMENTATION.md](oh_parser/OH_PARSER_DOCUMENTATION.md) for complete API reference and usage examples.

## Project Structure

```
oh_parser_project/
├── README.md
├── requirements.txt
└── oh_parser/
    ├── __init__.py          # Public API exports
    ├── loader.py            # Load OH profile JSONs
    ├── path_resolver.py     # Dot-notation path navigation
    ├── filters.py           # Subject/date filtering
    ├── extract.py           # DataFrame extraction functions
    ├── utils.py             # Utility functions
    └── OH_PARSER_DOCUMENTATION.md
```

## Dependencies

- Python 3.9+
- pandas >= 1.5.0

## License

MIT
