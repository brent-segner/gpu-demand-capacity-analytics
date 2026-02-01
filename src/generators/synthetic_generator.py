"""
GPU Demand vs Capacity Analytics - Synthetic Data Generator
============================================================

Generates synthetic datasets for analyzing GPU demand-versus-capacity imbalances
in Kueue-managed Kubernetes clusters.

All data is 100% synthetic. No real production data is used.

Usage:
    python -m src.generators.synthetic_generator
    python -m src.generators.synthetic_generator --scenario demand_exceeds_capacity
    python -m src.generators.synthetic_generator --seed 42 --days 7 --gpus 100
"""

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .scenarios import get_scenario_config
from .validators import validate_dcgm_data, validate_kueue_data, validate_nodepool_data


# GPU Specifications (published values)
GPU_SPECS = {
    'NVIDIA A10G': {
        'max_power': 300,
        'idle_power': 40,
        'memory_total': 24576,
        'theoretical_tflops_fp16': 125,
        'achievable_tflops_fp16': 35,
    },
    'NVIDIA A100-SXM4-40GB': {
        'max_power': 400,
        'idle_power': 50,
        'memory_total': 40960,
        'theoretical_tflops_fp16': 312,
        'achievable_tflops_fp16': 102,
    },
    'NVIDIA H100 80GB HBM3': {
        'max_power': 700,
        'idle_power': 70,
        'memory_total': 81920,
        'theoretical_tflops_fp16': 1979,
        'achievable_tflops_fp16': 646,
    },
}

# Nodegroup configurations
NODEGROUP_CONFIGS = [
    {'name': 'ml-training-h100', 'gpu_model': 'NVIDIA H100 80GB HBM3', 'gpu_count': 32, 'cluster': 'gen-ai-cluster-1', 'region': 'us-west-2'},
    {'name': 'ml-training-a100', 'gpu_model': 'NVIDIA A100-SXM4-40GB', 'gpu_count': 48, 'cluster': 'gen-ai-cluster-1', 'region': 'us-west-2'},
    {'name': 'ml-inference-a10g', 'gpu_model': 'NVIDIA A10G', 'gpu_count': 64, 'cluster': 'gen-ai-cluster-1', 'region': 'us-west-2'},
    {'name': 'research-a100', 'gpu_model': 'NVIDIA A100-SXM4-40GB', 'gpu_count': 24, 'cluster': 'gen-ai-cluster-2', 'region': 'us-east-1'},
    {'name': 'research-h100', 'gpu_model': 'NVIDIA H100 80GB HBM3', 'gpu_count': 16, 'cluster': 'gen-ai-cluster-2', 'region': 'us-east-1'},
]

QUEUE_NODEGROUP_MAP = {
    'training-h100-queue': 'ml-training-h100',
    'training-a100-queue': 'ml-training-a100',
    'inference-a10g-queue': 'ml-inference-a10g',
    'research-a100-queue': 'research-a100',
    'research-h100-queue': 'research-h100',
    'batch-training-queue': 'ml-training-a100',
}

NAMESPACES = ['ml-training', 'ml-inference', 'research', 'fraud-detection', 'recommendations', 'nlp-platform']


def generate_timestamps(start_date: datetime, days: int, samples_per_hour: int = 60) -> pd.DatetimeIndex:
    total_samples = days * 24 * samples_per_hour
    return pd.date_range(start=start_date, periods=total_samples, freq=f'{60 // samples_per_hour}min')


def generate_nodepool_state(nodegroups: List[Dict], timestamps: pd.DatetimeIndex, rng: np.random.Generator, scenario_config: Dict) -> pd.DataFrame:
    records = []
    for ts in timestamps:
        for ng in nodegroups:
            base_count = ng['gpu_count']
            scale_factor = scenario_config.get('autoscale_variance', 0.05)
            actual_count = max(1, int(base_count * (1 + rng.uniform(-scale_factor, scale_factor))))
            records.append({
                'timestamp': ts, 'timestamp_hour': ts.floor('H'), 'nodegroup': ng['name'],
                'cluster': ng['cluster'], 'region': ng['region'], 'gpu_model': ng['gpu_model'],
                'capacity_gpu_count': actual_count, 'allocatable_gpu_count': int(actual_count * 0.95),
            })
    return pd.DataFrame(records)


