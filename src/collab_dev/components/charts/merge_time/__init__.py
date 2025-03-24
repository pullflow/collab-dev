import numpy as np
import plotly
import plotly.graph_objects as go
from components.charts.utils import (
    apply_theme_to_figure,
    get_plotly_config,
    get_theme_colors,
    humanize_time,
)
from flask import render_template

from .data import calculate_pmt


def create_pr_merge_time_chart(data):
    """Create PR Merge Time visualization"""

    # Handle both DataFrame and dictionary input
    repo_df = data.get("pr_data") if isinstance(data, dict) else data
    if repo_df is None:
        return None, None

    median_time, pr_times, percentile_values = calculate_pmt(repo_df)

    if median_time is None or pr_times is None:
        return None, None

    # Sort merge times for CDF
    sorted_times = np.sort(pr_times["merge_time"])
    cumulative_prob = np.arange(1, len(sorted_times) + 1) / len(sorted_times)

    # Calculate 95th percentile for x-axis limit
    percentile_95 = np.percentile(sorted_times, 95)

    # Create CDF plot
    # Get theme colors
    colors = get_theme_colors(5)

    fig = go.Figure()

    # Filter data points up to 95th percentile
    mask_95 = sorted_times <= percentile_95
    fig.add_trace(
        {
            "type": "scatter",
            "x": sorted_times[mask_95].tolist(),  # Convert numpy array to list
            "y": cumulative_prob[mask_95].tolist(),  # Convert numpy array to list
            "mode": "lines",
            "line": {"color": colors[0]},  # Use theme color
            "customdata": [[humanize_time(x)] for x in sorted_times[mask_95].tolist()],
            "hovertemplate": "%{y:.0%}: %{customdata[0]}<extra></extra>",
        }
    )

    # Add reference lines at key percentiles
    percentiles = [0.25, 0.5, 0.75]

    for p, val in zip(percentiles, percentile_values, strict=False):
        # Add vertical line
        fig.add_vline(x=val, line_dash="dash", line_color=colors[1], opacity=0.3)

        # Add annotation
        fig.add_annotation(
            x=val,
            y=p,
            text=f"{int(p * 100)}%: {val:.1f}h",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=1,
            arrowcolor=colors[1],
            font={"size": 12},
            bgcolor="white",
            bordercolor=colors[1],
            borderwidth=1,
            borderpad=4,
            ax=40,
            ay=0,
        )

    fig.update_layout(
        xaxis=dict(title="Merge Time (hours)", range=[0, percentile_95]),
        yaxis=dict(title="Cumulative Proportion of PRs", tickformat=",.0%", range=[0, 1.05]),
        showlegend=False,
        height=450,
        width=None,
        autosize=True,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(t=10, b=50, l=50, r=10),
    )

    # Apply theme to the figure
    fig = apply_theme_to_figure(fig)

    return fig, median_time


def render(data):
    """Render the PR merge time chart component"""

    try:
        # Create plot figure
        fig, median_time = create_pr_merge_time_chart(data)

        if fig is None:
            return render_template("components/charts/merge_time/template.html", pr_merge_data=None)

        # Get plotly config from theme
        config = get_plotly_config()

        # Convert the figure to HTML
        plot_html = plotly.offline.plot(fig, include_plotlyjs=False, output_type="div", config=config)

        # Prepare data for template
        pr_merge_data = {"median_time": median_time, "plot_html": plot_html}

        return render_template(
            "components/charts/merge_time/template.html", pr_merge_data=pr_merge_data, humanize_time=humanize_time
        )

    except Exception:
        return render_template("components/charts/merge_time/template.html", pr_merge_data=None)
