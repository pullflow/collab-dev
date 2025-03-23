from typing import Dict, Optional

import plotly.graph_objects as go
from components.charts.utils import (
    apply_theme_to_figure,
    get_plotly_config,
    get_theme_colors,
)
from flask import render_template

from .data import prepare_sankey_data


def create_pr_flow_chart(data) -> Optional[Dict]:
    """Creates a Sankey diagram showing PR flow through different stages"""
    if not data:
        return None

    # Process links into sources and targets arrays
    sources = []
    targets = []
    values = []
    node_values = [0] * len(data["nodes"])  # Initialize array for node values

    for link in data["links"]:
        source_idx = data["nodes"].index(link["source"])
        target_idx = data["nodes"].index(link["target"])
        sources.append(source_idx)
        targets.append(target_idx)
        values.append(link["value"])
        node_values[source_idx] = link["value"]  # Store value for each node

    # Create the Plotly figure
    # Get theme colors
    colors = get_theme_colors(len(data["nodes"]), "primary")

    fig = go.Figure(
        data=[
            go.Sankey(
                arrangement="snap",
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="rgba(0,0,0,0.3)", width=0.5),
                    label=data["nodes"],
                    color=colors,  # Using theme colors
                    hoverlabel=dict(
                        bgcolor="rgba(100,100,100,0.8)",  # Semi-transparent dark background
                        bordercolor="rgba(0,0,0,0)",  # Transparent border
                        font=dict(size=16, color="white"),  # White text
                    ),
                    customdata=[
                        [val, "PR" if val == 1 else "PRs"] for val in node_values
                    ],  # Use node_values instead of values
                    hovertemplate="%{value:.0f} %{customdata[1]}<extra></extra>",  # Simple PR count for nodes
                ),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values,
                    color=["rgba(229, 229, 229, 0.5)"] * len(sources),
                    hoverlabel=dict(
                        bgcolor="rgba(100,100,100,0.8)",  # Semi-transparent dark background
                        bordercolor="rgba(0,0,0,0)",  # Transparent border
                        font=dict(size=16, color="white"),  # White text
                    ),
                    customdata=[[val, "PR" if val == 1 else "PRs"] for val in values],
                    hovertemplate="%{value:.0f} %{customdata[1]}<br>"
                    + "%{source.label} → %{target.label}<extra></extra>",  # Clean text format for links
                ),
            )
        ]
    )

    fig.update_layout(
        title=None,
        font={"size": 14},
        height=400,
        margin={"t": 20, "l": 20, "r": 20, "b": 20},
    )

    # Apply theme to the figure
    fig = apply_theme_to_figure(fig)

    # Convert to HTML with the consistent Plotly config
    return fig.to_html(full_html=False, include_plotlyjs=False, config=get_plotly_config())


def render(repo_df) -> str:
    pr_flow_data = prepare_sankey_data(repo_df)
    chart_html = create_pr_flow_chart(pr_flow_data)
    if not chart_html:
        return "<div>No data available</div>"

    return render_template("components/charts/pr_sankey/template.html", chart_content=chart_html)
