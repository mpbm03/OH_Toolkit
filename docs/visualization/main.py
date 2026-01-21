

from oh_parser import (
    load_profiles,
    list_subjects,
    extract_nested)
import pandas as pd

from data import extract_smartwatch_and_smartphone

OH_PROFILES_PATH = r"D:\Teste\metrics\Sara"

COMPONENTS = ("HR", "noise", "activity")

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



