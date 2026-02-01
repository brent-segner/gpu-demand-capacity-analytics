# Assumptions and Limitations

## Overview

This document explicitly states the assumptions made in this synthetic data analysis project and where **real-world implementations would differ**. Transparency about these limitations is essential for practitioners adapting this methodology to production environments.

---

## Core Assumptions

### 1. Synthetic Data Only

**Assumption**: All data in this repository is synthetically generated. No real production data, customer information, or actual cluster telemetry is used.

**Why this matters**: Synthetic data allows public sharing, reproducibility, and scenario exploration. However, synthetic distributions may not capture real-world anomalies, edge cases, or the true complexity of production systems.

**Real-world wiring**: Production implementations would connect to:
- Prometheus/Thanos for Kueue and DCGM metrics
- Kubernetes API for node and pod state
- Custom relabeling rules for joining disparate metric sources

---

### 2. Label Cardinality and Consistency

**Assumption**: The synthetic data uses a fixed, consistent set of labels:
- 5 nodegroups (e.g., `ml-training-a100`, `ml-inference-a10g`)
- 6 namespaces (e.g., `ml-training`, `research`, `fraud-detection`)
- 3 GPU models (A10G, A100, H100)
- 3 clusters

**Real-world differences**:

| Aspect | Synthetic | Real World |
|--------|-----------|------------|
| Label changes | Static | Nodegroups added/removed dynamically |
| Cardinality | Low (~50 unique GPUs) | High (1000s of GPUs, 100s of namespaces) |
| Label format | Consistent | May vary between clusters, teams |
| Missing labels | None | Common—pods may lack expected labels |

**Wiring implications**:
- Need label mapping/normalization layers
- Handle missing labels gracefully (default values, separate "unknown" category)
- Consider label cardinality explosion in storage/query costs

---

### 3. Queue-to-GPU Mapping

**Assumption**: Kueue LocalQueues map directly to nodegroups via explicit labels. Each queue targets a specific GPU type/nodegroup.

**Synthetic mapping**:
```
Queue: research-h100-queue-large → Nodegroup: ml-training-h100
Queue: inference-a10g-queue → Nodegroup: ml-inference-a10g
```

**Real-world differences**:
- Queues may target multiple nodegroups via ClusterQueue `cohorts`
- ResourceFlavors add another layer of indirection
- Preemption and borrowing allow cross-queue resource sharing
- Queue naming conventions vary between organizations

**Wiring implications**:
- Query Kueue ClusterQueue and ResourceFlavor CRDs for true mappings
- Build a queue→nodegroup resolution function that handles:
  - Multiple flavors per queue
  - Cohort-level sharing
  - Priority-based admission order

---

### 4. Scrape Intervals and Alignment

**Assumption**: All metrics are scraped at uniform 1-minute intervals, perfectly aligned across data sources.

**Synthetic implementation**:
```python
timestamps = pd.date_range(start, end, freq='1min')
```

**Real-world differences**:

| Aspect | Synthetic | Real World |
|--------|-----------|------------|
| Scrape interval | 1 minute, uniform | 15s to 5min, may vary by metric |
| Alignment | Perfect | Timestamps offset by seconds |
| Gaps | None | Scrape failures, pod restarts |
| Staleness | None | Metrics may be stale during outages |

**Wiring implications**:
- Align timestamps to common interval (floor to minute/hour)
- Handle missing values: forward-fill, interpolate, or drop
- Consider scrape jitter when joining datasets
- Add staleness checks (reject metrics older than threshold)

---

### 5. GPU Specifications

**Assumption**: GPU power limits and TFLOPS values are hardcoded based on published specifications.

**Hardcoded values**:
```python
GPU_SPECS = {
    'NVIDIA A10G': {'max_power': 300, 'achievable_tflops': 35},
    'NVIDIA A100-SXM4-40GB': {'max_power': 400, 'achievable_tflops': 102},
    'NVIDIA H100 80GB HBM3': {'max_power': 700, 'achievable_tflops': 646},
}
```

**Real-world differences**:
- Power limits may be software-configurable (power capping)
- Different GPU variants (SXM vs PCIe, 40GB vs 80GB) have different specs
- Achievable TFLOPS vary by workload type (FP16, FP32, INT8, FP8)
- Thermal throttling can reduce actual power draw

**Wiring implications**:
- Query DCGM for actual power limits: `DCGM_FI_DEV_POWER_LIMIT`
- Maintain a GPU specification registry updated for new SKUs
- Consider querying GPU model from DCGM: `DCGM_FI_DEV_NAME`

---

### 6. Power Intensity as Compute Proxy

