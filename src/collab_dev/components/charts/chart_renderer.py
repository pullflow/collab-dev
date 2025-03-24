"""
Chart renderer module to execute all available charts against a data frame.
"""

import sys
from typing import Any, Dict, List

import components.charts.approval_time
import components.charts.bot_analysis
import components.charts.contribution
import components.charts.merge_time
import components.charts.review_coverage
import components.charts.review_funnel
import components.charts.review_turnaround
import components.charts.workflow
import pandas as pd

# Ordered list of chart modules
CHART_MODULES = [
    components.charts.workflow,
    components.charts.contribution,
    components.charts.bot_analysis,
    components.charts.review_coverage,
    components.charts.review_funnel,
    components.charts.review_turnaround,
    components.charts.approval_time,
    components.charts.merge_time,
]


def render_charts(data: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Render all available charts with the provided DataFrame. Have new charts?
    Add them to the CHART_MODULES list and they'll be rendered automatically.
    """
    chart_renders = []

    # Iterate through the ordered list of chart modules and render them
    for chart in CHART_MODULES:
        try:
            chart_renders.append(chart.render(data))
        except Exception as e:
            print(f"Error rendering chart {chart.__name__}: {e}", file=sys.stderr)
            chart_renders.append(f"Failed to render {chart.__name__}. Error: {e}.")

    return chart_renders
