import pandas as pd


def analyze_bot_activity(repo_df):
    """
    Analyze PR activity by bots vs humans.

    Args:
        repo_df: DataFrame containing repository data

    Returns:
        dict: Statistics about bot vs human PR activity
    """
    if repo_df is None or repo_df.empty:
        return None

    # Get unique PRs and their first events to determine PR type
    pr_data = repo_df[repo_df["event_type"] == "pr_created"].drop_duplicates("pr_number")

    if pr_data.empty:
        return None

    # Create a list of PR authors
    pr_authors = []
    for _, row in pr_data.iterrows():
        author = row.get("actor", "")
        if author:
            pr_authors.append(
                {"actor": author, "pr_number": row.get("pr_number", 0), "is_bot": row.get("is_bot", False)}
            )

    if not pr_authors:
        return None

    # Convert to DataFrame
    pr_df = pd.DataFrame(pr_authors)

    # Group by actor to count PRs
    author_counts = pr_df.groupby(["actor", "is_bot"]).size().reset_index(name="pr_count")

    # Calculate statistics
    total_prs = len(pr_authors)
    bot_prs = pr_df[pr_df["is_bot"]].shape[0]
    human_prs = pr_df[~pr_df["is_bot"]].shape[0]

    # Get bot breakdown
    bot_breakdown = author_counts[author_counts["is_bot"]].sort_values("pr_count", ascending=False)

    # Rename column for consistency with the expected output
    bot_breakdown = bot_breakdown.rename(columns={"pr_count": "pr_number"})

    return {
        "total_prs": total_prs,
        "bot_prs": bot_prs,
        "human_prs": human_prs,
        "bot_count": bot_prs,
        "human_count": human_prs,
        "bot_percentage": round((bot_prs / total_prs * 100) if total_prs > 0 else 0, 1),
        "human_percentage": round((human_prs / total_prs * 100) if total_prs > 0 else 0, 1),
        "bot_breakdown": bot_breakdown.to_dict("records"),
    }
