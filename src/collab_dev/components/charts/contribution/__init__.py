import plotly
import plotly.graph_objects as go
from components.charts.utils import (
    apply_theme_to_figure,
    get_plotly_config,
    get_theme_colors,
)
from flask import render_template
from theme import CHART_DIMENSIONS


def create_contribution_plot(stats: dict) -> go.Figure:
    """Create visualization configuration for contribution donut chart"""

    # Get theme colors for the chart
    colors = get_theme_colors(3)

    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Core Team", "Bot", "Community"],
                values=[
                    stats["core_percentage"],
                    stats["bot_percentage"],
                    stats["community_percentage"],
                ],
                hole=0.4,
                marker_colors=colors,  # Use theme colors
                domain={"x": [0.05, 0.95], "y": [0, 0.85]},  # Match other pie charts
                textposition="inside",
                textinfo="percent",
                hovertemplate="%{label}: %{customdata}<extra></extra>",
                customdata=[
                    f"{stats['core_prs']} {'PR' if stats['core_prs'] == 1 else 'PRs'}",
                    f"{stats['bot_prs']} {'PR' if stats['bot_prs'] == 1 else 'PRs'}",
                    f"{stats['community_prs']} {'PR' if stats['community_prs'] == 1 else 'PRs'}",
                ],
                insidetextorientation="auto",
            )
        ]
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.92,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.8)",
        ),
        margin=dict(t=25, b=20, l=10, r=10),
        height=CHART_DIMENSIONS["pie_chart_height"],
        autosize=True,
        width=None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    # Apply theme to the figure
    fig = apply_theme_to_figure(fig)

    return fig


def render(repo_df):
    """
    Render the contribution chart component

    Args:
        repo_df: DataFrame containing repository data

    Returns:
        str: Rendered HTML for the contribution component
    """
    from .data import get_contribution_stats

    # Get the stats from data module
    stats = get_contribution_stats(repo_df)

    if not stats:
        return render_template("components/charts/contribution/template.html", contribution_data=None)

    # Create plot figure
    fig = create_contribution_plot(stats)

    # Get plotly config from theme
    config = get_plotly_config()

    # Convert the figure to HTML
    plot_html = plotly.offline.plot(fig, include_plotlyjs=False, output_type="div", config=config)

    # Prepare data for template
    contribution_data = {
        "plot_html": plot_html,
        "stats": {
            "core_team": stats["core_percentage"],
            "bot": stats["bot_percentage"],
            "community": stats["community_percentage"],
        },
        "counts": {
            "total": stats["total_prs"],
            "core": stats["core_prs"],
            "bot": stats["bot_prs"],
            "community": stats["community_prs"],
        },
    }

    # Pass the prepared data to the template
    return render_template(
        "components/charts/contribution/template.html",
        contribution_data=contribution_data,
    )
