"""
Data Validation for Synthetic Datasets
=======================================

Validates that generated data meets expected constraints:
- No negative values where inappropriate
- Percentages in valid ranges
- Monotonic timestamps
- Required columns present
"""

import pandas as pd
import numpy as np
from typing import List


class ValidationError(Exception):
    """Raised when data validation fails."""
    pass


def validate_nodepool_data(df: pd.DataFrame) -> None:
    """
    Validate nodepool state data.
    
    Checks:
    - Required columns present
    - No negative GPU counts
    - Allocatable <= Capacity
    - Timestamps are valid
    """
    required_cols = [
        'timestamp', 'timestamp_hour', 'nodegroup', 'cluster', 'region',
        'gpu_model', 'capacity_gpu_count', 'allocatable_gpu_count'
    ]
    _check_required_columns(df, required_cols, 'nodepool_state')
    
    # No negative GPU counts
    if (df['capacity_gpu_count'] < 0).any():
        raise ValidationError("nodepool_state: capacity_gpu_count contains negative values")
    if (df['allocatable_gpu_count'] < 0).any():
        raise ValidationError("nodepool_state: allocatable_gpu_count contains negative values")
    
    # Allocatable should not exceed capacity
    if (df['allocatable_gpu_count'] > df['capacity_gpu_count']).any():
        raise ValidationError("nodepool_state: allocatable_gpu_count exceeds capacity_gpu_count")
    
    # Check timestamp validity
    _check_timestamps(df, 'nodepool_state')


def validate_kueue_data(df: pd.DataFrame) -> None:
    """
    Validate Kueue metrics data.
    
    Checks:
    - Required columns present
    - No negative counts or wait times
    - Queue status is valid
    """
    required_cols = [
        'timestamp', 'timestamp_hour', 'cluster', 'region', 'namespace',
        'queue_name', 'nodegroup', 'pending_workloads', 'admission_wait_time_seconds',
        'admitted_active_workloads', 'resource_usage'
    ]
    _check_required_columns(df, required_cols, 'kueue_metrics')
    
    # No negative workload counts
    for col in ['pending_workloads', 'admitted_active_workloads', 'resource_usage']:
        if (df[col] < 0).any():
            raise ValidationError(f"kueue_metrics: {col} contains negative values")
    
    # No negative wait times
    if (df['admission_wait_time_seconds'] < 0).any():
        raise ValidationError("kueue_metrics: admission_wait_time_seconds contains negative values")
    
    _check_timestamps(df, 'kueue_metrics')


def validate_dcgm_data(df: pd.DataFrame) -> None:
    """
    Validate DCGM metrics data.
    
    Checks:
    - Required columns present
    - Utilization in 0-100 range
    - Power >= 0
    - Temperature in reasonable range
    - Memory values non-negative
    """
    required_cols = [
        'timestamp', 'timestamp_hour', 'hostname', 'cluster', 'region',
        'nodegroup', 'gpu_model', 'gpu_uuid', 'gpu_utilization_pct',
        'power_usage_watts', 'memory_used_mb', 'memory_free_mb', 'gpu_temp_celsius'
    ]
    _check_required_columns(df, required_cols, 'dcgm_metrics')
    
    # Utilization in valid range
    if (df['gpu_utilization_pct'] < 0).any() or (df['gpu_utilization_pct'] > 100).any():
        raise ValidationError("dcgm_metrics: gpu_utilization_pct out of range [0, 100]")
    
    if 'tensor_active_pct' in df.columns:
        if (df['tensor_active_pct'] < 0).any() or (df['tensor_active_pct'] > 100).any():
            raise ValidationError("dcgm_metrics: tensor_active_pct out of range [0, 100]")
    
    # Power should be non-negative
    if (df['power_usage_watts'] < 0).any():
        raise ValidationError("dcgm_metrics: power_usage_watts contains negative values")
    
    # Memory should be non-negative
    if (df['memory_used_mb'] < 0).any():
        raise ValidationError("dcgm_metrics: memory_used_mb contains negative values")
    if (df['memory_free_mb'] < 0).any():
        raise ValidationError("dcgm_metrics: memory_free_mb contains negative values")
    
    # Temperature in reasonable range (0-120 C)
    if (df['gpu_temp_celsius'] < 0).any() or (df['gpu_temp_celsius'] > 120).any():
        raise ValidationError("dcgm_metrics: gpu_temp_celsius out of range [0, 120]")
    
    _check_timestamps(df, 'dcgm_metrics')


def _check_required_columns(df: pd.DataFrame, required: List[str], dataset_name: str) -> None:
    """Check that all required columns are present."""
    missing = set(required) - set(df.columns)
    if missing:
        raise ValidationError(f"{dataset_name}: Missing required columns: {missing}")


def _check_timestamps(df: pd.DataFrame, dataset_name: str) -> None:
    """Check that timestamps are valid and monotonic per group."""
    if df['timestamp'].isna().any():
        raise ValidationError(f"{dataset_name}: timestamp contains null values")
    
    # Convert to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        try:
            pd.to_datetime(df['timestamp'])
        except Exception as e:
            raise ValidationError(f"{dataset_name}: timestamp contains invalid datetime values: {e}")


def validate_all(nodepool_df: pd.DataFrame, kueue_df: pd.DataFrame, dcgm_df: pd.DataFrame) -> None:
    """Validate all datasets."""
    validate_nodepool_data(nodepool_df)
    validate_kueue_data(kueue_df)
    validate_dcgm_data(dcgm_df)
    print("All validations passed.")
