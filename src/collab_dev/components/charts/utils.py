"""
Utility functions for chart components to apply consistent theming
"""

import pandas as pd
import plotly.graph_objects as go
import theme as theme


def apply_theme_to_figure(fig: go.Figure) -> go.Figure:
    """
    Apply the application theme to a Plotly figure

    Args:
        fig: Plotly figure to apply theme to

    Returns:
        go.Figure: Themed Plotly figure
    """
    # Get the plotly template from our theme module
    template = theme.get_plotly_template()

    # Apply layout settings from the template
    for key, value in template["layout"].items():
        if key not in fig.layout or fig.layout[key] is None:
            fig.layout[key] = value

    # Apply font settings if they exist
    if "font" in template["layout"]:
        if "font" not in fig.layout:
            fig.layout.font = template["layout"]["font"]
        else:
            for font_key, font_value in template["layout"]["font"].items():
                if font_key not in fig.layout.font or fig.layout.font[font_key] is None:
                    fig.layout.font[font_key] = font_value

    # Apply axis settings if they exist
    for axis in ["xaxis", "yaxis"]:
        if axis in template["layout"]:
            if axis not in fig.layout:
                fig.layout[axis] = template["layout"][axis]
            else:
                for axis_key, axis_value in template["layout"][axis].items():
                    if axis_key not in fig.layout[axis] or fig.layout[axis][axis_key] is None:
                        fig.layout[axis][axis_key] = axis_value

    return fig


def get_theme_colors(num_colors: int = 5, palette: str = "primary") -> list:
    """
    Get a list of colors from the theme for charts

    Args:
        num_colors: Number of colors needed
        palette: Which palette to use ('primary', 'secondary', 'mono', 'diverging')

    Returns:
        list: List of color hex codes
    """
    return theme.get_chart_colors(num_colors, palette)


def get_plotly_config() -> dict:
    """
    Get a consistent Plotly config for all charts

    Returns:
        dict: Plotly config
    """
    return {
        "displayModeBar": False,
        "responsive": True,
        "displaylogo": False,  # Disable the Plotly logo/advertisement
        "modeBarButtonsToRemove": ["sendDataToCloud", "autoScale2d", "resetScale2d"],
    }


def humanize_time(hours, precision=1):
    """
    Convert a time duration (in hours) to a human-readable string.
    Automatically selects the most appropriate unit (seconds to years) for display.

    Args:
        hours: Number of hours (input is always in hours)
        precision: Number of decimal places for values

    Returns:
        str: Human-readable string with appropriate unit (e.g. "2.5 minutes", "3 days")
    """
    if hours is None or pd.isna(hours):
        return "N/A"

    # Convert hours to seconds for easier unit conversion
    seconds = hours * 3600

    # Less than a minute
    if seconds < 60:
        return f"{int(seconds)} seconds"

    # Less than an hour
    if seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"

    # Less than a day
    if seconds < 86400:
        return f"{hours:.1f} hours"

    # Days
    days = hours / 24
    if days < 7:
        return f"{days:.1f} days"

    # Weeks
    weeks = days / 7
    if weeks < 4:
        return f"{weeks:.1f} weeks"

    # Months (approximate)
    months = days / 30.44
    if months < 12:
        return f"{months:.1f} months"

    # Years
    years = days / 365.25
    return f"{years:.1f} years"
