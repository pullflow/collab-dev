import plotly
import plotly.graph_objects as go
from components.charts.utils import (
    apply_theme_to_figure,
    get_plotly_config,
    get_theme_colors,
    humanize_time,
)
from flask import render_template

from .data import get_review_turnaround_data


def create_turnaround_distribution_plot(turnaround_data: dict) -> go.Figure:
    """Create visualization for review turnaround distribution"""

    # Calculate percentages for each segment
    within_1h = turnaround_data["within_1h"]
    within_4h = turnaround_data["within_4h"] - turnaround_data["within_1h"]
    within_24h = turnaround_data["within_24h"] - turnaround_data["within_4h"]
    over_24h = 100 - turnaround_data["within_24h"]

    # Calculate counts for hover text
    total_prs = turnaround_data["total_prs"]
    within_1h_count = int(within_1h * total_prs / 100)
    within_4h_count = int((turnaround_data["within_4h"] - turnaround_data["within_1h"]) * total_prs / 100)
    within_24h_count = int((turnaround_data["within_24h"] - turnaround_data["within_4h"]) * total_prs / 100)
    over_24h_count = total_prs - within_1h_count - within_4h_count - within_24h_count

    # Get theme colors for the chart
    colors = get_theme_colors(4)

    # Create figure
    fig = go.Figure()

    # Add each segment in the order they should appear in the chart
    fig.add_trace(
        go.Bar(
            y=[""],
            x=[within_1h],
            name="Within 1 hour",
            orientation="h",
            marker=dict(color=colors[0], line=dict(width=0)),
            hoverinfo="text",
            hovertext=[f"Within 1 hour: {within_1h_count} {'PR' if within_1h_count == 1 else 'PRs'}"],
            text=[f"{within_1h:.1f}%"],
            textposition="auto",
            insidetextanchor="middle",
        )
    )

    fig.add_trace(
        go.Bar(
            y=[""],
            x=[within_4h],
            name="Within 4 hours",
            orientation="h",
            marker=dict(color=colors[1], line=dict(width=0)),
            hoverinfo="text",
            hovertext=[f"Within 4 hours: {within_4h_count} {'PR' if within_4h_count == 1 else 'PRs'}"],
            text=[f"{within_4h:.1f}%"],
            textposition="auto",
            insidetextanchor="middle",
        )
    )

    fig.add_trace(
        go.Bar(
            y=[""],
            x=[within_24h],
            name="Within 24 hours",
            orientation="h",
            marker=dict(color=colors[2], line=dict(width=0)),
            hoverinfo="text",
            hovertext=[f"Within 24 hours: {within_24h_count} {'PR' if within_24h_count == 1 else 'PRs'}"],
            text=[f"{within_24h:.1f}%"],
            textposition="auto",
            insidetextanchor="middle",
        )
    )

    fig.add_trace(
        go.Bar(
            y=[""],
            x=[over_24h],
            name="Over 24 hours",
            orientation="h",
            marker=dict(color=colors[3], line=dict(width=0)),
            hoverinfo="text",
            hovertext=[f"Over 24 hours: {over_24h_count} {'PR' if over_24h_count == 1 else 'PRs'}"],
            text=[f"{over_24h:.1f}%"],
            textposition="auto",
            insidetextanchor="middle",
        )
    )

    # Add x-axis ticks
    tick_vals = [0, 20, 40, 60, 80, 100]

    # Update layout
    fig.update_layout(
        barmode="stack",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.1,
            xanchor="center",
            x=0.5,
            traceorder="normal",
            font=dict(size=10),
        ),
        margin=dict(t=30, l=0, r=0, b=20),
        height=150,
        uniformtext=dict(mode="hide", minsize=10),
        xaxis=dict(
            range=[0, 100],
            showgrid=True,
            tickvals=tick_vals,
            zeroline=False,
            fixedrange=True,
        ),
        yaxis=dict(showticklabels=False, showgrid=False, fixedrange=True),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    # Apply theme to figure
    fig = apply_theme_to_figure(fig)

    return fig


def render(repo_df):
    """Render the review turnaround chart component"""

    try:
        # Get turnaround data
        turnaround_data = get_review_turnaround_data(repo_df)

        if not turnaround_data:
            return render_template(
                "components/charts/review_turnaround/template.html",
                turnaround_data=None,
            )

        # Create plot figure
        fig = create_turnaround_distribution_plot(turnaround_data)

        # Get plotly config from theme
        config = get_plotly_config()

        # Convert the figure to HTML
        plot_html = plotly.offline.plot(fig, include_plotlyjs=False, output_type="div", config=config)

        # Prepare data for template
        chart_data = {
            "plot_html": plot_html,
            "median_hours": turnaround_data["median_hours"],
            "total_prs": turnaround_data["total_prs"],
            "reviewed_prs": turnaround_data["reviewed_prs"],
            "review_rate": turnaround_data["review_rate"],
            "within_1h": turnaround_data["within_1h"],
            "within_4h": turnaround_data["within_4h"],
            "within_24h": turnaround_data["within_24h"],
        }

        # Pass the prepared data to the template
        return render_template(
            "components/charts/review_turnaround/template.html",
            turnaround_data=chart_data,
            humanize_time=humanize_time,
        )

    except Exception:
        return render_template("components/charts/review_turnaround/template.html", turnaround_data=None)
