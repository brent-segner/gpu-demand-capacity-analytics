# Data Dictionary

## Overview

This document defines all metrics, fields, and derived calculations used in the GPU Demand vs Capacity Analytics project. Every metric includes:
- **Plain English definition**
- **Formula** (where applicable)
- **Units**
- **Data source**
- **Interpretation guidance**

---

## Table of Contents

1. [Naming Conventions](#naming-conventions)
2. [Demand Signals (Kueue)](#demand-signals-kueue)
3. [Capacity Signals (DCGM)](#capacity-signals-dcgm)
4. [Nodepool State](#nodepool-state)
5. [Derived Metrics](#derived-metrics)
6. [Imbalance Metrics](#imbalance-metrics)
7. [Classification Labels](#classification-labels)

---

## Naming Conventions

To ensure clarity and consistency:

| Category | Prefix/Suffix | Example |
|----------|---------------|---------|
| Demand signals | `demand_`, `queue_`, `pending_` | `demand_pending_workloads` |
| Capacity signals | `capacity_`, `gpu_` | `capacity_gpu_count` |
| Efficiency signals | `efficiency_`, `rfu_`, `pif_` | `efficiency_gap` |
| Imbalance metrics | `imbalance_`, `ratio_` | `imbalance_dcr` |
| Normalized (0-1) | `_norm` suffix | `demand_pending_norm` |
| Percentage (0-100) | `_pct` suffix | `gpu_util_pct` |

---

## Demand Signals (Kueue)

These metrics come from Kubernetes Kueue LocalQueue Prometheus metrics and represent **workload demand**.

### KUEUE_LOCAL_QUEUE_PENDING_WORKLOADS

| Attribute | Value |
|-----------|-------|
| **Definition** | Number of workloads submitted to a queue but not yet admitted (scheduled) |
| **Formula** | Direct from Kueue metric |
| **Units** | Count (integer) |
| **Source** | `kueue_local_queue_pending_workloads` Prometheus metric |
| **Range** | 0 to unbounded |
| **Interpretation** | Higher values indicate demand exceeding current scheduling capacity. Sustained high values suggest capacity shortage or scheduling constraints. |

### KUEUE_LOCAL_QUEUE_ADMISSION_WAIT_TIME_SECONDS

| Attribute | Value |
|-----------|-------|
| **Definition** | Time (seconds) from workload submission to admission |
| **Formula** | Direct from Kueue metric (histogram or summary) |
| **Units** | Seconds |
| **Source** | `kueue_local_queue_admission_wait_time_seconds` |
| **Range** | 0 to unbounded |
| **Interpretation** | Long wait times indicate scheduling delays. Combined with pending workloads, helps distinguish between transient spikes and sustained bottlenecks. |

### KUEUE_LOCAL_QUEUE_ADMITTED_ACTIVE_WORKLOADS

| Attribute | Value |
|-----------|-------|
| **Definition** | Number of workloads currently running (admitted and active) |
| **Formula** | Direct from Kueue metric |
| **Units** | Count (integer) |
| **Source** | `kueue_local_queue_admitted_active_workloads` |
| **Range** | 0 to queue limit |
| **Interpretation** | Shows current utilization of queue quota. Compare to pending to understand throughput. |

### KUEUE_LOCAL_QUEUE_ADMITTED_WORKLOADS_TOTAL

| Attribute | Value |
|-----------|-------|
| **Definition** | Cumulative count of all workloads admitted since queue creation |
| **Formula** | Direct from Kueue metric (counter) |
| **Units** | Count (integer, monotonic) |
| **Source** | `kueue_local_queue_admitted_workloads_total` |
| **Range** | 0 to unbounded |
| **Interpretation** | Useful for calculating admission rate (delta over time). |

### KUEUE_LOCAL_QUEUE_EVICTED_WORKLOADS_TOTAL

| Attribute | Value |
|-----------|-------|
| **Definition** | Cumulative count of workloads evicted (preempted) from the queue |
| **Formula** | Direct from Kueue metric (counter) |
| **Units** | Count (integer, monotonic) |
| **Source** | `kueue_local_queue_evicted_workloads_total` |
| **Range** | 0 to unbounded |
| **Interpretation** | High eviction rates indicate resource contention or priority inversions. |

### KUEUE_LOCAL_QUEUE_RESOURCE_USAGE

| Attribute | Value |
|-----------|-------|
| **Definition** | Current resource usage by admitted workloads (e.g., GPU count) |
| **Formula** | Direct from Kueue metric |
| **Units** | Resource-specific (e.g., GPU count) |
| **Source** | `kueue_local_queue_resource_usage` |
| **Range** | 0 to quota limit |
| **Interpretation** | Shows actual resource consumption. Compare to quota and capacity. |

### KUEUE_LOCAL_QUEUE_RESOURCE_RESERVATION

| Attribute | Value |
|-----------|-------|
| **Definition** | Resources reserved (but not necessarily used) by workloads |
| **Formula** | Direct from Kueue metric |
| **Units** | Resource-specific |
| **Source** | `kueue_local_queue_resource_reservation` |
| **Range** | 0 to quota limit |
| **Interpretation** | Reservation > Usage indicates over-provisioned requests or pending starts. |

---

## Capacity Signals (DCGM)

These metrics come from NVIDIA Data Center GPU Manager and represent **GPU capacity and efficiency**.

### DCGM_FI_DEV_GPU_UTIL

| Attribute | Value |
|-----------|-------|
| **Definition** | Percentage of time the GPU had one or more kernels executing |
| **Formula** | Direct from DCGM |
| **Units** | Percentage (0-100) |
| **Source** | `DCGM_FI_DEV_GPU_UTIL` field |
| **Range** | 0 to 100 |
| **Interpretation** | Traditional utilization metric. **Caution**: High utilization does NOT guarantee productive work—GPU may be stalled waiting for data. |

### DCGM_FI_DEV_POWER_USAGE

| Attribute | Value |
|-----------|-------|
| **Definition** | Current power consumption of the GPU |
| **Formula** | Direct from DCGM |
| **Units** | Watts |
| **Source** | `DCGM_FI_DEV_POWER_USAGE` field |
| **Range** | Idle power (~50W) to TDP (varies by GPU) |
| **Interpretation** | Proxy for actual computational work. Physics dictates that intensive compute draws more power than idle or stalled kernels. |

### DCGM_FI_DEV_FB_USED / DCGM_FI_DEV_FB_FREE

| Attribute | Value |
|-----------|-------|
| **Definition** | GPU framebuffer (HBM/GDDR) memory used/free |
| **Formula** | Direct from DCGM |
| **Units** | Megabytes (MB) |
| **Source** | `DCGM_FI_DEV_FB_USED`, `DCGM_FI_DEV_FB_FREE` |
| **Range** | 0 to GPU memory capacity |
| **Interpretation** | Memory pressure indicator. Near-full memory may cause OOM errors or memory-bound performance. |

### DCGM_FI_DEV_GPU_TEMP

| Attribute | Value |
|-----------|-------|
| **Definition** | GPU core temperature |
| **Formula** | Direct from DCGM |
| **Units** | Degrees Celsius |
| **Source** | `DCGM_FI_DEV_GPU_TEMP` |
| **Range** | ~25°C (idle) to ~85°C (thermal limit) |
| **Interpretation** | Correlated with power draw. Sustained high temps may indicate thermal throttling. |

### DCGM_FI_PROF_PIPE_TENSOR_ACTIVE

| Attribute | Value |
|-----------|-------|
| **Definition** | Percentage of cycles the tensor cores were active |
| **Formula** | Direct from DCGM profiling metrics |
| **Units** | Percentage (0-100) |
| **Source** | `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` |
| **Range** | 0 to 100 |
| **Interpretation** | For ML workloads, high tensor activity indicates efficient use of specialized hardware. Low tensor activity during "training" suggests non-matmul bottlenecks. |

### DCGM_FI_PROF_PCIE_RX_BYTES / DCGM_FI_PROF_PCIE_TX_BYTES

| Attribute | Value |
|-----------|-------|
| **Definition** | PCIe data transfer rates (receive/transmit) |
| **Formula** | Direct from DCGM profiling metrics |
| **Units** | Bytes per second |
| **Source** | `DCGM_FI_PROF_PCIE_RX_BYTES`, `DCGM_FI_PROF_PCIE_TX_BYTES` |
| **Range** | 0 to PCIe bandwidth limit |
| **Interpretation** | High sustained PCIe traffic may indicate data-bound workloads. Unusual patterns may signal data pipeline issues. |

---

## Nodepool State

These metrics describe the **inventory and configuration** of GPU nodepools.

### capacity_gpu_count

| Attribute | Value |
|-----------|-------|
| **Definition** | Total number of GPUs available in a nodepool/nodegroup |
| **Formula** | Sum of `nvidia.com/gpu` capacity across nodes in nodegroup |
| **Units** | Count (integer) |
| **Source** | Kubernetes node `Capacity` field |
| **Range** | 0 to cluster limit |
| **Interpretation** | Denominator for capacity ratios. Changes indicate scaling events. |

### allocatable_gpu_count

| Attribute | Value |
|-----------|-------|
| **Definition** | GPUs available for scheduling (capacity minus system reservations) |
| **Formula** | Sum of `nvidia.com/gpu` allocatable across nodes |
| **Units** | Count (integer) |
| **Source** | Kubernetes node `Allocatable` field |
| **Range** | 0 to capacity_gpu_count |
| **Interpretation** | True schedulable capacity. May differ from capacity due to daemonsets or system reservations. |

### nodegroup

| Attribute | Value |
|-----------|-------|
| **Definition** | Logical grouping of nodes with similar characteristics |
| **Formula** | Label-based (e.g., `eks.amazonaws.com/nodegroup`) |
| **Units** | String identifier |
| **Source** | Node labels |
| **Interpretation** | Primary aggregation dimension. Corresponds to autoscaling groups or instance pools. |

---

## Derived Metrics

Metrics calculated from raw signals to provide normalized, comparable values.

### power_intensity_factor (PIF)

| Attribute | Value |
|-----------|-------|
| **Definition** | Ratio of current power draw to maximum GPU power |
| **Formula** | `DCGM_FI_DEV_POWER_USAGE / max_power_for_gpu_model` |
| **Units** | Ratio (0.0 to 1.0) |
| **Source** | Calculated |
| **Range** | 0.0 (idle) to 1.0 (max power) |
| **Interpretation** | Proxy for actual computational intensity. High PIF = actually computing. Low PIF with high utilization = stalled/waiting. |

**GPU Max Power Reference:**

| GPU Model | Max Power (TDP) |
|-----------|-----------------|
| NVIDIA A10G | 300W |
| NVIDIA A100-SXM4-40GB | 400W |
| NVIDIA H100 80GB HBM3 | 700W |

### realized_tflops (RT)

| Attribute | Value |
|-----------|-------|
| **Definition** | Estimated actual mathematical throughput |
| **Formula** | `achievable_tflops_for_gpu_model × PIF` |
| **Units** | TFLOPS (FP16) |
| **Source** | Calculated |
| **Interpretation** | Actual computational work being performed. Compare to achievable TFLOPS to understand efficiency. |

**GPU Achievable TFLOPS Reference (FP16):**

| GPU Model | Theoretical | Achievable |
|-----------|-------------|------------|
| NVIDIA A10G | 125 | 35 |
| NVIDIA A100-SXM4-40GB | 312 | 102 |
| NVIDIA H100 80GB HBM3 | 1,979 | 646 |

### realized_tflops_utilization (RFU)

| Attribute | Value |
|-----------|-------|
| **Definition** | Percentage of achievable computational capacity being used |
| **Formula** | `(realized_tflops / achievable_tflops) × 100` |
| **Units** | Percentage (0-100) |
| **Source** | Calculated |
| **Interpretation** | True efficiency metric. RFU < GPU_UTIL indicates hidden inefficiency. |

### efficiency_gap

| Attribute | Value |
|-----------|-------|
| **Definition** | Difference between reported utilization and realized efficiency |
| **Formula** | `DCGM_FI_DEV_GPU_UTIL - RFU` |
| **Units** | Percentage points |
| **Source** | Calculated |
| **Range** | Can be negative (rare) to ~80 (severe bottleneck) |
| **Interpretation** | Quantifies "hidden" inefficiency. Large gaps indicate data starvation, I/O bottlenecks, or memory-bound workloads. |

### memory_pressure_pct

| Attribute | Value |
|-----------|-------|
| **Definition** | Percentage of GPU memory currently used |
| **Formula** | `DCGM_FI_DEV_FB_USED / (FB_USED + FB_FREE) × 100` |
| **Units** | Percentage (0-100) |
| **Source** | Calculated |
| **Range** | 0 to 100 |
| **Interpretation** | >90% suggests memory pressure risk. May correlate with OOM events or forced batch size reductions. |

---

## Imbalance Metrics

The core metrics that quantify demand-versus-capacity mismatch.

### demand_capacity_ratio (DCR)

| Attribute | Value |
|-----------|-------|
| **Definition** | Ratio of pending workloads to available GPU capacity |
| **Formula** | `total_pending_workloads / (allocatable_gpu_count - active_gpu_usage)` |
| **Alternative Formula** | `total_pending_workloads / allocatable_gpu_count` (simpler) |
| **Units** | Ratio (0.0 to unbounded) |
| **Source** | Calculated |
| **Interpretation** | |
| | DCR < 0.5: Healthy, capacity exceeds demand |
| | DCR 0.5-1.0: Moderate pressure, queues may form |
| | DCR > 1.0: Demand exceeds capacity, expect growing queues |
| | DCR > 2.0: Severe shortage, significant delays |

**Sensitivity**: Very sensitive to pending workload count. Transient spikes may cause false alarms.

**Failure modes**: Does not account for workload size (a pending 8-GPU job ≠ 8 pending 1-GPU jobs).

**Suggested action**: If DCR > 1.0 persists, investigate capacity scaling or demand redistribution.

### queue_pressure_score (QPS)

| Attribute | Value |
|-----------|-------|
| **Definition** | Composite demand urgency score combining pending count and wait time |
| **Formula** | `0.6 × normalize(pending_workloads) + 0.4 × normalize(admission_wait_time)` |
| **Units** | Score (0.0 to 1.0, normalized) |
| **Source** | Calculated |
| **Interpretation** | |
| | QPS < 0.3: Low pressure, healthy queue dynamics |
| | QPS 0.3-0.6: Moderate pressure, monitor for trends |
| | QPS > 0.6: High pressure, likely capacity constrained |
| | QPS > 0.8: Critical, immediate attention needed |

**Sensitivity**: Balanced between count and time. Weights can be adjusted.

**Failure modes**: Normalization depends on historical ranges—new extremes may skew scores.

### composite_imbalance_score (CIS)

| Attribute | Value |
|-----------|-------|
| **Definition** | Overall imbalance indicator combining demand and efficiency signals |
| **Formula** | `0.5 × normalize(DCR) + 0.3 × normalize(efficiency_gap) + 0.2 × QPS` |
| **Units** | Score (0.0 to 1.0, normalized) |
| **Source** | Calculated |
| **Interpretation** | |
| | CIS < 0.3: Well-balanced, efficient operation |
| | CIS 0.3-0.5: Minor imbalances, investigate specific components |
| | CIS > 0.5: Significant imbalance, prioritize remediation |
| | CIS > 0.7: Severe imbalance, immediate action recommended |

**Recommended default metric** for dashboard alerts and trend analysis.

**Sensitivity**: Weighted toward demand (DCR). Adjust weights for different operational priorities.

**Failure modes**: Composite score can mask which component is driving the imbalance—always decompose when investigating.

---

## Classification Labels

Categorical labels assigned to observations for analysis and visualization.

### efficiency_class

| Value | Criteria | Interpretation |
|-------|----------|----------------|
| **Efficient** | GPU_UTIL > 70% AND PIF > 0.75 | Workload is both busy and productive |
| **Bottlenecked** | GPU_UTIL > 70% AND PIF < 0.60 | GPU is busy but stalled—likely I/O bound |
| **Moderate** | GPU_UTIL 40-70% AND PIF > 0.50 | Partial utilization with reasonable efficiency |
| **Inefficient** | GPU_UTIL > 10% AND not above categories | Active but poorly utilized |
| **Idle** | GPU_UTIL < 10% | Minimal activity |

### imbalance_severity

| Value | Criteria | Interpretation |
|-------|----------|----------------|
| **Critical** | CIS > 0.7 OR DCR > 2.0 | Immediate attention required |
| **Warning** | CIS > 0.5 OR DCR > 1.0 | Trending toward problems |
| **Moderate** | CIS > 0.3 | Minor imbalances present |
| **Healthy** | CIS ≤ 0.3 | Operating within normal bounds |

---

## Aggregation Conventions

### Time Aggregation

| Granularity | Method | Use Case |
|-------------|--------|----------|
| **Per-minute** | Raw scrape values | Detailed investigation |
| **Hourly** | Mean for gauges, max for counters | Primary analysis |
| **Daily** | Mean of hourly values | Trend analysis |

### Spatial Aggregation

| Level | Dimensions | Use Case |
|-------|------------|----------|
| **Per-GPU** | UUID, hostname | Individual GPU analysis |
| **Per-Nodegroup** | nodegroup label | Capacity planning |
| **Per-Namespace** | namespace | Workload attribution |
| **Per-Cluster** | cluster_name | Cross-cluster comparison |
| **Fleet-wide** | None | Executive summary |

---

## Normalization Methods

For composite scores, metrics are normalized to 0-1 range:

### Min-Max Normalization (default)
```
normalized = (value - min) / (max - min)
```
- Uses rolling window min/max (e.g., past 7 days)
- Sensitive to outliers

### Percentile Normalization (alternative)
```
normalized = percentile_rank(value) / 100
```
- Robust to outliers
- Requires historical data

### Z-Score Normalization (for alerts)
```
z_score = (value - mean) / std_dev
```
- Good for anomaly detection
- Assumes normal distribution

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-31 | Initial version | Project Team |

---

*This data dictionary is a living document. Propose changes via the [RFC process](rfcs/RFC_TEMPLATE.md).*
