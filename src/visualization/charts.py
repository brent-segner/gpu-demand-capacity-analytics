"""
Visualization Functions
=======================

Chart generation functions for GPU demand-capacity analysis.
All charts include titles, axis labels, units, and interpretation guidance.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Optional, Tuple, List, Dict
from .styles import COLORS, apply_style, add_interpretation_box


def plot_utilization_vs_power_intensity(
    df: pd.DataFrame,
    util_col: str = 'gpu_utilization_pct',
    pif_col: str = 'power_intensity_factor',
    class_col: str = 'efficiency_class',
    sample_size: int = 5000,
    figsize: Tuple[int, int] = (14, 8),
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Scatter plot of GPU utilization vs Power Intensity Factor.
    
    Reveals the relationship between reported utilization and actual
    computational work (power draw). High util + low power = bottlenecked.
    
    Args:
        df: DataFrame with utilization, PIF, and class columns
        util_col: Column name for GPU utilization
        pif_col: Column name for PIF
        class_col: Column name for efficiency class
        sample_size: Number of points to sample for plotting
        figsize: Figure size
        save_path: If provided, save figure to this path
        
    Returns:
        matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    apply_style(ax)
    
    # Sample data if needed
    if len(df) > sample_size:
        plot_df = df.sample(n=sample_size, random_state=42)
    else:
        plot_df = df
    
    # Plot by efficiency class
    for efficiency_class in plot_df[class_col].unique():
        mask = plot_df[class_col] == efficiency_class
        ax.scatter(
            plot_df.loc[mask, util_col],
            plot_df.loc[mask, pif_col],
            c=COLORS.get(efficiency_class, 'gray'),
            label=efficiency_class,
            alpha=0.5,
            s=20,
        )
    
    # Add reference lines
    ax.axhline(y=0.75, color='green', linestyle=':', alpha=0.3, linewidth=1, label='High efficiency threshold')
    ax.axhline(y=0.60, color='orange', linestyle=':', alpha=0.3, linewidth=1, label='Moderate threshold')
    ax.axvline(x=70, color='gray', linestyle=':', alpha=0.3, linewidth=1)
    
    # Labels and title
    ax.set_xlabel('GPU Utilization (%)', fontsize=12)
    ax.set_ylabel('Power Intensity Factor (PIF)', fontsize=12)
    ax.set_title('GPU Utilization vs Power Intensity Factor\nIdentifying Bottlenecked Workloads', fontsize=14, fontweight='bold')
    ax.legend(loc='lower right', fontsize=10)
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    
    # Add interpretation
    interpretation = (
        "SO WHAT: Points in upper-right (green) are efficient—busy AND productive. "
        "Points in lower-right (red) are bottlenecked—busy but stalled on I/O or memory. "
        "Large efficiency gaps suggest optimization opportunities."
    )
    add_interpretation_box(ax, interpretation)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_imbalance_heatmap(
    df: pd.DataFrame,
    time_col: str = 'timestamp_hour',
    group_col: str = 'nodegroup',
    metric_col: str = 'composite_imbalance_score',
    figsize: Tuple[int, int] = (16, 8),
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Heatmap of imbalance metric by nodegroup over time.
    
    Shows where and when imbalances occur across the fleet.
    
    Args:
        df: DataFrame with time, group, and metric columns
        time_col: Time column
        group_col: Grouping column (e.g., nodegroup)
        metric_col: Metric to display
        figsize: Figure size
        save_path: If provided, save figure to this path
        
    Returns:
        matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Pivot for heatmap
    pivot = df.pivot_table(
        index=group_col,
        columns=time_col,
        values=metric_col,
        aggfunc='mean'
    )
    
    # Create heatmap
    im = ax.imshow(pivot.values, aspect='auto', cmap='RdYlGn_r', vmin=0, vmax=1)
    
    # Labels
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    
    # Simplify x-axis for readability
    n_ticks = min(12, len(pivot.columns))
    tick_indices = np.linspace(0, len(pivot.columns) - 1, n_ticks, dtype=int)
    ax.set_xticks(tick_indices)
    ax.set_xticklabels([str(pivot.columns[i])[:13] for i in tick_indices], rotation=45, ha='right')
    
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Nodegroup', fontsize=12)
    ax.set_title(f'{metric_col.replace("_", " ").title()} by Nodegroup Over Time', fontsize=14, fontweight='bold')
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Imbalance Score (0=Healthy, 1=Critical)', fontsize=10)
    
    # Interpretation
    interpretation = (
        "SO WHAT: Red/orange cells indicate periods of imbalance. "
        "Horizontal bands suggest persistent issues with specific nodegroups. "
        "Vertical bands suggest fleet-wide events."
    )
    add_interpretation_box(ax, interpretation, y=-0.25)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_demand_vs_capacity_timeseries(
    df: pd.DataFrame,
    time_col: str = 'timestamp_hour',
    figsize: Tuple[int, int] = (16, 12),
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Multi-panel time series showing demand, capacity, and efficiency trends.
    
    Three panels:
    1. Pending workloads vs Available capacity
    2. GPU utilization vs RFU (efficiency gap)
    3. Composite imbalance score
    
    Args:
        df: DataFrame with aggregated metrics
        time_col: Time column
        figsize: Figure size
        save_path: If provided, save figure to this path
        
    Returns:
        matplotlib Figure
    """
    fig, axes = plt.subplots(3, 1, figsize=figsize, sharex=True)
    
    for ax in axes:
        apply_style(ax)
    
    ts = df[time_col]
    
    # Panel 1: Demand vs Capacity
    ax1 = axes[0]
    ax1.plot(ts, df['pending_workloads'], label='Pending Workloads', color='red', linewidth=2)
    ax1.plot(ts, df['allocatable_gpu_count'], label='Allocatable GPUs', color='green', linewidth=2)
    ax1.fill_between(ts, df['pending_workloads'], alpha=0.3, color='red')
    ax1.set_ylabel('Count', fontsize=11)
    ax1.set_title('Demand (Pending) vs Capacity (Allocatable GPUs)', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # Panel 2: Utilization vs RFU
    ax2 = axes[1]
    ax2.plot(ts, df['gpu_utilization_pct'], label='GPU Utilization %', color='steelblue', linewidth=2)
    if 'rfu_pct' in df.columns:
        ax2.plot(ts, df['rfu_pct'], label='Realized TFLOPS Util (RFU) %', color='darkgreen', linewidth=2)
        ax2.fill_between(ts, df['gpu_utilization_pct'], df['rfu_pct'], alpha=0.2, color='red', label='Efficiency Gap')
    ax2.set_ylabel('Percentage (%)', fontsize=11)
    ax2.set_title('GPU Utilization vs Realized Efficiency', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    
    # Panel 3: Imbalance Score
    ax3 = axes[2]
    if 'composite_imbalance_score' in df.columns:
        ax3.plot(ts, df['composite_imbalance_score'], label='Composite Imbalance Score', color='purple', linewidth=2)
        ax3.axhline(y=0.5, color='orange', linestyle='--', alpha=0.5, label='Warning threshold')
        ax3.axhline(y=0.7, color='red', linestyle='--', alpha=0.5, label='Critical threshold')
    ax3.set_ylabel('Score (0-1)', fontsize=11)
    ax3.set_xlabel('Time', fontsize=11)
    ax3.set_title('Composite Imbalance Score Over Time', fontsize=12, fontweight='bold')
    ax3.legend(loc='upper right')
    ax3.grid(True, alpha=0.3)
    
    # Format x-axis
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    ax3.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45, ha='right')
    
    # Overall interpretation
    fig.text(0.02, 0.02, 
             "SO WHAT: Top panel shows supply-demand balance. Middle panel reveals efficiency (gap=hidden waste). "
             "Bottom panel is the composite signal. Peaks in any panel warrant investigation.",
             fontsize=9, style='italic', wrap=True)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_top_contributors(
    contributors: Dict[str, pd.DataFrame],
    figsize: Tuple[int, int] = (16, 6),
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Bar charts showing top contributors to imbalance.
    
    Three panels: by nodegroup, by queue, by namespace.
    
    Args:
        contributors: Dictionary with 'by_nodegroup', 'by_queue', 'by_namespace' DataFrames
        figsize: Figure size
        save_path: If provided, save figure to this path
        
    Returns:
        matplotlib Figure
    """
    fig, axes = plt.subplots(1, 3, figsize=figsize)
    
    # By nodegroup
    ax1 = axes[0]
    ng_df = contributors['by_nodegroup']
    metric_col = [c for c in ng_df.columns if 'score' in c.lower() or 'imbalance' in c.lower()][0] if any('score' in c.lower() or 'imbalance' in c.lower() for c in ng_df.columns) else ng_df.columns[1]
    ax1.barh(ng_df['nodegroup'], ng_df[metric_col], color='steelblue')
    ax1.set_xlabel('Imbalance Score')
    ax1.set_title('Top Nodegroups', fontweight='bold')
    ax1.invert_yaxis()
    
    # By queue
    ax2 = axes[1]
    q_df = contributors['by_queue']
    ax2.barh(q_df['queue_name'], q_df['queue_pressure'], color='darkorange')
    ax2.set_xlabel('Queue Pressure Score')
    ax2.set_title('Top Queues', fontweight='bold')
    ax2.invert_yaxis()
    
    # By namespace
    ax3 = axes[2]
    ns_df = contributors['by_namespace']
    ax3.barh(ns_df['namespace'], ns_df['namespace_pressure'], color='darkgreen')
    ax3.set_xlabel('Namespace Pressure Score')
    ax3.set_title('Top Namespaces', fontweight='bold')
    ax3.invert_yaxis()
    
    fig.suptitle('Top Contributors to Demand-Capacity Imbalance', fontsize=14, fontweight='bold')
    
    # Interpretation
    fig.text(0.5, 0.02, 
             "SO WHAT: These are the primary sources of imbalance. "
             "Investigate these nodegroups/queues/namespaces first for optimization.",
             fontsize=9, style='italic', ha='center')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_efficiency_distribution(
    df: pd.DataFrame,
    class_col: str = 'efficiency_class',
    figsize: Tuple[int, int] = (10, 6),
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Pie/bar chart showing distribution of efficiency classes.
    
    Args:
        df: DataFrame with efficiency class column
        class_col: Column name for efficiency class
        figsize: Figure size
        save_path: If provided, save figure to this path
        
    Returns:
        matplotlib Figure
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    
    # Count by class
    class_counts = df[class_col].value_counts()
    
    # Pie chart
    colors = [COLORS.get(c, 'gray') for c in class_counts.index]
    ax1.pie(class_counts.values, labels=class_counts.index, colors=colors,
            autopct='%1.1f%%', startangle=90)
    ax1.set_title('Efficiency Class Distribution', fontweight='bold')
    
    # Bar chart
    ax2.bar(class_counts.index, class_counts.values, color=colors)
    ax2.set_xlabel('Efficiency Class')
    ax2.set_ylabel('Sample Count')
    ax2.set_title('Efficiency Class Counts', fontweight='bold')
    ax2.tick_params(axis='x', rotation=45)
    
    fig.text(0.5, 0.02, 
             "SO WHAT: 'Bottlenecked' samples indicate GPUs busy but not productive. "
             "High bottleneck % suggests fleet-wide I/O or data pipeline issues.",
             fontsize=9, style='italic', ha='center')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig
