import pandas as pd


def calculate_review_ratio_stats(repo_df: pd.DataFrame) -> dict:
    """Calculate PR review ratio statistics"""
    try:
        if repo_df.empty:
            return None

        # Group by PR number to get unique PRs and their events
        pr_summary = (
            repo_df.groupby("pr_number")
            .agg(
                {
                    "event_type": list,
                    "time": "first",  # Keep first timestamp for reference
                }
            )
            .reset_index()
        )

        # Count total PRs
        total_prs = len(pr_summary)

        # Count PRs that received a review (any type of review action)
        reviewed_prs = sum(
            any(event in events for event in ["review_commented", "review_approved", "review_changes_requested"])
            for events in pr_summary["event_type"]
        )

        # Calculate unreviewed PRs
        unreviewed_prs = total_prs - reviewed_prs

        # Calculate review percentage
        review_percentage = (reviewed_prs / total_prs * 100) if total_prs > 0 else 0

        return {
            "total_prs": total_prs,
            "reviewed_prs": reviewed_prs,
            "unreviewed_prs": unreviewed_prs,
            "review_percentage": review_percentage,
        }

    except Exception:
        return None


def get_review_merge_data(repo_df: pd.DataFrame) -> dict:
    """Process raw data into review merge metrics"""

    stats = calculate_review_ratio_stats(repo_df)
    if not stats:
        return None

    return stats