def generate_kueue_metrics(queue_nodegroup_map: Dict, namespaces: List, timestamps: pd.DatetimeIndex, rng: np.random.Generator, scenario_config: Dict, nodepool_df: pd.DataFrame) -> pd.DataFrame:
    records = []
    capacity_lookup = nodepool_df.groupby(['timestamp_hour', 'nodegroup'])['capacity_gpu_count'].first().to_dict()
    cluster_lookup = nodepool_df.groupby('nodegroup')['cluster'].first().to_dict()
    region_lookup = nodepool_df.groupby('nodegroup')['region'].first().to_dict()
    
    for ts in timestamps:
        hour = ts.hour
        ts_hour = ts.floor('H')
        time_multiplier = 1.2 + 0.3 * np.sin((hour - 9) * np.pi / 9) if 9 <= hour <= 18 else 0.6
        
        for queue_name, nodegroup in queue_nodegroup_map.items():
            capacity = capacity_lookup.get((ts_hour, nodegroup), 32)
            namespace = rng.choice(['ml-training', 'nlp-platform'] if 'training' in queue_name else ['ml-inference', 'fraud-detection', 'recommendations'] if 'inference' in queue_name else namespaces)
            
            demand_ratio = scenario_config.get('demand_capacity_ratio', 0.7)
            base_pending = int(capacity * demand_ratio * time_multiplier)
            if scenario_config.get('high_demand_queues') and nodegroup in scenario_config['high_demand_queues']:
                base_pending = int(base_pending * 1.8)
            
            pending = max(0, int(base_pending + rng.normal(0, base_pending * 0.2)))
            base_wait = scenario_config.get('base_wait_seconds', 60)
            wait_time = max(0, int(base_wait * (1 + pending / capacity) + rng.normal(0, 30)))
            active_ratio = scenario_config.get('active_ratio', 0.8)
            max_active = int(capacity * active_ratio)
            active = min(max_active, max(0, int(capacity - pending * 0.3 + rng.normal(0, 3))))
            
            records.append({
                'timestamp': ts, 'timestamp_hour': ts_hour,
                'cluster': cluster_lookup.get(nodegroup, 'unknown'),
                'region': region_lookup.get(nodegroup, 'unknown'),
                'namespace': namespace, 'queue_name': queue_name, 'nodegroup': nodegroup,
                'pending_workloads': pending, 'admission_wait_time_seconds': wait_time,
                'admitted_active_workloads': active,
                'admitted_workloads_total': int(ts.timestamp() / 3600) * rng.integers(5, 15),
                'evicted_workloads_total': int(int(ts.timestamp() / 3600) * rng.integers(5, 15) * scenario_config.get('eviction_rate', 0.02)),
                'resource_usage': active, 'resource_reservation': active + min(pending, int(capacity * 0.2)),
                'quota_reserved_wait_time_seconds': int(wait_time * 0.7),
                'reserving_active_workloads': min(active, pending), 'queue_status': 1,
            })
    return pd.DataFrame(records)


def generate_dcgm_metrics(nodegroups: List[Dict], timestamps: pd.DatetimeIndex, rng: np.random.Generator, scenario_config: Dict, kueue_df: pd.DataFrame) -> pd.DataFrame:
    records = []
    demand_lookup = kueue_df.groupby(['timestamp_hour', 'nodegroup'])['admitted_active_workloads'].sum().to_dict()
    
    for ng in nodegroups:
        gpu_spec = GPU_SPECS[ng['gpu_model']]
        for gpu_idx in range(ng['gpu_count']):
            gpu_uuid = f"GPU-{ng['name'][:8]}-{gpu_idx:04d}-{rng.integers(1000, 9999)}"
            hostname = f"ip-10-{rng.integers(0, 255)}-{rng.integers(0, 255)}-{rng.integers(0, 255)}.{ng['region']}.compute.internal"
            
            for ts in timestamps:
                ts_hour = ts.floor('H')
                active_workloads = demand_lookup.get((ts_hour, ng['name']), ng['gpu_count'] * 0.5)
                utilization_base = min(100, (active_workloads / ng['gpu_count']) * 100)
                
                profile = scenario_config.get('workload_profile', 'balanced')
                if profile == 'efficient':
                    util = min(100, max(0, utilization_base + rng.normal(10, 5)))
                    power_ratio = 0.75 + rng.uniform(0, 0.2)
                elif profile == 'bottlenecked':
                    util = min(100, max(0, utilization_base + rng.normal(15, 5)))
                    power_ratio = 0.35 + rng.uniform(0, 0.15)
                elif profile == 'fragmented':
                    util = max(0, utilization_base * 0.5 + rng.normal(0, 10))
                    power_ratio = 0.4 + rng.uniform(0, 0.2)
                else:
                    util = min(100, max(0, utilization_base + rng.normal(0, 8)))
                    power_ratio = 0.5 + (util / 100) * 0.4 + rng.uniform(-0.05, 0.05)
                
                power_range = gpu_spec['max_power'] - gpu_spec['idle_power']
                power = max(gpu_spec['idle_power'], min(gpu_spec['max_power'], gpu_spec['idle_power'] + power_range * power_ratio))
                mem_ratio = 0.3 + (util / 100) * 0.5 + rng.uniform(-0.1, 0.1)
                mem_used = int(gpu_spec['memory_total'] * min(0.95, max(0.05, mem_ratio)))
                temp = max(25, min(85, int(30 + (power / gpu_spec['max_power']) * 45 + rng.normal(0, 2))))
                tensor_active = max(0, min(100, int(util * (0.85 if 'training' in ng['name'] and util > 50 else 0.3) + rng.normal(0, 5 if 'training' in ng['name'] else 3))))
                
                records.append({
                    'timestamp': ts, 'timestamp_hour': ts_hour, 'hostname': hostname,
                    'cluster': ng['cluster'], 'region': ng['region'], 'nodegroup': ng['name'],
                    'gpu_model': ng['gpu_model'], 'gpu_uuid': gpu_uuid, 'namespace': rng.choice(NAMESPACES),
                    'gpu_utilization_pct': round(util, 1), 'power_usage_watts': round(power, 2),
                    'memory_used_mb': mem_used, 'memory_free_mb': gpu_spec['memory_total'] - mem_used,
                    'gpu_temp_celsius': temp, 'memory_temp_celsius': max(20, temp - 5),
                    'sm_clock_mhz': int(1000 + (util / 100) * 800 + rng.normal(0, 30)),
                    'memory_clock_mhz': int(5000 + rng.normal(0, 100)),
                    'tensor_active_pct': tensor_active, 'gr_engine_active_pct': int(util),
                    'pcie_rx_bytes': int(rng.integers(100000, 1000000) * (1 + util / 100)),
                    'pcie_tx_bytes': int(rng.integers(100000, 1000000) * (1 + util / 100)),
                    'correctable_remapped_rows': 0, 'uncorrectable_remapped_rows': 0,
                    'xid_errors': 0, 'pcie_replay_counter': 0,
                })
    return pd.DataFrame(records)


