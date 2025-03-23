import pandas as pd


def get_contribution_stats(repo_df: pd.DataFrame) -> dict:
    """
    Calculate contribution percentages and prepare statistics.
    TODO: This function is too slow. We may need to pre-calculate this data and store it in the database.
    """

    if repo_df.empty:
        return None

    # Get unique PRs and their first events to determine PR type
    pr_data = repo_df[repo_df["event_type"] == "pr_created"].drop_duplicates("pr_number")
    total_prs = len(pr_data)

    if total_prs == 0:
        return None

    # Count PRs by type using the database columns
    bot_prs = len(pr_data[pr_data["is_bot"]])
    non_bot_data = pr_data[~pr_data["is_bot"]]
    core_prs = len(non_bot_data[non_bot_data["is_core_team"]])
    community_prs = len(non_bot_data[~non_bot_data["is_core_team"]])

    # Calculate all stats needed for display
    stats = {
        "total_prs": total_prs,
        "core_prs": core_prs,
        "community_prs": community_prs,
        "bot_prs": bot_prs,
        "core_percentage": round((core_prs / total_prs * 100), 1) if total_prs > 0 else 0,
        "community_percentage": round((community_prs / total_prs * 100), 1) if total_prs > 0 else 0,
        "bot_percentage": round((bot_prs / total_prs * 100), 1) if total_prs > 0 else 0,
    }

    return stats
