"""
Data Preparation Module
=======================

Transforms OH Parser output into analysis-ready datasets with:
- Date harmonization (DD-MM-YYYY to datetime)
- Day index computation (ordinal within-subject)
- Side handling (separate, average, or both)
- Weekday extraction (for exploratory use)

Architecture Note:
    This module uses dictionaries instead of classes for data structures
    to maintain consistency with the oh_parser project style.
    
    AnalysisDataset is a TypedDict containing:
    - data: pandas DataFrame with tidy long-format data
    - outcome_vars: list of outcome column names
    - id_var, time_var: identifier columns
    - grouping_vars: additional grouping columns
    - sensor, level: metadata
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple, TypedDict, Union
import warnings

import pandas as pd
import numpy as np


# =============================================================================
# Date Parsing
# =============================================================================

def parse_date(date_str: str) -> Optional[pd.Timestamp]:
    """
    Parse date strings in multiple formats.
    
    Supports:
    - DD-MM-YYYY (EMG dates)
    - YYYY-MM-DD (questionnaire dates, ISO format)
    
    :param date_str: Date string to parse
    :returns: pandas Timestamp or None if parsing fails
    """
    formats = ["%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"]
    
    for fmt in formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except (ValueError, TypeError):
            continue
    
    # Last resort: let pandas try to infer
    try:
        return pd.to_datetime(date_str, errors="coerce")
    except Exception:
        return None


def _parse_date_column(series: pd.Series) -> pd.Series:
    """Parse a series of date strings to datetime."""
    return series.apply(parse_date)


# =============================================================================
# Analysis Dataset TypedDict
# =============================================================================

class AnalysisDataset(TypedDict):
    """
    Container for analysis-ready data with metadata.
    
    Keys:
        data: Tidy long-format DataFrame
        outcome_vars: List of outcome column names
        id_var: Subject identifier column (default: "subject_id")
        time_var: Time/date column (default: "date")
        grouping_vars: Additional grouping columns (e.g., ["side"])
        sensor: Source sensor (e.g., "emg", "heart_rate")
        level: Analysis level (e.g., "daily", "session")
    """
    data: pd.DataFrame
    outcome_vars: List[str]
    id_var: str
    time_var: str
    grouping_vars: List[str]
    sensor: str
    level: str


def create_analysis_dataset(
    data: pd.DataFrame,
    outcome_vars: List[str],
    id_var: str = "subject_id",
    time_var: str = "date",
    grouping_vars: Optional[List[str]] = None,
    sensor: str = "emg",
    level: str = "daily",
) -> AnalysisDataset:
    """
    Create an AnalysisDataset dictionary with validation.
    
    :param data: Tidy long-format DataFrame
    :param outcome_vars: List of outcome column names
    :param id_var: Subject identifier column (default: "subject_id")
    :param time_var: Time/date column (default: "date")
    :param grouping_vars: Additional grouping columns (e.g., ["side"])
    :param sensor: Source sensor (e.g., "emg", "heart_rate")
    :param level: Analysis level (e.g., "daily", "session")
    :returns: Validated AnalysisDataset dictionary
    """
    grouping_vars = grouping_vars or []
    
    # Validate
    ds: AnalysisDataset = {
        "data": data,
        "outcome_vars": outcome_vars,
        "id_var": id_var,
        "time_var": time_var,
        "grouping_vars": grouping_vars,
        "sensor": sensor,
        "level": level,
    }
    
    ds = validate_dataset(ds)
    return ds


def validate_dataset(ds: AnalysisDataset) -> AnalysisDataset:
    """
    Validate the dataset structure.
    
    :param ds: AnalysisDataset dictionary
    :returns: Validated AnalysisDataset (outcome_vars may be filtered)
    :raises ValueError: If required columns are missing
    """
    data = ds["data"]
    id_var = ds["id_var"]
    time_var = ds["time_var"]
    outcome_vars = ds["outcome_vars"]
    
    if id_var not in data.columns:
        raise ValueError(f"ID variable '{id_var}' not found in data")
    if time_var not in data.columns:
        raise ValueError(f"Time variable '{time_var}' not found in data")
    
    missing_outcomes = [v for v in outcome_vars if v not in data.columns]
    if missing_outcomes:
        warnings.warn(f"Outcome variables not found in data: {missing_outcomes}")
        ds["outcome_vars"] = [v for v in outcome_vars if v in data.columns]
    
    return ds


def get_n_subjects(ds: AnalysisDataset) -> int:
    """Get number of unique subjects in dataset."""
    return ds["data"][ds["id_var"]].nunique()


def get_n_observations(ds: AnalysisDataset) -> int:
    """Get total number of observations in dataset."""
    return len(ds["data"])


def get_date_range(ds: AnalysisDataset) -> Tuple[Any, Any]:
    """Get date range (min, max) from dataset."""
    dates = ds["data"][ds["time_var"]]
    return (dates.min(), dates.max())


def get_obs_per_subject(ds: AnalysisDataset) -> pd.Series:
    """Get number of observations per subject."""
    return ds["data"].groupby(ds["id_var"]).size()


def subset_dataset(
    ds: AnalysisDataset,
    outcomes: Optional[List[str]] = None,
    subjects: Optional[List[str]] = None,
    sides: Optional[List[str]] = None,
) -> AnalysisDataset:
    """
    Create a subset of the dataset.
    
    :param ds: AnalysisDataset dictionary
    :param outcomes: Subset of outcome variables
    :param subjects: Subset of subject IDs
    :param sides: Subset of sides (if "side" in grouping_vars)
    :returns: New AnalysisDataset with filtered data
    """
    df = ds["data"].copy()
    
    if subjects is not None:
        df = df[df[ds["id_var"]].isin(subjects)]
    
    if sides is not None and "side" in ds["grouping_vars"]:
        df = df[df["side"].isin(sides)]
    
    new_outcomes = outcomes if outcomes is not None else ds["outcome_vars"]
    
    return create_analysis_dataset(
        data=df,
        outcome_vars=new_outcomes,
        id_var=ds["id_var"],
        time_var=ds["time_var"],
        grouping_vars=ds["grouping_vars"],
        sensor=ds["sensor"],
        level=ds["level"],
    )


def describe_dataset(ds: AnalysisDataset) -> str:
    """
    Return a summary description of the dataset.
    
    :param ds: AnalysisDataset dictionary
    :returns: Human-readable summary string
    """
    date_range = get_date_range(ds)
    lines = [
        f"AnalysisDataset: {ds['sensor']} ({ds['level']} level)",
        f"  Subjects: {get_n_subjects(ds)}",
        f"  Observations: {get_n_observations(ds)}",
        f"  Date range: {date_range[0]} to {date_range[1]}",
        f"  Outcomes: {len(ds['outcome_vars'])} variables",
        f"  Grouping: {ds['grouping_vars']}",
    ]
    return "\n".join(lines)


# =============================================================================
# EMG Data Preparation
# =============================================================================

SideOption = Literal["left", "right", "both", "average"]


def prepare_daily_emg(
    profiles: Dict[str, dict],
    side: SideOption = "both",
    add_day_index: bool = True,
    add_weekday: bool = True,
) -> AnalysisDataset:
    """
    Prepare daily EMG metrics for analysis.
    
    Extracts EMG_daily_metrics from OH profiles and returns an analysis-ready
    dataset with parsed dates, day indices, and optional side handling.
    
    :param profiles: Dictionary mapping subject_id -> OH profile dict
    :param side: How to handle sides:
        - "left": Only left side data
        - "right": Only right side data
        - "both": Keep both sides as separate rows (default)
        - "average": Average across sides (only when both exist)
    :param add_day_index: Add within-subject day index (1, 2, 3, ...)
    :param add_weekday: Add weekday name column
    :returns: AnalysisDataset dictionary with daily EMG metrics
    
    Example:
        >>> from oh_parser import load_profiles
        >>> profiles = load_profiles("/path/to/OH_profiles")
        >>> ds = prepare_daily_emg(profiles, side="both")
        >>> print(describe_dataset(ds))
    """
    # Import here to avoid circular dependency
    from oh_parser import extract_nested
    
    # Extract daily EMG metrics
    df = extract_nested(
        profiles,
        base_path="sensor_metrics.emg",
        level_names=["date", "level", "side"],
        value_paths=[
            "EMG_session.*",
            "EMG_intensity.*",
            "EMG_apdf.full.*",
            "EMG_apdf.active.*",
            "EMG_rest_recovery.*",
            "EMG_relative_bins.*",
        ],
        flatten_values=True,
    )
    
    if df.empty:
        warnings.warn("No EMG data found in profiles")
        return create_analysis_dataset(
            data=pd.DataFrame(),
            outcome_vars=[],
            sensor="emg",
            level="daily",
        )
    
    # Filter to daily metrics only
    df = df[df["level"] == "EMG_daily_metrics"].copy()
    df = df.drop(columns=["level"])
    
    # Parse dates
    df["date"] = _parse_date_column(df["date"])
    
    # Remove rows with unparseable dates
    n_before = len(df)
    df = df.dropna(subset=["date"])
    if len(df) < n_before:
        warnings.warn(f"Dropped {n_before - len(df)} rows with unparseable dates")
    
    # Handle sides
    df, grouping_vars = _handle_sides(df, side)
    
    # Add day index (ordinal within subject)
    if add_day_index:
        df = _add_day_index(df)
    
    # Add weekday
    if add_weekday:
        df["weekday"] = df["date"].dt.day_name()
    
    # Sort for reproducibility
    sort_cols = ["subject_id", "date"]
    if "side" in df.columns:
        sort_cols.append("side")
    df = df.sort_values(sort_cols).reset_index(drop=True)
    
    # Identify outcome columns (exclude metadata columns)
    meta_cols = {"subject_id", "date", "side", "day_index", "weekday"}
    outcome_vars = [c for c in df.columns if c not in meta_cols]
    
    return create_analysis_dataset(
        data=df,
        outcome_vars=outcome_vars,
        id_var="subject_id",
        time_var="date",
        grouping_vars=grouping_vars,
        sensor="emg",
        level="daily",
    )


def _handle_sides(
    df: pd.DataFrame,
    side: SideOption,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Handle side filtering/averaging.
    
    :param df: DataFrame with "side" column
    :param side: Side handling option
    :returns: (processed_df, grouping_vars)
    """
    if "side" not in df.columns:
        return df, []
    
    if side == "left":
        df = df[df["side"] == "left"].copy()
        df = df.drop(columns=["side"])
        return df, []
    
    elif side == "right":
        df = df[df["side"] == "right"].copy()
        df = df.drop(columns=["side"])
        return df, []
    
    elif side == "both":
        return df, ["side"]
    
    elif side == "average":
        # Average across sides only when both exist
        meta_cols = ["subject_id", "date"]
        
        # Check which subject×date combinations have both sides
        side_counts = df.groupby(["subject_id", "date"])["side"].nunique()
        has_both = side_counts[side_counts == 2].index
        
        if len(has_both) == 0:
            warnings.warn("No subject×date combinations have both sides. Returning all data.")
            return df, ["side"]
        
        # Filter to only rows with both sides
        df_both = df.set_index(["subject_id", "date"])
        df_both = df_both.loc[df_both.index.isin(has_both)].reset_index()
        
        # Identify numeric columns for averaging
        numeric_cols = df_both.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c not in meta_cols]
        
        # Group and average
        df_avg = df_both.groupby(meta_cols)[numeric_cols].mean().reset_index()
        
        n_dropped = len(df) - len(df_both)
        if n_dropped > 0:
            warnings.warn(
                f"Dropped {n_dropped} rows where only one side existed. "
                f"Kept {len(df_avg)} averaged observations."
            )
        
        return df_avg, []
    
    else:
        raise ValueError(f"Unknown side option: {side}")