def generate_synthetic_data(scenario: str = 'balanced', seed: int = 42, days: int = 7, samples_per_hour: int = 60, output_dir: str = 'data/synthetic') -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict]:
    rng = np.random.default_rng(seed)
    scenario_config = get_scenario_config(scenario)
    start_date = datetime(2026, 1, 20, 0, 0, 0)
    timestamps = generate_timestamps(start_date, days, samples_per_hour)
    
    print(f"Generating synthetic data: scenario={scenario}, seed={seed}, days={days}")
    
    nodepool_df = generate_nodepool_state(NODEGROUP_CONFIGS, timestamps, rng, scenario_config)
    kueue_df = generate_kueue_metrics(QUEUE_NODEGROUP_MAP, NAMESPACES, timestamps, rng, scenario_config, nodepool_df)
    dcgm_df = generate_dcgm_metrics(NODEGROUP_CONFIGS, timestamps, rng, scenario_config, kueue_df)
    
    validate_nodepool_data(nodepool_df)
    validate_kueue_data(kueue_df)
    validate_dcgm_data(dcgm_df)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    nodepool_df.to_csv(output_path / 'nodepool_state.csv', index=False)
    kueue_df.to_csv(output_path / 'kueue_metrics.csv', index=False)
    dcgm_df.to_csv(output_path / 'dcgm_metrics.csv', index=False)
    
    manifest = {
        'generated_at': datetime.now().isoformat(), 'scenario': scenario, 'seed': seed,
        'days': days, 'samples_per_hour': samples_per_hour,
        'date_range': {'start': str(timestamps[0]), 'end': str(timestamps[-1])},
        'row_counts': {'nodepool_state': len(nodepool_df), 'kueue_metrics': len(kueue_df), 'dcgm_metrics': len(dcgm_df)},
        'unique_counts': {'nodegroups': nodepool_df['nodegroup'].nunique(), 'queues': kueue_df['queue_name'].nunique(), 'gpus': dcgm_df['gpu_uuid'].nunique()},
        'gpu_models': list(dcgm_df['gpu_model'].unique()),
    }
    
    with open(output_path / 'manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Data saved to {output_dir}/")
    print(f"  nodepool_state.csv: {len(nodepool_df):,} rows")
    print(f"  kueue_metrics.csv: {len(kueue_df):,} rows")
    print(f"  dcgm_metrics.csv: {len(dcgm_df):,} rows")
    
    return kueue_df, dcgm_df, nodepool_df, manifest


def main():
    parser = argparse.ArgumentParser(description='Generate synthetic GPU demand/capacity data')
    parser.add_argument('--scenario', type=str, default='balanced', choices=['balanced', 'demand_exceeds_capacity', 'capacity_fragmentation', 'io_bottleneck'], help='Scenario to generate')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    parser.add_argument('--days', type=int, default=7, help='Number of days of data')
    parser.add_argument('--samples-per-hour', type=int, default=60, help='Samples per hour (60=1/min)')
    parser.add_argument('--output', type=str, default='data/synthetic', help='Output directory')
    args = parser.parse_args()
    
    generate_synthetic_data(scenario=args.scenario, seed=args.seed, days=args.days, samples_per_hour=args.samples_per_hour, output_dir=args.output)


if __name__ == '__main__':
    main()
