"""
Tests for Synthetic Data Generators
===================================
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.generators.synthetic_generator import (
    generate_timestamps,
    generate_nodepool_state,
    generate_kueue_metrics,
    generate_dcgm_metrics,
    GPU_SPECS,
    NODEGROUP_CONFIGS,
    QUEUE_NODEGROUP_MAP,
    NAMESPACES,
)
from src.generators.scenarios import get_scenario_config, list_scenarios
from src.generators.validators import (
    validate_nodepool_data,
    validate_kueue_data,
    validate_dcgm_data,
    ValidationError,
)


class TestTimestampGeneration:
    def test_generates_correct_count(self):
        start = datetime(2026, 1, 1)
        ts = generate_timestamps(start, days=1, samples_per_hour=60)
        assert len(ts) == 24 * 60
    
    def test_uniform_intervals(self):
        start = datetime(2026, 1, 1)
        ts = generate_timestamps(start, days=1, samples_per_hour=60)
        diffs = ts.to_series().diff().dropna()
        assert (diffs == pd.Timedelta(minutes=1)).all()
    
    def test_starts_at_correct_time(self):
        start = datetime(2026, 1, 15, 8, 0, 0)
        ts = generate_timestamps(start, days=1, samples_per_hour=60)
        assert ts[0] == start


class TestScenarios:
    def test_all_scenarios_exist(self):
        scenarios = list_scenarios()
        assert 'balanced' in scenarios
        assert 'demand_exceeds_capacity' in scenarios
        assert 'capacity_fragmentation' in scenarios
        assert 'io_bottleneck' in scenarios
    
    def test_scenario_config_has_required_keys(self):
        for scenario_name in list_scenarios().keys():
            config = get_scenario_config(scenario_name)
            assert 'demand_capacity_ratio' in config
            assert 'base_wait_seconds' in config
            assert 'workload_profile' in config
    
    def test_invalid_scenario_raises(self):
        with pytest.raises(ValueError):
            get_scenario_config('nonexistent_scenario')


class TestNodepoolGeneration:
    def test_generates_all_nodegroups(self):
        rng = np.random.default_rng(42)
        config = get_scenario_config('balanced')
        ts = generate_timestamps(datetime(2026, 1, 1), days=1, samples_per_hour=1)
        
        df = generate_nodepool_state(NODEGROUP_CONFIGS, ts, rng, config)
        
        nodegroups = df['nodegroup'].unique()
        expected = [ng['name'] for ng in NODEGROUP_CONFIGS]
        assert set(nodegroups) == set(expected)
    
    def test_no_negative_counts(self):
        rng = np.random.default_rng(42)
        config = get_scenario_config('balanced')
        ts = generate_timestamps(datetime(2026, 1, 1), days=1, samples_per_hour=1)
        
        df = generate_nodepool_state(NODEGROUP_CONFIGS, ts, rng, config)
        
        assert (df['capacity_gpu_count'] >= 0).all()
        assert (df['allocatable_gpu_count'] >= 0).all()
    
    def test_allocatable_lte_capacity(self):
        rng = np.random.default_rng(42)
        config = get_scenario_config('balanced')
        ts = generate_timestamps(datetime(2026, 1, 1), days=1, samples_per_hour=1)
        
        df = generate_nodepool_state(NODEGROUP_CONFIGS, ts, rng, config)
        
        assert (df['allocatable_gpu_count'] <= df['capacity_gpu_count']).all()


class TestValidators:
    def test_nodepool_validation_passes_valid_data(self):
        df = pd.DataFrame({
            'timestamp': [datetime(2026, 1, 1)],
            'timestamp_hour': [datetime(2026, 1, 1)],
            'nodegroup': ['test'],
            'cluster': ['cluster1'],
            'region': ['us-west-2'],
            'gpu_model': ['NVIDIA A100'],
            'capacity_gpu_count': [10],
            'allocatable_gpu_count': [9],
        })
        validate_nodepool_data(df)  # Should not raise
    
    def test_nodepool_validation_fails_negative_capacity(self):
        df = pd.DataFrame({
            'timestamp': [datetime(2026, 1, 1)],
            'timestamp_hour': [datetime(2026, 1, 1)],
            'nodegroup': ['test'],
            'cluster': ['cluster1'],
            'region': ['us-west-2'],
            'gpu_model': ['NVIDIA A100'],
            'capacity_gpu_count': [-1],
            'allocatable_gpu_count': [9],
        })
        with pytest.raises(ValidationError):
            validate_nodepool_data(df)
    
    def test_dcgm_validation_fails_invalid_utilization(self):
        df = pd.DataFrame({
            'timestamp': [datetime(2026, 1, 1)],
            'timestamp_hour': [datetime(2026, 1, 1)],
            'hostname': ['host1'],
            'cluster': ['cluster1'],
            'region': ['us-west-2'],
            'nodegroup': ['ng1'],
            'gpu_model': ['NVIDIA A100'],
            'gpu_uuid': ['GPU-123'],
            'gpu_utilization_pct': [150],  # Invalid: > 100
            'power_usage_watts': [300],
            'memory_used_mb': [10000],
            'memory_free_mb': [30000],
            'gpu_temp_celsius': [50],
        })
        with pytest.raises(ValidationError):
            validate_dcgm_data(df)


class TestDeterminism:
    def test_same_seed_same_results(self):
        from src.generators.synthetic_generator import generate_synthetic_data
        
        kueue1, dcgm1, nodepool1, _ = generate_synthetic_data(
            scenario='balanced', seed=42, days=1, samples_per_hour=1
        )
        kueue2, dcgm2, nodepool2, _ = generate_synthetic_data(
            scenario='balanced', seed=42, days=1, samples_per_hour=1
        )
        
        pd.testing.assert_frame_equal(kueue1, kueue2)
        pd.testing.assert_frame_equal(nodepool1, nodepool2)
    
    def test_different_seed_different_results(self):
        from src.generators.synthetic_generator import generate_synthetic_data
        
        kueue1, _, _, _ = generate_synthetic_data(
            scenario='balanced', seed=42, days=1, samples_per_hour=1
        )
        kueue2, _, _, _ = generate_synthetic_data(
            scenario='balanced', seed=99, days=1, samples_per_hour=1
        )
        
        # Values should differ (with very high probability)
        assert not kueue1['pending_workloads'].equals(kueue2['pending_workloads'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
