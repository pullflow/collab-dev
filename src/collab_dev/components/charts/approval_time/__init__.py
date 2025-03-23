import logging

import pandas as pd
import plotly
import plotly.graph_objects as go
from components.charts.utils import (
    apply_theme_to_figure,
    get_plotly_config,
    get_theme_colors,
    humanize_time,
)
from flask import render_template

from .data import get_approval_time_data


def create_approval_time_plot(size_stats) -> go.Figure:
    """Create visualization for approval time by PR size"""

    logging.debug("Processing size stats for approval time plot")
    logging.debug(f"Input size_stats:\n{size_stats}")

    # Define the desired order of size categories
    size_order = [
        "XS (<10 lines)",
        "S (10-99 lines)",
        "M (100-499 lines)",
        "L (500-999 lines)",
        "XL (1000+ lines)",
    ]

    # Sort the DataFrame by our custom order
    size_stats = size_stats.set_index("size_category").reindex(size_order).reset_index()

    # Extract data from size_stats DataFrame
    categories = size_stats["size_category"].tolist()

    # Fix: Replace NaN values with 0 in median_hours and pr_count
    median_hours = [0 if pd.isna(val) else val for val in size_stats["median_hours"].tolist()]
    pr_counts = [0 if pd.isna(val) else int(val) for val in size_stats["pr_count"].tolist()]

    # Create hover text with humanized times
    hover_text = [
        f"Median: {humanize_time(hours)}<br>Count: {count} PR{'s' if count != 1 else ''}"
        for hours, count in zip(median_hours, pr_counts, strict=False)
    ]

    logging.debug(f"Categories: {categories}")
    logging.debug(f"Median hours: {median_hours}")
    logging.debug(f"PR counts: {pr_counts}")

    # Calculate percentage of PRs in each category
    total_prs = sum(pr_counts)
    logging.debug(f"Total PRs: {total_prs}")

    # Create fraction text for each bar with simple dash
    bar_text = [f"{count}" for count in pr_counts]
    logging.debug(f"Bar text fractions: {bar_text}")

    # Calculate percentages based on PR counts
    percentages = [count / total_prs * 100 if total_prs > 0 else 0 for count in pr_counts]
    logging.debug(f"Calculated percentages: {percentages}")

    # Get theme colors
    colors = get_theme_colors(len(categories))

    # Create figure using plotly graph objects
    fig = go.Figure(
        data=[
            go.Bar(
                x=categories,
                y=median_hours,
                text=bar_text,
                textposition="outside",
                marker_color=colors,
                marker_line_width=0,  # Remove border lines from bars
                hoverinfo="text",
                hovertext=hover_text,
            )
        ]
    )

    # Update layout
    fig.update_layout(
        xaxis_title="PR Size",
        yaxis_title="Median Hours to Approval",
        showlegend=False,
        margin={"t": 40, "l": 50, "r": 50, "b": 50},
        height=400,
        paper_bgcolor="white",
        plot_bgcolor="white",
    )

    # Apply theme to the figure
    fig = apply_theme_to_figure(fig)

    return fig


def render(repo_df):
    """Render the approval time chart component"""

    try:
        # Get approval time statistics
        approval_data = get_approval_time_data(repo_df)

        if not approval_data:
            return render_template("components/charts/approval_time/template.html", approval_data=None)

        # Create plot figure
        fig = create_approval_time_plot(approval_data["size_stats"])

        # Get plotly config from theme
        config = get_plotly_config()

        # Convert the figure to HTML
        plot_html = plotly.offline.plot(fig, include_plotlyjs=False, output_type="div", config=config)

        # Prepare data for template
        template_data = {
            "overall_median": approval_data["overall_median"],
            "plot_html": plot_html,
        }

        return render_template("components/charts/approval_time/template.html", approval_data=template_data)

    except Exception:
        return render_template("components/charts/approval_time/template.html", approval_data=None)
