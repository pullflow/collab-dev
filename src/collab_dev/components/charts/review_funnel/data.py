import logging

import pandas as pd


def get_pr_review_stats(pr_summary: pd.DataFrame) -> dict:
    """
    Calculate review flow statistics from PR summary DataFrame

    Args:
        pr_summary (pd.DataFrame): DataFrame from load_repository_prs

    Returns:
        dict: Review statistics including counts of different review states
    """
    # Group by PR number to get unique PRs and their events
    pr_events = (
        pr_summary.groupby("pr_number")
        .agg(
            {
                "event_type": list,
                "time": "first",  # Keep first timestamp for reference
            }
        )
        .reset_index()
    )

    total_prs = len(pr_events)

    # Count different review states
    review_requested = sum("review_requested" in events for events in pr_events["event_type"])
    review_completed = sum(
        any(event in events for event in ["review_commented", "review_changes_requested", "review_approved"])
        and "review_requested" in events
        for events in pr_events["event_type"]
    )
    review_approved = sum(
        "review_approved" in events and "review_requested" in events for events in pr_events["event_type"]
    )
    approved_without_request = sum(
        "review_approved" in events and "review_requested" not in events for events in pr_events["event_type"]
    )
    merged_without_review = sum(
        not any(event in events for event in ["review_approved", "review_commented", "review_changes_requested"])
        for events in pr_events["event_type"]
    )

    return {
        "total_prs": total_prs,
        "review_requested": review_requested,
        "review_completed": review_completed,
        "review_approved": review_approved,
        "approved_without_review_request": approved_without_request,
        "merged_without_review": merged_without_review,
    }


def analyze_pr_review_flow(repo_df: pd.DataFrame) -> dict:
    """Analyze PR review flow metrics for a repository"""

    if repo_df.empty:
        return None

    return get_pr_review_stats(repo_df)


def get_simplified_pr_flow_stats(pr_summary: pd.DataFrame) -> dict:
    """
    Calculate simplified PR flow statistics with just created, reviewed, and approved stages

    Args:
        pr_summary (pd.DataFrame): DataFrame from load_repository_prs

    Returns:
        dict: Review statistics with basic flow stages
    """
    total_prs = len(pr_summary)

    # Count PRs that received any type of review
    reviewed_prs = sum(
        any(event in events for event in ["review_commented", "review_changes_requested", "review_approved"])
        for events in pr_summary["event_type"]
    )

    # Count PRs that were approved
    approved_prs = sum("review_approved" in events for events in pr_summary["event_type"])

    return {"total_prs": total_prs, "reviewed_prs": reviewed_prs, "approved_prs": approved_prs}


def analyze_simplified_pr_flow(repo_df: pd.DataFrame) -> dict:
    """Analyze simplified PR flow metrics for a repository"""

    if repo_df.empty:
        return None

    # Group by PR number to get unique PRs and their events
    pr_events = (
        repo_df.groupby("pr_number")
        .agg(
            {
                "event_type": list,
                "time": "first",  # Keep first timestamp for reference
            }
        )
        .reset_index()
    )

    return get_simplified_pr_flow_stats(pr_events)


def get_review_funnel_data(repo_df: pd.DataFrame) -> dict:
    """Process raw data into review funnel metrics"""

    if repo_df.empty:
        logging.debug("Empty repository dataframe")
        return None

    # Group by PR number to get unique PRs and their events
    pr_events = repo_df.groupby("pr_number").agg({"event_type": list, "time": "first"}).reset_index()

    logging.debug(f"PR events shape: {pr_events.shape}")

    total_prs = len(pr_events)

    # Count PRs that received any type of review
    reviewed_prs = sum(
        any(event in events for event in ["review_commented", "review_changes_requested", "review_approved"])
        for events in pr_events["event_type"]
    )

    # Count PRs that were approved
    approved_prs = sum("review_approved" in events for events in pr_events["event_type"])

    logging.debug(f"Total PRs: {total_prs}, Reviewed: {reviewed_prs}, Approved: {approved_prs}")

    if total_prs == 0:
        logging.debug("No PRs found")
        return None

    return {"total_prs": total_prs, "reviewed_prs": reviewed_prs, "approved_prs": approved_prs}
