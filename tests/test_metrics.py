"""
Tests for Metric Calculations
=============================
"""

import pytest
import pandas as pd
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.metrics import (
    calculate_power_intensity_factor,
    calculate_realized_tflops,
    calculate_rfu,
    calculate_efficiency_gap,
    calculate_memory_pressure,
    classify_efficiency,
    add_efficiency_metrics,
    normalize_series,
    GPU_SPECS,
)
from src.analysis.imbalance import (
    calculate_demand_capacity_ratio,
    calculate_queue_pressure_score,
    calculate_composite_imbalance_score,
    classify_imbalance_severity,
)


class TestPowerIntensityFactor:
    def test_pif_at_max_power(self):
        df = pd.DataFrame({
            'power_usage_watts': [400],
            'gpu_model': ['NVIDIA A100-SXM4-40GB'],
        })
        pif = calculate_power_intensity_factor(df)
        assert pif.iloc[0] == pytest.approx(1.0)
    
    def test_pif_at_half_power(self):
        df = pd.DataFrame({
            'power_usage_watts': [200],
            'gpu_model': ['NVIDIA A100-SXM4-40GB'],
        })
        pif = calculate_power_intensity_factor(df)
        assert pif.iloc[0] == pytest.approx(0.5)
    
    def test_pif_clamped_to_one(self):
        df = pd.DataFrame({
            'power_usage_watts': [500],  # Over max
            'gpu_model': ['NVIDIA A100-SXM4-40GB'],
        })
        pif = calculate_power_intensity_factor(df)
        assert pif.iloc[0] == 1.0
    
    def test_pif_non_negative(self):
        df = pd.DataFrame({
            'power_usage_watts': [0],
            'gpu_model': ['NVIDIA A100-SXM4-40GB'],
        })
        pif = calculate_power_intensity_factor(df)
        assert pif.iloc[0] >= 0


class TestRealizedTflops:
    def test_rt_at_full_pif(self):
        df = pd.DataFrame({'gpu_model': ['NVIDIA A100-SXM4-40GB']})
        pif = pd.Series([1.0])
        rt = calculate_realized_tflops(df, pif)
        assert rt.iloc[0] == GPU_SPECS['NVIDIA A100-SXM4-40GB']['achievable_tflops']
    
    def test_rt_at_half_pif(self):
        df = pd.DataFrame({'gpu_model': ['NVIDIA A100-SXM4-40GB']})
        pif = pd.Series([0.5])
        rt = calculate_realized_tflops(df, pif)
        expected = GPU_SPECS['NVIDIA A100-SXM4-40GB']['achievable_tflops'] * 0.5
        assert rt.iloc[0] == pytest.approx(expected)


class TestRFU:
    def test_rfu_at_full_efficiency(self):
        df = pd.DataFrame({'gpu_model': ['NVIDIA A100-SXM4-40GB']})
        achievable = GPU_SPECS['NVIDIA A100-SXM4-40GB']['achievable_tflops']
        realized = pd.Series([achievable])
        rfu = calculate_rfu(df, realized)
        assert rfu.iloc[0] == pytest.approx(100.0)
    
    def test_rfu_at_half_efficiency(self):
        df = pd.DataFrame({'gpu_model': ['NVIDIA A100-SXM4-40GB']})
        achievable = GPU_SPECS['NVIDIA A100-SXM4-40GB']['achievable_tflops']
        realized = pd.Series([achievable * 0.5])
        rfu = calculate_rfu(df, realized)
        assert rfu.iloc[0] == pytest.approx(50.0)


class TestEfficiencyGap:
    def test_positive_gap(self):
        util = pd.Series([80])
        rfu = pd.Series([50])
        gap = calculate_efficiency_gap(util, rfu)
        assert gap.iloc[0] == 30
    
    def test_zero_gap(self):
        util = pd.Series([70])
        rfu = pd.Series([70])
        gap = calculate_efficiency_gap(util, rfu)
        assert gap.iloc[0] == 0
    
    def test_negative_gap_possible(self):
        # Theoretically possible if RFU > util (rare)
        util = pd.Series([50])
        rfu = pd.Series([60])
        gap = calculate_efficiency_gap(util, rfu)
        assert gap.iloc[0] == -10


class TestEfficiencyClassification:
    def test_efficient_classification(self):
        util = pd.Series([85])
        pif = pd.Series([0.80])
        cls = classify_efficiency(util, pif)
        assert cls.iloc[0] == 'Efficient'
    
    def test_bottlenecked_classification(self):
        util = pd.Series([90])
        pif = pd.Series([0.40])
        cls = classify_efficiency(util, pif)
        assert cls.iloc[0] == 'Bottlenecked'
    
    def test_idle_classification(self):
        util = pd.Series([5])
        pif = pd.Series([0.10])
        cls = classify_efficiency(util, pif)
        assert cls.iloc[0] == 'Idle'
    
    def test_moderate_classification(self):
        util = pd.Series([55])
        pif = pd.Series([0.60])
        cls = classify_efficiency(util, pif)
        assert cls.iloc[0] == 'Moderate'


class TestDemandCapacityRatio:
    def test_dcr_equal_demand_capacity(self):
        pending = pd.Series([10])
        capacity = pd.Series([10])
        dcr = calculate_demand_capacity_ratio(pending, capacity)
        assert dcr.iloc[0] == pytest.approx(1.0, rel=0.01)
    
    def test_dcr_high_demand(self):
        pending = pd.Series([20])
        capacity = pd.Series([10])
        dcr = calculate_demand_capacity_ratio(pending, capacity)
        assert dcr.iloc[0] == pytest.approx(2.0, rel=0.01)
    
    def test_dcr_zero_demand(self):
        pending = pd.Series([0])
        capacity = pd.Series([10])
        dcr = calculate_demand_capacity_ratio(pending, capacity)
        assert dcr.iloc[0] == pytest.approx(0.0, rel=0.01)


class TestQueuePressureScore:
    def test_qps_normalized(self):
        pending = pd.Series([10, 20, 30])
        wait = pd.Series([60, 120, 180])
        qps = calculate_queue_pressure_score(pending, wait)
        assert (qps >= 0).all()
        assert (qps <= 1).all()
    
    def test_qps_max_at_max_values(self):
        pending = pd.Series([0, 50, 100])
        wait = pd.Series([0, 150, 300])
        qps = calculate_queue_pressure_score(pending, wait)
        assert qps.iloc[2] == pytest.approx(1.0)


class TestImbalanceSeverity:
    def test_critical_high_cis(self):
        cis = pd.Series([0.8])
        dcr = pd.Series([0.5])
        severity = classify_imbalance_severity(cis, dcr)
        assert severity.iloc[0] == 'Critical'
    
    def test_critical_high_dcr(self):
        cis = pd.Series([0.3])
        dcr = pd.Series([2.5])
        severity = classify_imbalance_severity(cis, dcr)
        assert severity.iloc[0] == 'Critical'
    
    def test_healthy_low_values(self):
        cis = pd.Series([0.2])
        dcr = pd.Series([0.3])
        severity = classify_imbalance_severity(cis, dcr)
        assert severity.iloc[0] == 'Healthy'


class TestNormalization:
    def test_minmax_normalization(self):
        s = pd.Series([0, 50, 100])
        norm = normalize_series(s, method='minmax')
        assert norm.iloc[0] == 0.0
        assert norm.iloc[1] == 0.5
        assert norm.iloc[2] == 1.0
    
    def test_normalization_handles_constant(self):
        s = pd.Series([50, 50, 50])
        norm = normalize_series(s, method='minmax')
        assert (norm == 0).all()  # All same value normalizes to 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
