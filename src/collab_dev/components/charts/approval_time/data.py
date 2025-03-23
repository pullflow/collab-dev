import logging  # Add this at the top

import numpy as np
import pandas as pd


def calculate_pat(repo_df: pd.DataFrame) -> float:
    """Calculate overall median PAT"""
    try:
        if repo_df.empty:
            return None

        # Convert time to datetime
        repo_df["time"] = pd.to_datetime(repo_df["time"])

        # Get review request and approval times for each PR
        review_requests = repo_df[repo_df["event_type"] == "review_requested"].groupby("pr_number")["time"].first()
        approvals = repo_df[repo_df["event_type"] == "review_approved"].groupby("pr_number")["time"].first()

        # Match PRs that have both request and approval
        matched_prs = pd.DataFrame({"request_time": review_requests, "approval_time": approvals}).dropna()

        if matched_prs.empty:
            return None

        # Calculate time difference in hours
        matched_prs["approval_time_hours"] = (
            matched_prs["approval_time"] - matched_prs["request_time"]
        ).dt.total_seconds() / 3600

        # Return median time
        return matched_prs["approval_time_hours"].median()

    except Exception as e:
        logging.error(f"Error calculating PAT: {e}")
        return None


def get_pr_size_category(total_lines_changed: int) -> str:
    """
    Categorize PR size based on total lines changed

    These categories provide a more accurate representation of PR complexity:
    - XS: <10 lines (minimal changes, very quick to review)
    - S: 10-99 lines (small changes, quick to review)
    - M: 100-499 lines (moderate changes, reasonable review time)
    - L: 500-999 lines (large changes, significant review time)
    - XL: 1000+ lines (extensive changes, challenging to review effectively)
    """
    if total_lines_changed < 10:
        return "XS (<10 lines)"
    elif total_lines_changed < 100:
        return "S (10-99 lines)"
    elif total_lines_changed < 500:
        return "M (100-499 lines)"
    elif total_lines_changed < 1000:
        return "L (500-999 lines)"
    else:
        return "XL (1000+ lines)"


