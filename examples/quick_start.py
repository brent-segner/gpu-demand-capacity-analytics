#!/usr/bin/env python3
"""
Quick Start Script for GPU Demand vs Capacity Analytics
========================================================

This script demonstrates the core analysis workflow:
1. Generate synthetic data
2. Calculate efficiency metrics
3. Compute imbalance metrics
4. Print summary statistics

Usage:
    python examples/quick_start.py
    python examples/quick_start.py --scenario demand_exceeds_capacity
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np

from src.generators.synthetic_generator import generate_synthetic_data
from src.generators.scenarios import list_scenarios
from src.analysis.metrics import add_efficiency_metrics
from src.analysis.imbalance import (
    calculate_all_imbalance_metrics,
    identify_top_contributors,
)
from src.analysis.aggregations import build_unified_model, create_time_series_summary


def print_header(text: str) -> None:
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Quick start analysis')
    parser.add_argument('--scenario', type=str, default='balanced',
                       choices=list(list_scenarios().keys()),
                       help='Scenario to generate')
    parser.add_argument('--days', type=int, default=3, help='Days of data (default: 3 for quick demo)')
    parser.add_argument('--samples-per-hour', type=int, default=12, help='Samples per hour (default: 12 = 5min)')
    args = parser.parse_args()
    
    print_header("GPU Demand vs Capacity Analytics - Quick Start")
    print(f"\nScenario: {args.scenario}")
    print(f"Days: {args.days}")
    print(f"Samples per hour: {args.samples_per_hour}")
    
    # Step 1: Generate synthetic data
    print_header("Step 1: Generating Synthetic Data")
    kueue_df, dcgm_df, nodepool_df, manifest = generate_synthetic_data(
        scenario=args.scenario,
        seed=42,
        days=args.days,
        samples_per_hour=args.samples_per_hour,
        output_dir='data/synthetic',
    )
    
    # Step 2: Add efficiency metrics to DCGM data
    print_header("Step 2: Calculating Efficiency Metrics")
    dcgm_df = add_efficiency_metrics(dcgm_df)
    
    print("\nEfficiency Metrics Summary:")
    print(f"  Average GPU Utilization: {dcgm_df['gpu_utilization_pct'].mean():.1f}%")
    print(f"  Average Power Intensity Factor: {dcgm_df['power_intensity_factor'].mean():.3f}")
    print(f"  Average RFU: {dcgm_df['rfu_pct'].mean():.1f}%")
    print(f"  Average Efficiency Gap: {dcgm_df['efficiency_gap'].mean():.1f} pp")
    
    print("\nEfficiency Class Distribution:")
    for cls, count in dcgm_df['efficiency_class'].value_counts().items():
        pct = count / len(dcgm_df) * 100
        print(f"  {cls}: {count:,} ({pct:.1f}%)")
    
    # Step 3: Build unified model and calculate imbalance
    print_header("Step 3: Calculating Imbalance Metrics")
    imbalance_df = calculate_all_imbalance_metrics(kueue_df, dcgm_df, nodepool_df)
    
    print("\nImbalance Metrics Summary:")
    print(f"  Average Demand-Capacity Ratio: {imbalance_df['demand_capacity_ratio'].mean():.2f}")
    print(f"  Average Queue Pressure Score: {imbalance_df['queue_pressure_score'].mean():.3f}")
    print(f"  Average Composite Imbalance Score: {imbalance_df['composite_imbalance_score'].mean():.3f}")
    
    print("\nImbalance Severity Distribution:")
    for sev, count in imbalance_df['imbalance_severity'].value_counts().items():
        pct = count / len(imbalance_df) * 100
        print(f"  {sev}: {count:,} ({pct:.1f}%)")
    
    # Step 4: Identify top contributors
    print_header("Step 4: Top Contributors to Imbalance")
    contributors = identify_top_contributors(imbalance_df, kueue_df, n_top=3)
    
    print("\nTop Nodegroups:")
    print(contributors['by_nodegroup'].to_string(index=False))
    
    print("\nTop Queues:")
    print(contributors['by_queue'][['queue_name', 'pending_workloads', 'queue_pressure']].to_string(index=False))
    
    print("\nTop Namespaces:")
    print(contributors['by_namespace'][['namespace', 'pending_workloads', 'namespace_pressure']].to_string(index=False))
    
    # Step 5: Recommendations
    print_header("Step 5: Recommended Actions")
    
    avg_cis = imbalance_df['composite_imbalance_score'].mean()
    avg_dcr = imbalance_df['demand_capacity_ratio'].mean()
    avg_gap = dcgm_df['efficiency_gap'].mean()
    
    recommendations = []
    
    if avg_dcr > 1.0:
        recommendations.append("🔴 HIGH DEMAND: Demand exceeds capacity. Consider scaling up GPU resources or prioritizing workloads.")
    elif avg_dcr > 0.7:
        recommendations.append("🟡 MODERATE DEMAND: Approaching capacity limits. Monitor queue growth closely.")
    else:
        recommendations.append("🟢 HEALTHY DEMAND: Capacity comfortably exceeds current demand.")
    
    if avg_gap > 15:
        recommendations.append("🔴 HIGH EFFICIENCY GAP: Significant hidden waste. Investigate I/O bottlenecks, data pipelines.")
    elif avg_gap > 8:
        recommendations.append("🟡 MODERATE EFFICIENCY GAP: Some workloads may be data-starved. Review data loading patterns.")
    else:
        recommendations.append("🟢 HEALTHY EFFICIENCY: Workloads are generally productive.")
    
    bottleneck_pct = (dcgm_df['efficiency_class'] == 'Bottlenecked').sum() / len(dcgm_df) * 100
    if bottleneck_pct > 20:
        recommendations.append(f"🔴 BOTTLENECK ALERT: {bottleneck_pct:.1f}% of samples are bottlenecked. Prioritize optimization.")
    elif bottleneck_pct > 10:
        recommendations.append(f"🟡 BOTTLENECK WARNING: {bottleneck_pct:.1f}% bottlenecked. Review specific workloads.")
    
    for rec in recommendations:
        print(f"\n  {rec}")
    
    print_header("Analysis Complete")
    print("\nGenerated files in data/synthetic/:")
    print("  - manifest.json (generation metadata)")
    print("  - kueue_metrics.csv (Kueue demand signals)")
    print("  - dcgm_metrics.csv (DCGM efficiency signals)")
    print("  - nodepool_state.csv (Capacity inventory)")
    print("\nNext steps:")
    print("  - Open notebooks/demand_capacity_analysis.ipynb for detailed analysis")
    print("  - Try different scenarios: --scenario demand_exceeds_capacity")
    print("  - See docs/DATA_DICTIONARY.md for metric definitions")
    

if __name__ == '__main__':
    main()
