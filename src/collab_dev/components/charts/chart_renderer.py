"""
Chart renderer module to execute all available charts against a data frame.
"""

import importlib
import inspect
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict

import pandas as pd


def get_chart_modules() -> Dict[str, Callable]:
    """
    Discover all chart rendering functions from submodules.

    Returns:
        Dict[str, Callable]: Dictionary mapping chart names to their render functions
    """
    chart_modules = {}
    charts_dir = Path(__file__).parent

    # Get all directories in the charts folder (each should be a chart package)
    for item in os.listdir(charts_dir):
        item_path = charts_dir / item
        if not item_path.is_dir():
            continue

        # Import the chart module
        module_name = f"components.charts.{item}"
        try:
            module = importlib.import_module(module_name)

            # Find render functions - they typically start with "render_"
            for name, func in inspect.getmembers(module, inspect.isfunction):
                if name == "render":
                    chart_modules[item] = func
                    break
        except (ImportError, AttributeError) as e:
            print(f"Error importing chart module {module_name}: {e}", file=sys.stderr)

    return chart_modules


def render_charts(data: pd.DataFrame) -> list[Dict[str, Any]]:
    """
    Render all available charts with the provided DataFrame.

    Args:
        data: DataFrame containing the data to render charts with

    Returns:
        list[Dict[str, Any]]: List of dictionaries with 'name' and 'html' fields for each chart
    """
    chart_modules = get_chart_modules()
    results = []

    for chart_name, render_func in chart_modules.items():
        try:
            chart_output = render_func(data)
            results.append({"name": chart_name, "html": chart_output})
        except Exception as e:
            print(f"Error rendering chart {chart_name}: {e}", file=sys.stderr)
            results.append({"name": chart_name, "html": None})

    return results
