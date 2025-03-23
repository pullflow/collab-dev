import plotly
import plotly.graph_objects as go
from components.charts.utils import (
    apply_theme_to_figure,
    get_plotly_config,
    get_theme_colors,
)
from flask import render_template

from .data import get_review_funnel_data


def create_review_funnel_plot(funnel_data: dict) -> go.Figure:
    """Create visualization for review funnel"""

    # Prepare data for funnel chart with counts in the labels
    values = [funnel_data["total_prs"], funnel_data["reviewed_prs"], funnel_data["approved_prs"]]

    # Calculate relative percentages (each step relative to previous)
    total = values[0]
    reviewed = values[1]
    approved = values[2]

    # Create stage labels without counts
    stages = ["Total PRs", "Reviewed", "Approved"]

    # Format text to show just the count
    text = [str(values[0]), str(values[1]), str(values[2])]

    # Create hover text with percentages
    hover_text = [
        f"{values[0]} PR{'s' if values[0] != 1 else ''} Total",
        f"{values[1]} PR{'s' if values[1] != 1 else ''} Reviewed ({reviewed / total * 100:.0f}%)",
        f"{values[2]} PR{'s' if values[2] != 1 else ''} Approved ({approved / reviewed * 100:.0f}%)",
    ]

    # Get theme colors
    colors = get_theme_colors(3)

    # Create figure
    fig = go.Figure(
        data=[
            go.Funnel(
                y=stages,
                x=values,
                textinfo="text",
                textposition="auto",  # Automatically place text inside or outside based on space
                text=text,
                hovertemplate="%{customdata}<extra></extra>",
                customdata=hover_text,
                marker={
                    "color": colors,
                    "line": {"width": 0},  # Remove the line around funnel segments
                },
                connector={"line": {"color": "rgba(0,0,0,0)", "width": 0}},  # Make connector lines invisible
                textfont={"size": 14},  # Match font size
            )
        ]
    )

    # Update layout
    fig.update_layout(
        showlegend=False,
        margin={"t": 20, "l": 150, "r": 100, "b": 20},
        height=300,
        font={"size": 14},
        # Hide all axis lines, ticks, and grid lines
        xaxis={"showgrid": False, "zeroline": False, "showline": False, "showticklabels": False, "ticks": ""},
        yaxis={
            "showgrid": False,
            "zeroline": False,
            "showline": False,
            "ticks": "",
            "tickmode": "array",
            "ticktext": stages,  # Use the HTML formatted labels
            "tickfont": {"size": 14},  # Match the font size
        },
    )

    # Apply theme to the figure
    fig = apply_theme_to_figure(fig)

    return fig


def render(repo_df):
    """Render the review funnel chart component"""

    try:
        # Get funnel data
        funnel_data = get_review_funnel_data(repo_df)

        if not funnel_data:
            return render_template("components/charts/review_funnel/template.html", review_data=None)

        # Calculate rates
        total_prs = funnel_data["total_prs"]
        reviewed_prs = funnel_data["reviewed_prs"]
        approved_prs = funnel_data["approved_prs"]

        review_rate = (reviewed_prs / total_prs * 100) if total_prs > 0 else 0
        approval_rate = (approved_prs / reviewed_prs * 100) if reviewed_prs > 0 else 0

        # Create plot figure
        fig = create_review_funnel_plot(funnel_data)

        # Get plotly config from theme
        config = get_plotly_config()

        # Convert the figure to HTML
        plot_html = plotly.offline.plot(fig, include_plotlyjs=False, output_type="div", config=config)

        # Prepare data for template
        template_data = {
            "total_prs": total_prs,
            "reviewed_prs": reviewed_prs,
            "approved_prs": approved_prs,
            "review_rate": review_rate,
            "approval_rate": approval_rate,
            "plot_html": plot_html,
        }

        return render_template("components/charts/review_funnel/template.html", review_data=template_data)

    except Exception:
        return render_template("components/charts/review_funnel/template.html", review_data=None)
