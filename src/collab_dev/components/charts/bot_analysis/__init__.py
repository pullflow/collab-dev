import plotly
import plotly.graph_objects as go
from components.charts.utils import (
    apply_theme_to_figure,
    get_plotly_config,
    get_theme_colors,
)
from flask import render_template


def render(repo_df):
    """Render the bot analysis visualization"""
    from .data import analyze_bot_activity

    stats = analyze_bot_activity(repo_df)
    if not stats:
        return render_template("components/charts/bot_analysis/template.html")

    # Check if there's bot breakdown data to display
    if not stats["bot_breakdown"]:
        return render_template("components/charts/bot_analysis/template.html", stats=stats)

    # Get theme colors
    colors = get_theme_colors(len(stats["bot_breakdown"]))

    # Create a Plotly figure
    fig = go.Figure(
        data=[
            go.Bar(
                x=[item["pr_number"] for item in stats["bot_breakdown"]],
                y=[item["actor"] for item in stats["bot_breakdown"]],
                orientation="h",
                marker=dict(color=colors),
                customdata=[
                    [pr_num, "PR" if pr_num == 1 else "PRs"]
                    for pr_num in [item["pr_number"] for item in stats["bot_breakdown"]]
                ],
                hovertemplate="%{customdata[0]} %{customdata[1]}<extra></extra>",
            )
        ]
    )

    # Update layout
    fig.update_layout(
        margin=dict(t=30, l=200, r=30, b=50),
        height=max(300, len(stats["bot_breakdown"]) * 40),
        xaxis=dict(title="Number of PRs"),
        yaxis=dict(automargin=True, tickfont=dict(size=12)),
    )

    # Apply theme to the figure
    fig = apply_theme_to_figure(fig)

    # Get plotly config from theme
    config = get_plotly_config()

    # Convert the figure to HTML
    bot_breakdown_html = plotly.offline.plot(fig, include_plotlyjs=False, output_type="div", config=config)

    return render_template(
        "components/charts/bot_analysis/template.html",
        stats=stats,
        bot_breakdown_html=bot_breakdown_html,
    )
