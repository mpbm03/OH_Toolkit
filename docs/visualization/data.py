
from oh_parser import (
    load_profiles,
    list_subjects,
    extract_nested)
import pandas as pd

from utils import autofill_nan_groups, add_weekday_pt, add_session_number

def extract_smartwatch_and_smartphone(profiles, components=("HR", "wrist", "noise", "activity")):
    """
    Extract smartwatch and smartphone metrics from OH profiles.

    Parameters
    ----------
    profiles : dict
        Dictionary of OH profiles loaded with load_profiles().
    components : tuple of str, optional
        Components to extract. Supported values:
        - "HR"        : Heart rate (smartwatch)
        - "wrist"     : Wrist activities (smartwatch)
        - "noise"     : Noise (smartphone)
        - "activity"  : Human activities (smartphone)

    Returns
    -------
    tuple
        (df_smartwatch, df_smartphone)
    """

    # ---------- SMARTWATCH ----------
    df_hr = pd.DataFrame()
    df_wrist = pd.DataFrame()

    if "HR" in components:
        df_hr = extract_nested(
            profiles,
            base_path="sensor_metrics.heart_rate",
            level_names=["date", "session"],
            value_paths=[
                "HR_BPM_stats.*",
                "HR_ratio_stats.*",
                "HR_distributions.*"
            ],
            exclude_patterns=["HR_timeline"]
        )
        df_hr = autofill_nan_groups(df_hr)

    if "wrist" in components:
        df_wrist = extract_nested(
            profiles,
            base_path="sensor_metrics.wrist_activities",
            level_names=["date", "session"],
            value_paths=[
                "WRIST_significant_rotation_percentage",
                "WRIST_significant_acceleration_percentage",
            ],
        )

    # Merge smartwatch components if both exist
    if not df_hr.empty and not df_wrist.empty:
        df_smartwatch = pd.merge(
            df_hr,
            df_wrist,
            on=["subject_id", "work_type", "date", "session"],
            how="outer"
        )
    elif not df_hr.empty:
        df_smartwatch = df_hr
    elif not df_wrist.empty:
        df_smartwatch = df_wrist
    else:
        df_smartwatch = pd.DataFrame()

    # Add weekday and session number column
    if not df_smartwatch.empty:
        df_smartwatch = add_weekday_pt(df_smartwatch, date_col="date")
        df_smartwatch = add_session_number(df_smartwatch, date_col="date", session_col="session")


    # ---------- SMARTPHONE ----------
    df_noise = pd.DataFrame()
    df_human = pd.DataFrame()

    if "noise" in components:
        df_noise = extract_nested(
            profiles,
            base_path="sensor_metrics.noise",
            level_names=["date", "session"],
            value_paths=[
                "Noise_statistics.*",
                "Noise_distributions.*",
                "Noise_durations.*",
            ],
            exclude_patterns=["Noise_timeline*"]
        )

    if "activity" in components:
        df_human = extract_nested(
            profiles,
            base_path="sensor_metrics.human_activities",
            level_names=["date", "session"],
            value_paths=[
                "HAR_distributions.*",
                "HAR_durations.*",
                "HAR_steps.*",
            ],
            exclude_patterns=["HAR_timeline*"]
        )

    # Merge smartphone components if both exist
    if not df_noise.empty and not df_human.empty:
        df_smartphone = pd.merge(
            df_human,
            df_noise,
            on=["subject_id", "work_type", "date", "session"],
            how="outer"
        )
    elif not df_noise.empty:
        df_smartphone = df_noise
    elif not df_human.empty:
        df_smartphone = df_human
    else:
        df_smartphone = pd.DataFrame()

    if not df_smartphone.empty:
        df_smartphone = autofill_nan_groups(df_smartphone)
        df_smartphone = add_weekday_pt(df_smartphone, date_col="date")

    return df_smartwatch, df_smartphone
