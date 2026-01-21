import seaborn as sns
import matplotlib.pyplot as plt

weekdays_pt = {
    0: "segunda-feira",
    1: "terça-feira",
    2: "quarta-feira",
    3: "quinta-feira",
    4: "sexta-feira",
    5: "sábado",
    6: "domingo"
}


def pairplot_by_weekday(df, group_prefix, hue="work_type", weekday_col="weekday_num"):
    """
    Create pairplots for a metric group, split by weekday.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to plot.
    group_prefix : str
        Prefix of columns to include, e.g., "Noise_statistics" or "HAR_distributions".
    hue : str
        Column used for color grouping (default "work_type").
    weekday_col : str
        Column containing weekday number.
    """
    cols = [c for c in df.columns if c.startswith(group_prefix)]
    if not cols:
        print(f"No columns found for prefix {group_prefix}")
        return

    for wd in sorted(df[weekday_col].dropna().unique()):
        df_plot = df[df[weekday_col] == wd]
        if df_plot.shape[0] < 2:
            continue

        # Rename column only for the plot (so legend shows "Local de trabalho")
        df_plot = df_plot.rename(columns={hue: "Local de trabalho"})
        hue_plot = "Local de trabalho"

        g = sns.pairplot(df_plot[cols + [hue_plot]], hue=hue_plot, diag_kind="kde")

        # Ajustar figura
        g.fig.set_size_inches(12, 10)
        g.fig.subplots_adjust(top=0.92, hspace=0.2, wspace=0.2)

        # Título
        g.fig.suptitle(f"{group_prefix} - {weekdays_pt[wd]}", fontsize=14)

        plt.show()


def pairplot_by_weekday_and_session(df, group_prefix, hue="work_type",
                                    weekday_col="weekday_num", session_col="n_session"):
    """
    Create pairplots for a metric group, split by weekday and session number.

    Example output:
    - Monday (session 1)
    - Monday (session 2)
    - Tuesday (session 1)
    - ...

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to plot.
    group_prefix : str
        Prefix of columns to include, e.g., "HR_BPM_stats" or "WRIST_significant".
    hue : str
        Column used for color grouping (default "work_type").
    weekday_col : str
        Column containing weekday number.
    session_col : str
        Column containing session number.
    """
    cols = [c for c in df.columns if c.startswith(group_prefix)]
    if not cols:
        print(f"No columns found for prefix {group_prefix}")
        return

    weekdays = sorted(df[weekday_col].dropna().unique())
    sessions = sorted(df[session_col].dropna().unique())

    for wd in weekdays:
        for ns in sessions:
            df_plot = df[(df[weekday_col] == wd) & (df[session_col] == ns)]

            if df_plot.shape[0] < 2:
                continue

            # Rename column only for the plot (so legend shows "Local de trabalho")
            df_plot = df_plot.rename(columns={hue: "Local de trabalho"})
            hue_plot = "Local de trabalho"

            g = sns.pairplot(df_plot[cols + [hue_plot]], hue=hue_plot, diag_kind="kde")

            # Ajustar figura
            g.fig.set_size_inches(12, 10)
            g.fig.subplots_adjust(top=0.92, hspace=0.2, wspace=0.2)

            # Título
            g.fig.suptitle(f"{group_prefix} - {weekdays_pt[wd]} (Sessão {ns})", fontsize=14)

            plt.show()