def calculate_total_lines_changed(repo_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate total lines changed (added + deleted) for each PR
    """
    try:
        if repo_df.empty:
            return pd.DataFrame()

        # Group by PR number and calculate total lines changed
        pr_lines = (
            repo_df.groupby("pr_number")
            .agg(
                {
                    "lines_added": "max",  # Take the max value as it should be consistent for a PR
                    "lines_deleted": "max",
                }
            )
            .reset_index()
        )

        # Calculate total lines changed
        pr_lines["total_lines_changed"] = pr_lines["lines_added"] + pr_lines["lines_deleted"]

        return pr_lines[["pr_number", "total_lines_changed"]]

    except Exception:
        return pd.DataFrame()


def analyze_pr_size_distribution(repo_df: pd.DataFrame) -> dict:
    """
    Analyze the distribution of PR sizes based on line changes

    Returns a dictionary with:
    - percentiles: key percentiles of the distribution
    - histogram: counts of PRs in different line change ranges
    - category_counts: counts of PRs in each standardized category
    """
    try:
        if repo_df.empty:
            return {"percentiles": {}, "histogram": {}, "category_counts": {}}

        # Calculate total lines changed for each PR
        pr_lines = calculate_total_lines_changed(repo_df)

        if pr_lines.empty:
            return {"percentiles": {}, "histogram": {}, "category_counts": {}}

        # Get the total lines changed values
        total_lines = pr_lines["total_lines_changed"].dropna()

        if len(total_lines) == 0:
            return {"percentiles": {}, "histogram": {}, "category_counts": {}}

        # Calculate percentiles
        percentiles = {
            "min": total_lines.min(),
            "p10": total_lines.quantile(0.1),
            "p25": total_lines.quantile(0.25),
            "p50": total_lines.quantile(0.5),  # median
            "p75": total_lines.quantile(0.75),
            "p90": total_lines.quantile(0.9),
            "p95": total_lines.quantile(0.95),
            "p99": total_lines.quantile(0.99),
            "max": total_lines.max(),
        }

        # Create histogram with bins based on data range
        bins = [0, 10, 100, 500]
        if (total_lines >= 500).any():
            bins.append(1000)
        if (total_lines >= 1000).any():
            bins.append(int(total_lines.max()) + 1)

        # Create histogram
        hist_values, hist_bins = np.histogram(total_lines, bins=bins)

        histogram = {
            f"{int(hist_bins[i])}-{int(hist_bins[i + 1])}": int(hist_values[i]) for i in range(len(hist_values))
        }

        # Count PRs in each standardized category
        category_counts = {
            "XS (<10 lines)": len(total_lines[total_lines < 10]),
            "S (10-99 lines)": len(total_lines[(total_lines >= 10) & (total_lines < 100)]),
            "M (100-499 lines)": len(total_lines[(total_lines >= 100) & (total_lines < 500)]),
            "L (500-999 lines)": len(total_lines[(total_lines >= 500) & (total_lines < 1000)]),
            "XL (1000+ lines)": len(total_lines[total_lines >= 1000]),
        }

        return {
            "percentiles": {k: round(float(v), 1) for k, v in percentiles.items()},
            "histogram": histogram,
            "category_counts": category_counts,
        }

    except Exception:
        return {"percentiles": {}, "histogram": {}, "category_counts": {}}


def calculate_pat_by_size(repo_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate PR Approval Time (PAT) broken down by PR size based on line changes"""
    try:
        if repo_df.empty:
            return pd.DataFrame()

        # Convert time to datetime
        repo_df["time"] = pd.to_datetime(repo_df["time"])

        # Calculate total lines changed for each PR
        pr_lines = calculate_total_lines_changed(repo_df)

        if pr_lines.empty:
            return pd.DataFrame()

        # Get review request and approval times for each PR
        review_requests = repo_df[repo_df["event_type"] == "review_requested"].groupby("pr_number")["time"].first()
        approvals = repo_df[repo_df["event_type"] == "review_approved"].groupby("pr_number")["time"].first()

        # Match PRs that have both request and approval
        matched_prs = pd.DataFrame({"request_time": review_requests, "approval_time": approvals}).dropna()

        if matched_prs.empty:
            return pd.DataFrame()

        # Add total lines changed information
        matched_prs = matched_prs.reset_index().merge(pr_lines, on="pr_number", how="left").set_index("pr_number")

        # Calculate time difference in hours
        matched_prs["approval_time_hours"] = (
            matched_prs["approval_time"] - matched_prs["request_time"]
        ).dt.total_seconds() / 3600

        # Add size category
        matched_prs["size_category"] = matched_prs["total_lines_changed"].apply(get_pr_size_category)

        # Calculate stats by size category
        size_stats = (
            matched_prs.groupby("size_category")
            .agg({"approval_time_hours": ["median", "mean", "count"], "total_lines_changed": "mean"})
            .round(1)
        )

        # Flatten column names
        size_stats.columns = ["median_hours", "mean_hours", "pr_count", "avg_lines"]

        # Sort by size category in a logical order
        size_order = {
            "XS (<10 lines)": 0,
            "S (10-99 lines)": 1,
            "M (100-499 lines)": 2,
            "L (500-999 lines)": 3,
            "XL (1000+ lines)": 4,
        }

        return size_stats.reset_index().sort_values(
            by="size_category", key=lambda x: x.map(lambda cat: size_order.get(cat, 99))
        )

    except Exception:
        return pd.DataFrame()


def get_approval_time_data(repo_df):
    """Process raw data into approval time metrics"""
    logging.debug("Starting get_approval_time_data processing...")

    if repo_df.empty:
        logging.debug("Empty repository dataframe")
        return None

    # Get overall median approval time
    pat_hours = calculate_pat(repo_df)
    logging.debug(f"Overall PAT hours: {pat_hours}")

    if pat_hours is None:
        logging.debug("No PAT hours calculated")
        return None

    # Calculate PR size stats
    pr_lines = calculate_total_lines_changed(repo_df)

    if pr_lines.empty:
        logging.debug("No PR lines data")
        return None

    # Get review request and approval times for each PR
    review_requests = repo_df[repo_df["event_type"] == "review_requested"].groupby("pr_number")["time"].first()
    approvals = repo_df[repo_df["event_type"] == "review_approved"].groupby("pr_number")["time"].first()

    # Match PRs that have both request and approval
    matched_prs = pd.DataFrame({"request_time": review_requests, "approval_time": approvals}).dropna()

    if matched_prs.empty:
        logging.debug("No matched PRs with both request and approval")
        return None

    # Add size information
    matched_prs = matched_prs.reset_index().merge(pr_lines, on="pr_number", how="left")

    # Calculate approval time in hours
    matched_prs["approval_time_hours"] = (
        matched_prs["approval_time"] - matched_prs["request_time"]
    ).dt.total_seconds() / 3600

    # Add size categories
    matched_prs["size_category"] = matched_prs["total_lines_changed"].apply(get_pr_size_category)

    # Calculate stats by size category
    size_stats = (
        matched_prs.groupby("size_category")
        .agg({"approval_time_hours": ["median", "count"], "total_lines_changed": "mean"})
        .round(1)
    )

    # Flatten column names
    size_stats.columns = ["median_hours", "pr_count", "avg_lines"]
    size_stats = size_stats.reset_index()

    return {"overall_median": pat_hours, "size_stats": size_stats}
