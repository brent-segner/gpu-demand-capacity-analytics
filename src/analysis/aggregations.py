"""
Time-Indexed Aggregations
=========================

Functions to aggregate raw metrics to different time granularities
and build the unified analysis model.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict


def aggregate_to_hourly(
    df: pd.DataFrame,
    time_col: str = 'timestamp',
    group_cols: Optional[List[str]] = None,
    agg_config: Optional[Dict] = None,
) -> pd.DataFrame:
    """
    Aggregate data to hourly granularity.
    
    Args:
        df: Input DataFrame
        time_col: Timestamp column name
        group_cols: Additional grouping columns (e.g., ['nodegroup', 'cluster'])
        agg_config: Dictionary of {column: aggregation_function}
        
    Returns:
        Hourly aggregated DataFrame
    """
    df = df.copy()
    
    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
        df[time_col] = pd.to_datetime(df[time_col])
    
    # Create hour floor
    df['timestamp_hour'] = df[time_col].dt.floor('H')
    
    # Build grouping columns
    group_by = ['timestamp_hour']
    if group_cols:
        group_by.extend(group_cols)
    
    # Default aggregation if not provided
    if agg_config is None:
        # Auto-detect numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c not in group_by]
        agg_config = {col: 'mean' for col in numeric_cols}
    
    return df.groupby(group_by).agg(agg_config).reset_index()


def build_unified_model(
    kueue_df: pd.DataFrame,
    dcgm_df: pd.DataFrame,
    nodepool_df: pd.DataFrame,
    time_col: str = 'timestamp_hour',
    join_col: str = 'nodegroup',
) -> pd.DataFrame:
    """
    Build unified time-indexed model joining all data sources.
    
    Joins:
    - Kueue metrics (demand signals)
    - DCGM metrics (capacity/efficiency signals)
    - Nodepool state (inventory)
    
    Args:
        kueue_df: Kueue metrics DataFrame
        dcgm_df: DCGM metrics DataFrame
        nodepool_df: Nodepool state DataFrame
        time_col: Time column for joining
        join_col: Spatial column for joining
        
    Returns:
        Unified DataFrame with all metrics
    """
    # Prepare each dataset
    kueue_hourly = aggregate_to_hourly(
        kueue_df,
        group_cols=[join_col],
        agg_config={
            'pending_workloads': 'sum',
            'admission_wait_time_seconds': 'mean',
            'admitted_active_workloads': 'sum',
            'resource_usage': 'sum',
            'evicted_workloads_total': 'max',
        }
    )
    
    dcgm_hourly = aggregate_to_hourly(
        dcgm_df,
        group_cols=[join_col],
        agg_config={
            'gpu_utilization_pct': 'mean',
            'power_usage_watts': 'mean',
            'power_intensity_factor': 'mean' if 'power_intensity_factor' in dcgm_df.columns else 'first',
            'rfu_pct': 'mean' if 'rfu_pct' in dcgm_df.columns else 'first',
            'efficiency_gap': 'mean' if 'efficiency_gap' in dcgm_df.columns else 'first',
            'memory_used_mb': 'mean',
            'gpu_temp_celsius': 'mean',
            'tensor_active_pct': 'mean' if 'tensor_active_pct' in dcgm_df.columns else 'first',
        }
    )
    
    nodepool_hourly = aggregate_to_hourly(
        nodepool_df,
        group_cols=[join_col],
        agg_config={
            'capacity_gpu_count': 'mean',
            'allocatable_gpu_count': 'mean',
        }
    )
    
    # Join datasets
    unified = kueue_hourly.merge(
        nodepool_hourly,
        on=[time_col, join_col],
        how='outer',
        suffixes=('_kueue', '_nodepool')
    )
    
    unified = unified.merge(
        dcgm_hourly,
        on=[time_col, join_col],
        how='outer',
        suffixes=('', '_dcgm')
    )
    
    # Fill missing values
    unified = unified.fillna({
        'pending_workloads': 0,
        'admission_wait_time_seconds': 0,
        'admitted_active_workloads': 0,
        'resource_usage': 0,
    })
    
    return unified


def create_time_series_summary(
    unified_df: pd.DataFrame,
    time_col: str = 'timestamp_hour',
) -> pd.DataFrame:
    """
    Create fleet-wide time series summary.
    
    Aggregates across all nodegroups to show overall trends.
    
    Args:
        unified_df: Unified model DataFrame
        time_col: Time column
        
    Returns:
        DataFrame with one row per timestamp
    """
    return unified_df.groupby(time_col).agg({
        'pending_workloads': 'sum',
        'admission_wait_time_seconds': 'mean',
        'admitted_active_workloads': 'sum',
        'capacity_gpu_count': 'sum',
        'allocatable_gpu_count': 'sum',
        'resource_usage': 'sum',
        'gpu_utilization_pct': 'mean',
        'power_intensity_factor': 'mean',
        'rfu_pct': 'mean',
        'efficiency_gap': 'mean',
    }).reset_index()


def calculate_rolling_metrics(
    df: pd.DataFrame,
    time_col: str = 'timestamp_hour',
    window: int = 24,
    metrics: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Calculate rolling statistics for trend analysis.
    
    Args:
        df: Input DataFrame
        time_col: Time column
        window: Rolling window size (in time periods)
        metrics: Columns to calculate rolling stats for
        
    Returns:
        DataFrame with rolling mean and std columns
    """
    df = df.copy().sort_values(time_col)
    
    if metrics is None:
        metrics = df.select_dtypes(include=[np.number]).columns.tolist()
        metrics = [m for m in metrics if m not in [time_col]]
    
    for metric in metrics:
        if metric in df.columns:
            df[f'{metric}_rolling_mean'] = df[metric].rolling(window, min_periods=1).mean()
            df[f'{metric}_rolling_std'] = df[metric].rolling(window, min_periods=1).std()
    
    return df
