import pandas as pd

def shorten_axis_labels(cols, group_prefix):
    """
    Remove the group prefix from column names for plotting.

    Example:
    Noise_distributions.Ruído baixo -> Ruído baixo
    HR_BPM_stats.mean -> mean
    """
    return {
        c: c.replace(group_prefix + ".", "")
        for c in cols
    }

def add_session_number(df, date_col="date", session_col="session"):
    """
    Add a session number column based on the order of the session time.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with 'date' and 'session' columns.
    date_col : str
        Name of the date column (default 'date').
    session_col : str
        Name of the session column (default 'session').

    Returns
    -------
    pd.DataFrame
        DataFrame with a new column "n_session" (1, 2, 3, ...).
    """
    df = df.copy()

    # Convert date & session to datetime
    df[date_col] = pd.to_datetime(df[date_col], format="%d-%m-%Y", errors="coerce")
    df[session_col] = pd.to_datetime(df[session_col], format="%H-%M-%S", errors="coerce").dt.time

    # Create session order per subject and day
    df["n_session"] = (
        df.sort_values(session_col)
          .groupby([ "subject_id", date_col ])
          .cumcount() + 1
    )

    return df

def add_weekday_pt(df, date_col="date"):
    """
    Add a Portuguese weekday column to a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with a date column in "DD-MM-YYYY" format.
    date_col : str, default "date"
        Name of the date column.

    Returns
    -------
    pd.DataFrame
        DataFrame with a new column "weekday_pt" containing
        weekday names in Portuguese.
    """
    df[date_col] = pd.to_datetime(df[date_col], format="%d-%m-%Y", errors="coerce")
    df["weekday_num"] = df[date_col].dt.weekday
    return df

def autofill_nan_groups(df: pd.DataFrame, min_group_size: int = 2):
    """
    Fill NaN values within groups of related columns based on a shared prefix.

    This function only applies to columns that contain "distributions" in the
    column name.

    For each group of columns that share the same prefix (everything before the
    last '.'), the behavior is:

    - If ALL columns in the group are NaN for a given row → keep NaN
    - If ANY column in the group has a value for a given row → replace NaN
      values in the group with 0 for that row

    :param df: pd.DataFrame
        DataFrame containing flattened metric columns (e.g., "Noise_statistics.mean").
    :param min_group_size : int, default 2
        Minimum number of columns required to form a group. Groups with fewer
        columns are ignored.

    :return: The modified DataFrame with NaNs filled according to the rule above.
    """

    # Select only distribution columns that contain a dot (flattened metric columns)
    metric_cols = [c for c in df.columns if "." in c and "distributions" in c]

    # Group columns by prefix (everything before the last '.')
    groups = {}
    for col in metric_cols:
        prefix = col.rsplit(".", 1)[0]
        groups.setdefault(prefix, []).append(col)

    for prefix, cols in groups.items():
        if len(cols) < min_group_size:
            continue  # Ignore groups that are too small

        # Identify rows where at least one column in the group is not NaN
        mask_any = df[cols].notna().any(axis=1)

        # Fill NaNs with 0 only for rows where some value exists in the group
        df.loc[mask_any, cols] = df.loc[mask_any, cols].fillna(0)

    return df

