import logging

import numpy as np
import pandas as pd


def calculate_pmt(repo_df: pd.DataFrame) -> tuple:
    """
    Calculate PR Merge Time (PMT) metrics

    Args:
        repo_df (pd.DataFrame): DataFrame containing PR events

    Returns:
        tuple: (median_time, pr_times DataFrame, percentile_values)
    """
    try:
        if not isinstance(repo_df, pd.DataFrame):
            return None, None, None

        if repo_df.empty:
            return None, None, None

        # Ensure 'time' is in datetime format
        repo_df["time"] = pd.to_datetime(repo_df["time"])

        # Filter for PR creation and merge events
        pr_created = repo_df[repo_df["event_type"] == "pr_created"][["pr_number", "time"]]
        pr_merged = repo_df[repo_df["event_type"] == "pr_merged"][["pr_number", "time"]]

        # Merge the two DataFrames on 'pr_number'
        pr_times = pd.merge(pr_created, pr_merged, on="pr_number", suffixes=("_created", "_merged"))

        if len(pr_times) == 0:
            return None, None, None

        # Calculate the time difference in hours
        pr_times["merge_time"] = (pr_times["time_merged"] - pr_times["time_created"]).dt.total_seconds() / 3600

        # Calculate metrics
        median_time = pr_times["merge_time"].median()
        percentile_values = np.percentile(pr_times["merge_time"], [25, 50, 75])

        return median_time, pr_times, percentile_values

    except Exception as e:
        logging.error(f"Error calculating PMT: {e}")
        return None, None, None