def _add_day_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add within-subject day index (ordinal: 1, 2, 3, ...).
    
    Days are ordered chronologically within each subject.
    """
    df = df.copy()
    
    # Compute day_index per subject using transform instead of apply
    # This avoids the FutureWarning about grouping columns
    df = df.sort_values(["subject_id", "date"])
    
    # Create a mapping of date to day index within each subject
    day_indices = []
    for _, group in df.groupby("subject_id", sort=False):
        unique_dates = group["date"].unique()
        date_to_idx = {d: i + 1 for i, d in enumerate(sorted(unique_dates))}
        day_indices.extend(group["date"].map(date_to_idx).tolist())
    
    df["day_index"] = day_indices
    df["day_index"] = df["day_index"].astype(int)
    
    return df


# =============================================================================
# Questionnaire Data Preparation (Conditional)
# =============================================================================

def prepare_daily_questionnaires(
    profiles: Dict[str, dict],
    domain: Optional[str] = None,
    add_day_index: bool = True,
    add_weekday: bool = True,
) -> Optional[AnalysisDataset]:
    """
    Prepare daily questionnaire data for analysis.
    
    Returns None if no questionnaire data is available (conditionally activated).
    
    :param profiles: Dictionary mapping subject_id -> OH profile dict
    :param domain: Questionnaire domain ("workload", "pain", or None for all)
    :param add_day_index: Add within-subject day index
    :param add_weekday: Add weekday name column
    :returns: AnalysisDataset dict or None if no data
    """
    # Import here to avoid circular dependency
    from oh_parser import extract_nested
    
    # Check if any profile has questionnaire data
    has_data = False
    for profile in profiles.values():
        dq = profile.get("daily_questionnaires", {})
        if domain:
            if dq.get(domain):
                has_data = True
                break
        else:
            if any(bool(v) for v in dq.values() if isinstance(v, dict)):
                has_data = True
                break
    
    if not has_data:
        # Conditionally deactivated - no data available
        return None
    
    # Build base path
    base_path = f"daily_questionnaires.{domain}" if domain else "daily_questionnaires"
    
    # Extract
    level_names = ["date"] if domain else ["domain", "date"]
    
    df = extract_nested(
        profiles,
        base_path=base_path,
        level_names=level_names,
        value_paths=["*"],
        flatten_values=True,
    )
    
    if df.empty:
        return None
    
    # Parse dates
    df["date"] = _parse_date_column(df["date"])
    df = df.dropna(subset=["date"])
    
    if df.empty:
        return None
    
    # Add day index
    if add_day_index:
        df = _add_day_index(df)
    
    # Add weekday
    if add_weekday:
        df["weekday"] = df["date"].dt.day_name()
    
    # Identify outcome columns
    meta_cols = {"subject_id", "date", "domain", "day_index", "weekday"}
    outcome_vars = [c for c in df.columns if c not in meta_cols]
    
    grouping_vars = ["domain"] if "domain" in df.columns else []
    
    return create_analysis_dataset(
        data=df,
        outcome_vars=outcome_vars,
        id_var="subject_id",
        time_var="date",
        grouping_vars=grouping_vars,
        sensor="questionnaire",
        level="daily",
    )


# =============================================================================
# Weekly Data Preparation
# =============================================================================

def prepare_weekly_emg(
    profiles: Dict[str, dict],
    side: SideOption = "both",
) -> AnalysisDataset:
    """
    Prepare weekly EMG aggregates for analysis.
    
    Note: Weekly data has only one observation per subject×side,
    so it's suitable for between-subject comparisons only.
    
    :param profiles: Dictionary mapping subject_id -> OH profile dict
    :param side: How to handle sides
    :returns: AnalysisDataset dict with weekly EMG metrics
    """
    from oh_parser import extract_flat
    
    df = extract_flat(profiles, base_path="sensor_metrics.emg.EMG_weekly_metrics")
    
    if df.empty:
        warnings.warn("No weekly EMG data found in profiles")
        return create_analysis_dataset(
            data=pd.DataFrame(),
            outcome_vars=[],
            sensor="emg",
            level="weekly",
        )
    
    # Reshape from wide to long (one row per side)
    # Current: columns like "left.EMG_apdf.active.p50", "right.EMG_apdf.active.p50"
    
    left_cols = [c for c in df.columns if c.startswith("left.")]
    right_cols = [c for c in df.columns if c.startswith("right.")]
    
    rows = []
    for _, row in df.iterrows():
        subject_id = row["subject_id"]
        
        # Left side
        if left_cols:
            left_row = {"subject_id": subject_id, "side": "left"}
            for c in left_cols:
                new_name = c.replace("left.", "")
                left_row[new_name] = row[c]
            rows.append(left_row)
        
        # Right side
        if right_cols:
            right_row = {"subject_id": subject_id, "side": "right"}
            for c in right_cols:
                new_name = c.replace("right.", "")
                right_row[new_name] = row[c]
            rows.append(right_row)
    
    df_long = pd.DataFrame(rows)
    
    # Handle sides
    df_long, grouping_vars = _handle_sides(df_long, side)
    
    # Identify outcome columns
    meta_cols = {"subject_id", "side"}
    outcome_vars = [c for c in df_long.columns if c not in meta_cols]
    
    return create_analysis_dataset(
        data=df_long,
        outcome_vars=outcome_vars,
        id_var="subject_id",
        time_var="subject_id",  # No time dimension for weekly
        grouping_vars=grouping_vars,
        sensor="emg",
        level="weekly",
    )
