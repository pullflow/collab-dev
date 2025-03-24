import plotly
import plotly.graph_objects as go
from components.charts.utils import (
    apply_theme_to_figure,
    get_plotly_config,
    get_theme_colors,
)
from flask import render_template

from .data import get_review_merge_data


def create_coverage_donut_plot(coverage_data: dict) -> dict:
    """Create donut chart visualization for review coverage"""

    # Calculate values
    reviewed = coverage_data["reviewed_prs"]
    unreviewed = coverage_data["unreviewed_prs"]

    # Get theme colors for the chart
    colors = get_theme_colors(2)

    # Create figure
    fig = go.Figure(
        data=[
            go.Pie(
                values=[reviewed, unreviewed],
                labels=["Merged With Review", "Merged Without Review"],
                hole=0.4,
                textinfo="percent",
                marker_colors=colors,  # Use theme colors
                domain={
                    "x": [0.15, 0.85],
                    "y": [0.05, 0.85],
                },  # Balanced whitespace around the chart
                textposition="inside",
                hovertemplate="%{label}: %{customdata}<extra></extra>",
                customdata=[
                    f"{reviewed} PR{'s' if reviewed != 1 else ''}",
                    f"{unreviewed} PR{'s' if unreviewed != 1 else ''}",
                ],
                insidetextorientation="auto",
            )
        ]
    )

    # Update layout
    fig.update_layout(
        showlegend=True,
        height=350,  # Reduce height to remove extra whitespace
        margin=dict(t=10, b=10, l=10, r=10),  # Balanced margins around the chart
        legend=dict(
            orientation="h",
            yanchor="top",
            y=1.0,  # Position at the top of the chart
            xanchor="center",  # Center the legend
            x=0.5,  # Center position
            bgcolor="rgba(255,255,255,0.8)",
        ),
        autosize=True,
        width=None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    # Apply theme to the figure
    fig = apply_theme_to_figure(fig)

    return fig


def render(repo_df):
    """Render the review coverage chart component"""

    try:
        # Get coverage data
        coverage_data = get_review_merge_data(repo_df)

        if not coverage_data:
            return render_template("components/charts/review_coverage/template.html", coverage_data=None)

        # Create plot figure
        fig = create_coverage_donut_plot(coverage_data)

        # Get plotly config from theme
        config = get_plotly_config()

        # Convert the figure to HTML
        plot_html = plotly.offline.plot(fig, include_plotlyjs=False, output_type="div", config=config)

        # Add plot to template data
        coverage_data["plot_html"] = plot_html

        return render_template(
            "components/charts/review_coverage/template.html",
            coverage_data=coverage_data,
        )

    except Exception:
        return render_template("components/charts/review_coverage/template.html", coverage_data=None)
