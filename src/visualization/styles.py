"""
Visualization Styles
====================

Consistent styling for all charts in the project.
"""

import matplotlib.pyplot as plt
from typing import Optional

# Color palette for efficiency classes
COLORS = {
    'Efficient': '#2E8B57',      # Sea green
    'Bottlenecked': '#DC143C',   # Crimson
    'Moderate': '#FFA500',       # Orange
    'Inefficient': '#9370DB',    # Medium purple
    'Idle': '#808080',           # Gray
    
    # Severity colors
    'Critical': '#DC143C',
    'Warning': '#FFA500',
    'Moderate': '#FFD700',
    'Healthy': '#2E8B57',
}

# Default style settings
STYLE_CONFIG = {
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'axes.grid': True,
    'grid.alpha': 0.3,
    'font.family': 'sans-serif',
    'font.size': 10,
}


def apply_style(ax: plt.Axes) -> None:
    """Apply consistent styling to an axes object."""
    ax.set_facecolor('white')
    ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


def add_interpretation_box(
    ax: plt.Axes,
    text: str,
    x: float = 0.02,
    y: float = -0.15,
    fontsize: int = 9,
) -> None:
    """
    Add an interpretation text box below a chart.
    
    Args:
        ax: Axes to add text to
        text: Interpretation text
        x: X position (axes fraction)
        y: Y position (axes fraction, negative = below)
        fontsize: Font size
    """
    ax.text(
        x, y, text,
        transform=ax.transAxes,
        fontsize=fontsize,
        style='italic',
        wrap=True,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5)
    )


def get_color_for_value(value: float, thresholds: tuple = (0.3, 0.5, 0.7)) -> str:
    """
    Get traffic-light color based on value and thresholds.
    
    Args:
        value: Value to color (0-1)
        thresholds: (low, medium, high) thresholds
        
    Returns:
        Color string
    """
    low, medium, high = thresholds
    
    if value <= low:
        return COLORS['Healthy']
    elif value <= medium:
        return COLORS['Moderate']
    elif value <= high:
        return COLORS['Warning']
    else:
        return COLORS['Critical']


def setup_matplotlib_defaults() -> None:
    """Configure matplotlib with project defaults."""
    plt.rcParams.update(STYLE_CONFIG)
    plt.style.use('seaborn-v0_8-whitegrid')
