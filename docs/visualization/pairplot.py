import seaborn as sns
import matplotlib.pyplot as plt

from utils import shorten_axis_labels

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
    Axis labels are shortened by removing the group prefix.
    """
    cols = [c for c in df.columns if c.startswith(group_prefix)]
    if not cols:
        print(f"No columns found for prefix {group_prefix}")
        return

    rename_map = shorten_axis_labels(cols, group_prefix)

    for wd in sorted(df[weekday_col].dropna().unique()):
        df_plot = df[df[weekday_col] == wd]
        if df_plot.shape[0] < 2:
            continue

        df_plot = df_plot[cols + [hue]].rename(columns=rename_map)
        df_plot = df_plot.rename(columns={hue: "Local de trabalho"})

        g = sns.pairplot(
            df_plot,
            hue="Local de trabalho",
            diag_kind="kde"
        )

        g.fig.set_size_inches(12, 10)
        g.fig.subplots_adjust(top=0.9)
        g.fig.suptitle(f"{group_prefix} – {weekdays_pt[wd]}", fontsize=14)

        plt.show()

def pairplot_by_weekday_and_session(
    df,
    group_prefix,
    hue="work_type",
    weekday_col="weekday_num",
    session_col="n_session"
):
    """
    Create pairplots for a metric group, split by weekday and session number.
    Axis labels are shortened by removing the group prefix.
    """
    cols = [c for c in df.columns if c.startswith(group_prefix)]
    if not cols:
        print(f"No columns found for prefix {group_prefix}")
        return

    rename_map = shorten_axis_labels(cols, group_prefix)

    weekdays = sorted(df[weekday_col].dropna().unique())
    sessions = sorted(df[session_col].dropna().unique())

    for wd in weekdays:
        for ns in sessions:
            df_plot = df[
                (df[weekday_col] == wd) &
                (df[session_col] == ns)
            ]

            if df_plot.shape[0] < 2:
                continue

            df_plot = df_plot[cols + [hue]].rename(columns=rename_map)
            df_plot = df_plot.rename(columns={hue: "Local de trabalho"})

            g = sns.pairplot(
                df_plot,
                hue="Local de trabalho",
                diag_kind="kde"
            )

            g.fig.set_size_inches(12, 10)
            g.fig.subplots_adjust(top=0.9)
            g.fig.suptitle(
                f"{group_prefix} – {weekdays_pt[wd]} (Sessão {ns})",
                fontsize=14
            )

            plt.show()