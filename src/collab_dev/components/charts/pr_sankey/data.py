from typing import Dict, Optional

import pandas as pd


def prepare_sankey_data(df: pd.DataFrame) -> Optional[Dict]:
    """
    Process PR events into a format suitable for a Sankey diagram.

    Args:
        df: DataFrame containing PR events

    Returns:
        Dictionary containing nodes and links for the Sankey diagram, or None if no data
    """
    if df.empty:
        return None

    # Group events by PR number to analyze flow
    pr_events = (
        df.groupby("pr_number")
        .agg(
            {
                "event_type": list,
                "time": "first",  # Keep first timestamp for reference
            }
        )
        .reset_index()
    )

    # Initialize node lists and link counts
    nodes = ["PRs Created"]
    links = []

    # Count initial PRs
    total_prs = len(pr_events)

    # Track PRs at each stage
    review_requested = sum("review_requested" in events for events in pr_events["event_type"])
    direct_reviews = sum(
        any(event in ["review_commented", "review_changes_requested", "review_approved"] for event in events)
        and "review_requested" not in events
        for events in pr_events["event_type"]
    )
    no_review = total_prs - review_requested - direct_reviews

    # Add review request flow
    nodes.extend(["Review Requested", "No Review", "Direct Review"])

    links.extend(
        [
            {"source": "PRs Created", "target": "Review Requested", "value": review_requested},
            {"source": "PRs Created", "target": "No Review", "value": no_review},
            {"source": "PRs Created", "target": "Direct Review", "value": direct_reviews},
        ]
    )

    # Track review outcomes
    nodes.extend(["Approved", "Commented"])

    # Count PRs by their review outcome
    approved_prs = sum("review_approved" in events for events in pr_events["event_type"])
    commented_prs = sum(
        "review_commented" in events and "review_approved" not in events for events in pr_events["event_type"]
    )

    # Calculate how many PRs went from each review path to each outcome
    # For Review Requested path
    if review_requested > 0:
        approved_from_requested = sum(
            "review_approved" in events and "review_requested" in events for events in pr_events["event_type"]
        )
        commented_from_requested = sum(
            "review_commented" in events and "review_requested" in events and "review_approved" not in events
            for events in pr_events["event_type"]
        )

        # Add links for review outcomes
        if approved_from_requested > 0:
            links.append({"source": "Review Requested", "target": "Approved", "value": approved_from_requested})
        if commented_from_requested > 0:
            links.append({"source": "Review Requested", "target": "Commented", "value": commented_from_requested})

        # If there are remaining PRs with review requested but no outcome, add them to Approved
        remaining_requested = review_requested - approved_from_requested - commented_from_requested
        if remaining_requested > 0:
            links.append({"source": "Review Requested", "target": "Approved", "value": remaining_requested})

    # For Direct Review path
    if direct_reviews > 0:
        approved_from_direct = sum(
            "review_approved" in events and "review_requested" not in events for events in pr_events["event_type"]
        )
        commented_from_direct = sum(
            "review_commented" in events and "review_requested" not in events and "review_approved" not in events
            for events in pr_events["event_type"]
        )

        # Add links for review outcomes
        if approved_from_direct > 0:
            links.append({"source": "Direct Review", "target": "Approved", "value": approved_from_direct})
        if commented_from_direct > 0:
            links.append({"source": "Direct Review", "target": "Commented", "value": commented_from_direct})

        # If there are remaining PRs with direct review but no outcome, add them to Commented
        remaining_direct = direct_reviews - approved_from_direct - commented_from_direct
        if remaining_direct > 0:
            links.append({"source": "Direct Review", "target": "Commented", "value": remaining_direct})

    # Add final state - Merged
    nodes.append("Merged")

    # Use actual counts for merge paths instead of arbitrary allocation
    approved_to_merged = approved_prs
    comments_to_merged = commented_prs

    # Add links to Merged
    if approved_to_merged > 0:
        links.append({"source": "Approved", "target": "Merged", "value": approved_to_merged})

    if comments_to_merged > 0:
        links.append({"source": "Commented", "target": "Merged", "value": comments_to_merged})

    # Only use the original no_review count when connecting to Merged
    if no_review > 0:
        links.append({"source": "No Review", "target": "Merged", "value": no_review})

    # Remove any links with zero value
    links = [link for link in links if link["value"] > 0]

    return {"nodes": nodes, "links": links}
