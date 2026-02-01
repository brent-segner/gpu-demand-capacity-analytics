"""
Imbalance Metrics
=================

Functions to calculate demand-versus-capacity imbalance metrics.
These are the core analytical outputs of the project.

All formulas are documented in docs/DATA_DICTIONARY.md.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple

from .metrics import normalize_series


def calculate_demand_capacity_ratio(
    pending_workloads: pd.Series,
    available_capacity: pd.Series,
    epsilon: float = 1e-6
) -> pd.Series:
    """
    Calculate Demand-Capacity Ratio (DCR).
    
    DCR = pending_workloads / available_capacity
    
    Interpretation:
    - DCR < 0.5: Healthy, capacity exceeds demand
    - DCR 0.5-1.0: Moderate pressure
    - DCR > 1.0: Demand exceeds capacity
    - DCR > 2.0: Severe shortage
    
    Args:
        pending_workloads: Number of workloads waiting
        available_capacity: Available GPU capacity
        epsilon: Small value to avoid division by zero
        
    Returns:
        Series of DCR values
    """
    return pending_workloads / (available_capacity + epsilon)


def calculate_queue_pressure_score(
    pending_workloads: pd.Series,
    wait_time_seconds: pd.Series,
    pending_weight: float = 0.6,
    wait_weight: float = 0.4,
) -> pd.Series:
    """
    Calculate Queue Pressure Score (QPS).
    
    QPS = pending_weight × norm(pending) + wait_weight × norm(wait_time)
    
    Combines queue depth and wait time into a single urgency score.
    
    Interpretation:
    - QPS < 0.3: Low pressure
    - QPS 0.3-0.6: Moderate pressure
    - QPS > 0.6: High pressure
    - QPS > 0.8: Critical
    
    Args:
        pending_workloads: Number of pending workloads
        wait_time_seconds: Admission wait time in seconds
        pending_weight: Weight for pending component (default 0.6)
        wait_weight: Weight for wait time component (default 0.4)
        
    Returns:
        Series of QPS values (0-1)
    """
    norm_pending = normalize_series(pending_workloads)
    norm_wait = normalize_series(wait_time_seconds)
    
    return pending_weight * norm_pending + wait_weight * norm_wait


def calculate_composite_imbalance_score(
    dcr: pd.Series,
    efficiency_gap: pd.Series,
    qps: pd.Series,
    dcr_weight: float = 0.5,
    gap_weight: float = 0.3,
    qps_weight: float = 0.2,
) -> pd.Series:
    """
    Calculate Composite Imbalance Score (CIS).
    
    CIS = dcr_weight × norm(DCR) + gap_weight × norm(efficiency_gap) + qps_weight × QPS
    
    Overall indicator combining demand pressure and efficiency signals.
    
    Interpretation:
    - CIS < 0.3: Well-balanced
    - CIS 0.3-0.5: Minor imbalances
    - CIS > 0.5: Significant imbalance
    - CIS > 0.7: Severe imbalance
    
    Args:
        dcr: Demand-Capacity Ratio values
        efficiency_gap: Efficiency gap values (percentage points)
        qps: Queue Pressure Score values
        dcr_weight: Weight for DCR (default 0.5)
        gap_weight: Weight for efficiency gap (default 0.3)
        qps_weight: Weight for QPS (default 0.2)
        
    Returns:
        Series of CIS values (0-1)
    """
    norm_dcr = normalize_series(dcr)
    norm_gap = normalize_series(efficiency_gap.clip(0, None))  # Only positive gaps
    # QPS is already normalized
    
    return dcr_weight * norm_dcr + gap_weight * norm_gap + qps_weight * qps


def classify_imbalance_severity(cis: pd.Series, dcr: pd.Series) -> pd.Series:
    """
    Classify imbalance severity based on CIS and DCR.
    
    Categories:
    - Critical: CIS > 0.7 OR DCR > 2.0
    - Warning: CIS > 0.5 OR DCR > 1.0
    - Moderate: CIS > 0.3
    - Healthy: CIS <= 0.3
    
    Args:
        cis: Composite Imbalance Score values
        dcr: Demand-Capacity Ratio values
        
    Returns:
        Series of severity labels
    """
    def classify(cis_val, dcr_val):
        if cis_val > 0.7 or dcr_val > 2.0:
            return 'Critical'
        elif cis_val > 0.5 or dcr_val > 1.0:
            return 'Warning'
        elif cis_val > 0.3:
            return 'Moderate'
        else:
            return 'Healthy'
    
    return pd.Series([classify(c, d) for c, d in zip(cis, dcr)], index=cis.index)


def calculate_all_imbalance_metrics(
    kueue_df: pd.DataFrame,
    dcgm_df: pd.DataFrame,
    nodepool_df: pd.DataFrame,
    time_col: str = 'timestamp_hour',
    group_col: str = 'nodegroup',
) -> pd.DataFrame:
    """
    Calculate all imbalance metrics for aggregated data.
    
    Joins demand (Kueue), capacity (nodepool), and efficiency (DCGM) signals
    to produce comprehensive imbalance analysis.
    
    Args:
        kueue_df: Kueue metrics DataFrame
        dcgm_df: DCGM metrics DataFrame (with efficiency metrics added)
        nodepool_df: Nodepool state DataFrame
        time_col: Column for time aggregation
        group_col: Column for group aggregation (usually nodegroup)
        
    Returns:
        DataFrame with imbalance metrics per (time, group)
    """
    # Aggregate Kueue metrics
    kueue_agg = kueue_df.groupby([time_col, group_col]).agg({
        'pending_workloads': 'sum',
        'admission_wait_time_seconds': 'mean',
        'admitted_active_workloads': 'sum',
        'resource_usage': 'sum',
    }).reset_index()
    
    # Aggregate DCGM metrics
    dcgm_agg = dcgm_df.groupby([time_col, group_col]).agg({
        'gpu_utilization_pct': 'mean',
        'power_intensity_factor': 'mean',
        'rfu_pct': 'mean',
        'efficiency_gap': 'mean',
        'memory_pressure_pct': 'mean',
    }).reset_index()
    
    # Aggregate nodepool
    nodepool_agg = nodepool_df.groupby([time_col, group_col]).agg({
        'capacity_gpu_count': 'mean',
        'allocatable_gpu_count': 'mean',
    }).reset_index()
    
    # Join all
    result = kueue_agg.merge(nodepool_agg, on=[time_col, group_col], how='outer')
    result = result.merge(dcgm_agg, on=[time_col, group_col], how='outer')
    
    # Calculate available capacity
    result['available_capacity'] = (
        result['allocatable_gpu_count'] - result['resource_usage']
    ).clip(lower=0)
    
    # Calculate imbalance metrics
    result['demand_capacity_ratio'] = calculate_demand_capacity_ratio(
        result['pending_workloads'],
        result['available_capacity']
    )
    
    result['queue_pressure_score'] = calculate_queue_pressure_score(
        result['pending_workloads'],
        result['admission_wait_time_seconds']
    )
    
    result['composite_imbalance_score'] = calculate_composite_imbalance_score(
        result['demand_capacity_ratio'],
        result['efficiency_gap'],
        result['queue_pressure_score']
    )
    
    result['imbalance_severity'] = classify_imbalance_severity(
        result['composite_imbalance_score'],
        result['demand_capacity_ratio']
    )
    
    return result


def identify_top_contributors(
    imbalance_df: pd.DataFrame,
    kueue_df: pd.DataFrame,
    n_top: int = 5,
    metric: str = 'composite_imbalance_score',
) -> Dict[str, pd.DataFrame]:
    """
    Identify top contributors to imbalance.
    
    Returns breakdown by queue and namespace.
    
    Args:
        imbalance_df: DataFrame with imbalance metrics
        kueue_df: Original Kueue metrics for drill-down
        n_top: Number of top contributors to return
        metric: Metric to rank by
        
    Returns:
        Dictionary with 'by_nodegroup', 'by_queue', 'by_namespace' DataFrames
    """
    # Top nodegroups
    top_nodegroups = imbalance_df.groupby('nodegroup').agg({
        metric: 'mean',
        'pending_workloads': 'sum',
        'efficiency_gap': 'mean',
    }).nlargest(n_top, metric).reset_index()
    
    # Top queues
    queue_metrics = kueue_df.groupby('queue_name').agg({
        'pending_workloads': 'sum',
        'admission_wait_time_seconds': 'mean',
        'admitted_active_workloads': 'sum',
    }).reset_index()
    queue_metrics['queue_pressure'] = calculate_queue_pressure_score(
        queue_metrics['pending_workloads'],
        queue_metrics['admission_wait_time_seconds']
    )
    top_queues = queue_metrics.nlargest(n_top, 'queue_pressure')
    
    # Top namespaces
    namespace_metrics = kueue_df.groupby('namespace').agg({
        'pending_workloads': 'sum',
        'admission_wait_time_seconds': 'mean',
        'resource_usage': 'sum',
    }).reset_index()
    namespace_metrics['namespace_pressure'] = calculate_queue_pressure_score(
        namespace_metrics['pending_workloads'],
        namespace_metrics['admission_wait_time_seconds']
    )
    top_namespaces = namespace_metrics.nlargest(n_top, 'namespace_pressure')
    
    return {
        'by_nodegroup': top_nodegroups,
        'by_queue': top_queues,
        'by_namespace': top_namespaces,
    }
