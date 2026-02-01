"""
Derived Metrics Calculations
============================

Functions to calculate derived metrics from raw DCGM and Kueue data.
All formulas are documented in docs/DATA_DICTIONARY.md.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional

# GPU specifications for PIF and RFU calculations
GPU_SPECS = {
    'NVIDIA A10G': {'max_power': 300, 'achievable_tflops': 35},
    'NVIDIA A100-SXM4-40GB': {'max_power': 400, 'achievable_tflops': 102},
    'NVIDIA H100 80GB HBM3': {'max_power': 700, 'achievable_tflops': 646},
}


def calculate_power_intensity_factor(df: pd.DataFrame, power_col: str = 'power_usage_watts', model_col: str = 'gpu_model') -> pd.Series:
    """
    Calculate Power Intensity Factor (PIF).
    
    PIF = current_power / max_gpu_power
    
    Args:
        df: DataFrame with power and GPU model columns
        power_col: Column name for power usage
        model_col: Column name for GPU model
        
    Returns:
        Series of PIF values (0.0 to 1.0)
    """
    max_power = df[model_col].map(lambda x: GPU_SPECS.get(x, {}).get('max_power', 400))
    pif = df[power_col] / max_power
    return pif.clip(0, 1)


def calculate_realized_tflops(df: pd.DataFrame, pif: pd.Series, model_col: str = 'gpu_model') -> pd.Series:
    """
    Calculate Realized TFLOPS.
    
    Realized TFLOPS = achievable_tflops × PIF
    
    Args:
        df: DataFrame with GPU model column
        pif: Series of PIF values
        model_col: Column name for GPU model
        
    Returns:
        Series of realized TFLOPS values
    """
    achievable = df[model_col].map(lambda x: GPU_SPECS.get(x, {}).get('achievable_tflops', 100))
    return achievable * pif


def calculate_rfu(df: pd.DataFrame, realized_tflops: pd.Series, model_col: str = 'gpu_model') -> pd.Series:
    """
    Calculate Realized TFLOPS Utilization (RFU) as percentage.
    
    RFU = (realized_tflops / achievable_tflops) × 100
    
    Args:
        df: DataFrame with GPU model column
        realized_tflops: Series of realized TFLOPS values
        model_col: Column name for GPU model
        
    Returns:
        Series of RFU percentage values (0-100)
    """
    achievable = df[model_col].map(lambda x: GPU_SPECS.get(x, {}).get('achievable_tflops', 100))
    rfu = (realized_tflops / achievable) * 100
    return rfu.clip(0, 100)


def calculate_efficiency_gap(gpu_util: pd.Series, rfu: pd.Series) -> pd.Series:
    """
    Calculate efficiency gap.
    
    Efficiency Gap = GPU Utilization % - RFU %
    
    Positive gap indicates hidden inefficiency (GPU busy but not productive).
    
    Args:
        gpu_util: Series of GPU utilization percentages
        rfu: Series of RFU percentages
        
    Returns:
        Series of efficiency gap values (percentage points)
    """
    return gpu_util - rfu


def calculate_memory_pressure(used_mb: pd.Series, free_mb: pd.Series) -> pd.Series:
    """
    Calculate memory pressure percentage.
    
    Memory Pressure = used / (used + free) × 100
    
    Args:
        used_mb: Series of memory used values
        free_mb: Series of memory free values
        
    Returns:
        Series of memory pressure percentages (0-100)
    """
    total = used_mb + free_mb
    return (used_mb / total * 100).fillna(0)


def classify_efficiency(gpu_util: pd.Series, pif: pd.Series) -> pd.Series:
    """
    Classify GPU efficiency based on utilization and PIF.
    
    Categories:
    - Efficient: util > 70% AND pif > 0.75
    - Bottlenecked: util > 70% AND pif < 0.60
    - Moderate: util 40-70% AND pif > 0.50
    - Inefficient: util > 10% AND not above
    - Idle: util < 10%
    
    Args:
        gpu_util: Series of GPU utilization percentages
        pif: Series of PIF values
        
    Returns:
        Series of efficiency class labels
    """
    def classify_row(util, pif_val):
        if util < 10:
            return 'Idle'
        elif util >= 70 and pif_val >= 0.75:
            return 'Efficient'
        elif util >= 70 and pif_val < 0.60:
            return 'Bottlenecked'
        elif util >= 40 and pif_val >= 0.50:
            return 'Moderate'
        else:
            return 'Inefficient'
    
    return pd.Series([classify_row(u, p) for u, p in zip(gpu_util, pif)], index=gpu_util.index)


def add_efficiency_metrics(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
    """
    Add all efficiency metrics to a DCGM DataFrame.
    
    Adds columns:
    - power_intensity_factor (PIF)
    - realized_tflops
    - rfu_pct (Realized TFLOPS Utilization %)
    - efficiency_gap
    - memory_pressure_pct
    - efficiency_class
    
    Args:
        df: DataFrame with DCGM metrics
        inplace: If True, modify df in place
        
    Returns:
        DataFrame with added columns
    """
    if not inplace:
        df = df.copy()
    
    df['power_intensity_factor'] = calculate_power_intensity_factor(df)
    df['realized_tflops'] = calculate_realized_tflops(df, df['power_intensity_factor'])
    df['rfu_pct'] = calculate_rfu(df, df['realized_tflops'])
    df['efficiency_gap'] = calculate_efficiency_gap(df['gpu_utilization_pct'], df['rfu_pct'])
    df['memory_pressure_pct'] = calculate_memory_pressure(df['memory_used_mb'], df['memory_free_mb'])
    df['efficiency_class'] = classify_efficiency(df['gpu_utilization_pct'], df['power_intensity_factor'])
    
    return df


def normalize_series(s: pd.Series, method: str = 'minmax', window: Optional[int] = None) -> pd.Series:
    """
    Normalize a series to 0-1 range.
    
    Args:
        s: Series to normalize
        method: 'minmax' or 'percentile'
        window: If provided, use rolling window for min/max
        
    Returns:
        Normalized series (0-1)
    """
    if method == 'minmax':
        if window:
            min_val = s.rolling(window, min_periods=1).min()
            max_val = s.rolling(window, min_periods=1).max()
        else:
            min_val = s.min()
            max_val = s.max()
        
        range_val = max_val - min_val
        if isinstance(range_val, pd.Series):
            range_val = range_val.replace(0, 1)
        elif range_val == 0:
            range_val = 1
        
        return (s - min_val) / range_val
    
    elif method == 'percentile':
        return s.rank(pct=True)
    
    else:
        raise ValueError(f"Unknown normalization method: {method}")