**Assumption**: Power draw is a reliable proxy for computational work. High power = productive computation; low power with high utilization = stalled/waiting.

**Basis**: Physics dictates that active tensor cores consume more power than idle cores. NVIDIA's own efficiency metrics use similar reasoning.

**Limitations**:
- Some workloads (memory-bound) may show moderate power despite productive work
- Thermal conditions affect power draw
- Multi-instance GPU (MIG) complicates per-instance power attribution
- Power measurement granularity may miss short bursts

**Alternative approaches**:
- Use `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` for tensor core activity
- Use `DCGM_FI_PROF_GR_ENGINE_ACTIVE` for overall compute activity
- Combine multiple signals for higher confidence

---

### 7. Workload Homogeneity

**Assumption**: Each pending workload represents similar resource consumption (e.g., 1 GPU per workload).

**Synthetic implementation**: Workloads uniformly request 1 GPU.

**Real-world differences**:
- Workloads may request 1, 2, 4, or 8 GPUs
- Resource requests vs limits may differ
- Extended resources (GPU memory, NICs) vary
- Job duration varies dramatically (minutes to days)

**Wiring implications**:
- Weight pending workloads by requested GPU count
- Calculate demand in GPU-equivalents, not workload count
- Consider queue depth as `sum(workload_gpu_requests)` not `count(workloads)`

---

### 8. Single-Cluster Simplification

**Assumption**: Analysis focuses on per-cluster views. Cross-cluster federation is not addressed.

**Real-world differences**:
- Organizations may have multiple clusters per region
- Workloads may be routed across clusters
- Capacity may be shared via virtual clusters or federation

**Wiring implications**:
- Add cluster dimension to all aggregations
- Consider cross-cluster load balancing in demand calculations
- Use federated Prometheus or multi-cluster observability platforms

---

## Scenario-Specific Assumptions

### Balanced Scenario
- Demand fluctuates moderately (±20% of capacity)
- No sustained queue backlogs
- Efficiency is generally high (>60% RFU)

### Demand Exceeds Capacity Scenario
- Submission rate exceeds scheduling capacity
- Queues grow linearly over time
- Wait times increase monotonically

### Capacity Fragmentation Scenario
- Total capacity exists but can't be scheduled
- Simulated via reduced "effective capacity" (not actual anti-affinity)
- Does not model pod-level scheduling constraints

### I/O Bottleneck Scenario
- High utilization, low power (large efficiency gap)
- Does not distinguish between storage I/O, network I/O, or CPU bottlenecks
- Power drop is uniform across affected GPUs

---

## What This Project Does NOT Model

### Not Modeled (Simplification)

| Feature | Why Omitted | Real-World Importance |
|---------|-------------|----------------------|
| **Pod scheduling** | Complexity | Bin-packing, affinity, taints |
| **Preemption** | Requires job state tracking | Critical for priority workloads |
| **Autoscaling delays** | Focus on steady-state | Minutes to hours in practice |
| **Network topology** | Complexity | NVLink, InfiniBand, cross-rack |
| **Multi-GPU jobs** | Simplification | Common in distributed training |
| **Job duration** | Simplification | Affects queue dynamics significantly |
| **Cost modeling** | Scope | Critical for FinOps |
| **MIG partitioning** | Complexity | Affects resource granularity |

### Intentionally Out of Scope

- Real-time alerting thresholds
- Integration with specific monitoring platforms (Grafana, DataDog)
- Auto-remediation workflows
- Cost optimization recommendations
- Specific cloud provider APIs

---

## Validation Checklist

When adapting this methodology to production:

### Data Ingestion
- [ ] Verify Prometheus query ranges and step intervals
- [ ] Confirm label consistency across data sources
- [ ] Test join logic with missing/mismatched labels
- [ ] Handle metric staleness appropriately

### Metric Calculation
- [ ] Validate GPU specs against actual hardware
- [ ] Confirm power limit values from DCGM
- [ ] Test normalization ranges with historical data
- [ ] Verify aggregation produces expected results

### Interpretation
- [ ] Calibrate alert thresholds with operator feedback
- [ ] Validate efficiency gap against known bottleneck scenarios
- [ ] Confirm imbalance scores align with operational experience
- [ ] Test false positive rates before production alerts

### Visualization
- [ ] Verify charts render correctly with production cardinality
- [ ] Test query performance at production scale
- [ ] Confirm time zone handling

---

## Feedback Welcome

This assumptions document is a **living artifact**. If you identify:
- Assumptions that don't hold in your environment
- Important limitations we haven't documented
- Better approaches to any of these challenges

Please open an issue or submit an RFC. The goal is honest, transparent methodology—not perfect synthetic data.

---

*Last updated: 2026-01-31*
