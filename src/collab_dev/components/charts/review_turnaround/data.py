import pandas as pd


def calculate_rtt_trends(repo_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Review Turnaround Time (RTT) trends over time

    Args:
        repo_df (pd.DataFrame): DataFrame containing PR events

    Returns:
        pd.DataFrame: DataFrame with RTT trends
    """
    try:
        if repo_df.empty:
            return pd.DataFrame()

        # Convert time to datetime
        repo_df["time"] = pd.to_datetime(repo_df["time"])

        # Get PR creation and first review request times for each PR
        pr_created = (
            repo_df[repo_df["event_type"] == "pr_created"]
            .groupby("pr_number")
            .agg(
                {
                    "time": "first",
                    "pr_title": "first",  # Get PR title for hover info
                }
            )
        )
        review_requests = repo_df[repo_df["event_type"] == "review_requested"].groupby("pr_number")["time"].first()

        # Match PRs that have both creation and review request times
        matched_prs = pd.DataFrame(
            {
                "created_time": pr_created["time"],
                "pr_title": pr_created["pr_title"],
                "review_requested_time": review_requests,
            }
        ).dropna()

        if matched_prs.empty:
            return pd.DataFrame()

        # Calculate time difference in hours
        matched_prs["turnaround_hours"] = (
            matched_prs["review_requested_time"] - matched_prs["created_time"]
        ).dt.total_seconds() / 3600

        # Sort by creation time
        matched_prs = matched_prs.sort_values("created_time")

        # Calculate rolling median (7 PRs window)
        matched_prs["rolling_median"] = matched_prs["turnaround_hours"].rolling(window=7, min_periods=1).median()

        return matched_prs

    except Exception:
        return pd.DataFrame()


def calculate_rtt(repo_df: pd.DataFrame) -> float:
    """Calculate overall median RTT"""
    try:
        trends_df = calculate_rtt_trends(repo_df)
        if trends_df.empty:
            return None
        return trends_df["turnaround_hours"].median()
    except Exception:
        return None


def calculate_rtt_stats(repo_df: pd.DataFrame) -> dict:
    """Calculate RTT statistics including thresholds and distribution"""
    try:
        if repo_df.empty:
            return None

        # Get all PRs created
        all_prs = repo_df[repo_df["event_type"] == "pr_created"]["pr_number"].nunique()

        # Initialize DataFrame to store turnaround times
        turnaround_times = []

        # Process each PR
        for pr_number in repo_df[repo_df["event_type"] == "pr_created"]["pr_number"].unique():
            pr_events = repo_df[repo_df["pr_number"] == pr_number].sort_values("time")

            # Get PR creation time
            pr_created_time = pr_events[pr_events["event_type"] == "pr_created"]["time"].iloc[0]

            # Check for review requests
            review_requests = pr_events[pr_events["event_type"] == "review_requested"]

            if not review_requests.empty:
                # For each review request, find the first review action from that reviewer
                for _, request in review_requests.iterrows():
                    request_time = request["time"]
                    requested_reviewer = request.get("target_user")  # Use get() to avoid KeyError

                    if not requested_reviewer:
                        continue

                    # Find first review action from this reviewer
                    review_actions = pr_events[
                        (pr_events["time"] > request_time)
                        & (pr_events["actor"] == requested_reviewer)
                        & (
                            pr_events["event_type"].isin(
                                ["review_approved", "review_changes_requested", "review_commented"]
                            )
                        )
                    ]

                    if not review_actions.empty:
                        first_review_time = review_actions["time"].iloc[0]
                        turnaround_hours = (first_review_time - request_time).total_seconds() / 3600
                        turnaround_times.append(turnaround_hours)
                        break  # Only consider the first successful review request
            else:
                # If no review request, measure from PR creation to first review action
                review_actions = pr_events[
                    pr_events["event_type"].isin(["review_approved", "review_changes_requested", "review_commented"])
                ]

                if not review_actions.empty:
                    first_review_time = review_actions["time"].iloc[0]
                    turnaround_hours = (first_review_time - pr_created_time).total_seconds() / 3600
                    turnaround_times.append(turnaround_hours)

        if not turnaround_times:
            return None

        turnaround_times = pd.Series(turnaround_times)

        # Calculate statistics
        stats = {
            "median_hours": turnaround_times.median(),
            "total_prs": all_prs,
            "reviewed_prs": len(turnaround_times),
            "review_rate": (len(turnaround_times) / all_prs) * 100,
            "within_1h": (turnaround_times <= 1).mean() * 100,
            "within_4h": (turnaround_times <= 4).mean() * 100,
            "within_24h": (turnaround_times <= 24).mean() * 100,
        }

        return stats

    except Exception:
        return None


def get_review_turnaround_data(repo_df: pd.DataFrame) -> dict:
    """Process raw data into review turnaround metrics"""
    try:
        stats = calculate_rtt_stats(repo_df)
        if not stats:
            return None

        # Convert numpy values to Python floats
        return {
            "median_hours": float(stats["median_hours"]),
            "total_prs": stats["total_prs"],
            "reviewed_prs": stats["reviewed_prs"],
            "review_rate": float(stats["review_rate"]),
            "within_1h": float(stats["within_1h"]),
            "within_4h": float(stats["within_4h"]),
            "within_24h": float(stats["within_24h"]),
        }

    except Exception:
        return None
