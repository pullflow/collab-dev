"""
Theme configuration module providing consistent color palettes and styling utilities.
"""

# Chart dimensions
CHART_DIMENSIONS = {
    "pie_chart_height": 400,  # Standard height for pie/donut charts
    "bar_chart_height": 300,  # Standard height for bar charts
    "funnel_chart_height": 300,  # Standard height for funnel charts
}

# Primary brand colors
BRAND = {
    "primary": "#795DBD",  # Slate blue - Main brand color
    "secondary": "#A592D3",  # African Violet - Secondary brand color
    "accent": "#FF958C",  # Coral pink - Accent color
    "highlight": "#ACE4AA",  # Celadon - Highlight color
    "dark": "#6D1A36",  # Claret - Dark accent
}

# Theme variations
THEMES = {
    "default": {
        "primary_series": [
            "#795DBD",  # Slate blue
            "#A592D3",  # African Violet
            "#FF958C",  # Coral pink
            "#ACE4AA",  # Celadon
            "#6D1A36",  # Claret
        ],
    }
}

# Extended color palette for data visualizations
VISUALIZATION = {
    # Main colors for primary data series - will be set by active theme
    "primary_series": THEMES["default"]["primary_series"],
    # Colors for secondary or supporting data
    "secondary_series": [
        "#B3A1E0",  # Lighter slate blue
        "#C4B6E3",  # Lighter african violet
        "#FFB3AC",  # Lighter coral pink
        "#C4ECC2",  # Lighter celadon
        "#8F3854",  # Lighter claret
    ],
    # Monochromatic scale of the primary color (Slate blue)
    "mono_scale": [
        "#795DBD",  # 100%
        "#8E76C7",  # 80%
        "#A38FD1",  # 60%
        "#B8A8DB",  # 40%
        "#CDC1E5",  # 20%
    ],
    # Diverging color scale for comparisons
    "diverging": [
        "#FF958C",  # negative (coral pink)
        "#FFB3AC",  # slightly negative
        "#F5F5F5",  # neutral
        "#ACE4AA",  # slightly positive (celadon)
        "#8BC887",  # positive (darker celadon)
    ],
}

# Semantic colors for status and feedback
SEMANTIC = {
    "success": "#ACE4AA",  # Celadon
    "warning": "#FFB3AC",  # Light coral pink
    "error": "#FF958C",  # Coral pink
    "info": "#A592D3",  # African Violet
}

# Background and surface colors
BACKGROUND = {
    "primary": "#FFFFFF",
    "secondary": "#F8F9FA",
    "tertiary": "#F1F3F5",
    "dark": "#6D1A36",  # Claret for dark mode or accents
}

# Text colors
TEXT = {
    "primary": "#212529",
    "secondary": "#6C757D",
    "muted": "#ADB5BD",
    "on_dark": "#F8F9FA",  # For text on dark backgrounds
}


def get_chart_colors(num_colors: int, palette: str = "primary") -> list:
    """
    Get a list of colors for charts and visualizations.

    Args:
        num_colors (int): Number of colors needed
        palette (str): Which palette to use ('primary', 'secondary', 'mono', 'diverging')

    Returns:
        list: List of color hex codes
    """
    if palette == "primary":
        # Extended primary colors with darker celadon for better contrast
        colors = [
            "#795DBD",  # Slate blue
            "#A592D3",  # African Violet
            "#FF958C",  # Coral pink
            "#ACE4AA",  # Celadon
            "#6D1A36",  # Claret
            "#8BC887",  # Darker celadon
            "#FFB3AC",  # Light coral pink
        ]
    elif palette == "secondary":
        colors = VISUALIZATION["secondary_series"]
    elif palette == "mono":
        colors = VISUALIZATION["mono_scale"]
    elif palette == "diverging":
        colors = VISUALIZATION["diverging"]
    else:
        colors = VISUALIZATION["primary_series"]

    # If we need more colors than available, cycle through the palette
    result = []
    while len(result) < num_colors:
        result.extend(colors)
    return result[:num_colors]


def get_plotly_template() -> dict:
    """
    Get a consistent Plotly chart template using the theme colors.

    Returns:
        dict: Plotly layout template
    """
    return {
        "layout": {
            "paper_bgcolor": BACKGROUND["primary"],
            "plot_bgcolor": BACKGROUND["primary"],
            "margin": {"l": 50, "r": 50, "t": 35, "b": 30, "pad": 4},
            "font": {"color": TEXT["primary"], "family": "sans-serif"},
            "title": {"font": {"color": TEXT["primary"], "size": 20}},
            "legend": {"font": {"color": TEXT["secondary"]}},
            "xaxis": {
                "gridcolor": BACKGROUND["tertiary"],
                "linecolor": TEXT["muted"],
                "title": {"font": {"color": TEXT["secondary"]}},
                "tickfont": {"color": TEXT["secondary"]},
            },
            "yaxis": {
                "gridcolor": BACKGROUND["tertiary"],
                "linecolor": TEXT["muted"],
                "title": {"font": {"color": TEXT["secondary"]}},
                "tickfont": {"color": TEXT["secondary"]},
            },
        }
    }


def get_streamlit_theme() -> dict:
    """
    Get theme configuration for Streamlit's config.toml

    Returns:
        dict: Streamlit theme configuration
    """
    return {
        "primaryColor": BRAND["primary"],
        "backgroundColor": BACKGROUND["primary"],
        "secondaryBackgroundColor": BACKGROUND["secondary"],
        "textColor": TEXT["primary"],
        "font": "sans serif",
    }


def get_template_data() -> dict:
    """
    Get consistent theme data for template rendering.

    Returns:
        dict: Theme configuration for templates
    """
    return {
        "theme": {
            "brand": BRAND,
            "colors": VISUALIZATION["primary_series"],
            "background": BACKGROUND,
            "text": TEXT,
            "semantic": SEMANTIC,
        }
    }


def set_theme(theme_name: str = "default") -> None:
    """
    Set the active theme for visualizations.

    Args:
        theme_name (str): Name of the theme to use (currently only 'default' is supported)

    Raises:
        ValueError: If the specified theme name is not found
    """
    if theme_name not in THEMES:
        raise ValueError(f"Theme '{theme_name}' not found. Available themes: {list(THEMES.keys())}")

    # Update visualization colors based on theme
    VISUALIZATION["primary_series"] = THEMES[theme_name]["primary_series"]
