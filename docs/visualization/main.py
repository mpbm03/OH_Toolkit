

from oh_parser import (
    load_profiles,
    list_subjects,
    extract_nested)
import pandas as pd

from data import extract_smartwatch_and_smartphone
from pairplot import pairplot_by_weekday, pairplot_by_weekday_and_session

OH_PROFILES_PATH = r"D:\Teste\metrics\Sara"

COMPONENTS = ("HR", "noise", "activity", "wrist")

if __name__ == '__main__':
    OH_PROFILES_PATH = r"D:\Teste\metrics\Sara"
    profiles = load_profiles(OH_PROFILES_PATH)

    subjects = list_subjects(profiles)
    print(f"Subjects: {subjects}")
    print(f"Total: {len(subjects)} subjects\n")

    df_smartwatch, df_smartphone = extract_smartwatch_and_smartphone(profiles, components=COMPONENTS)

    # Print columns of each DataFrame
    print("=== Smartwatch Columns ===")
    print(df_smartwatch.columns.tolist())
    print("\nSmartwatch shape:", df_smartwatch.shape)

    print("\n=== Smartphone Columns ===")
    print(df_smartphone.columns.tolist())
    print("\nSmartphone shape:", df_smartphone.shape)


    # SMARTPHONE pairplots per day
    pairplot_by_weekday(df_smartphone, "Noise_statistics")
    pairplot_by_weekday(df_smartphone, "Noise_distributions")
    pairplot_by_weekday(df_smartphone, "HAR_distributions")
    pairplot_by_weekday(df_smartphone, "HAR_durations")
    pairplot_by_weekday(df_smartphone, "HAR_steps")

    # SMARTWATCH pairplots per session
    pairplot_by_weekday_and_session(df_smartwatch, "HR_BPM_stats")
    pairplot_by_weekday_and_session(df_smartwatch, "HR_ratio_stats")
    pairplot_by_weekday_and_session(df_smartwatch, "HR_distributions")
    pairplot_by_weekday_and_session(df_smartwatch, "WRIST_significant")


