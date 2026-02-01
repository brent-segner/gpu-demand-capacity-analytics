# GPU Demand vs Capacity Analytics

## Identifying Imbalances Between Workload Demand and GPU Capacity in GenAI Kubernetes Clusters

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## 🎯 Project Goal

This project provides a **reproducible, open-source analytical framework** for identifying **where, when, and why** queued or unmet workload demand diverges from actual GPU capacity in Kueue-managed Kubernetes clusters.

Using **100% synthetic data** (no production data), it demonstrates how combining:
- **Kueue LocalQueue metrics** (demand signals: pending workloads, admission delays, resource usage)
- **NVIDIA DCGM metrics** (capacity/efficiency signals: utilization, power draw, memory pressure)
- **Cluster telemetry** (nodepool inventory, scheduling metadata)

...can reveal imbalances that traditional "GPU utilization %" monitoring misses.

---

## 📊 The Core Analytical Question

> **Where, when, and why does queued or unmet workload demand diverge from actual GPU capacity or effective utilization at the node pool level?**

This includes:
1. **Demand exceeds capacity**: Queues backing up, long wait times, insufficient GPUs
2. **Capacity exists but is underutilized**: GPUs appear "busy" but aren't productive (I/O bottlenecks, network stalls)
3. **Fragmentation**: Capacity exists but can't be scheduled (resource fragmentation, anti-affinity, preemption)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SYNTHETIC DATA LAYER                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│   │ KUEUE METRICS   │    │  DCGM METRICS   │    │ NODEPOOL STATE  │        │
│   │                 │    │                 │    │                 │        │
│   │ • pending_wklds │    │ • gpu_util %    │    │ • gpu_count     │        │
│   │ • wait_time_sec │    │ • power_watts   │    │ • nodegroup     │        │
│   │ • admitted_wklds│    │ • memory_used   │    │ • labels        │        │
│   │ • evicted_total │    │ • tensor_active │    │ • capacity_gpu  │        │
│   │ • resource_usage│    │ • pcie_traffic  │    │                 │        │
│   └────────┬────────┘    └────────┬────────┘    └────────┬────────┘        │
│            │                      │                      │                 │
│            └──────────────────────┼──────────────────────┘                 │
│                                   │                                        │
│                      ┌────────────▼────────────┐                           │
│                      │   UNIFIED TIME-INDEXED  │                           │
│                      │        MODEL            │                           │
│                      │  (per nodegroup, hour)  │                           │
│                      └────────────┬────────────┘                           │
│                                   │                                        │
└───────────────────────────────────┼────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼────────────────────────────────────────┐
│                                   ▼                                        │
│                      ┌─────────────────────────┐                           │
│                      │   IMBALANCE METRICS     │                           │
│                      │                         │                           │
│                      │ • demand_capacity_ratio │                           │
│                      │ • efficiency_gap        │                           │
│                      │ • queue_pressure_score  │                           │
│                      │ • utilization_rfu_delta │                           │
│                      └────────────┬────────────┘                           │
│                                   │                                        │
│                      ┌────────────▼────────────┐                           │
│                      │    VISUALIZATIONS &     │                           │
│                      │    INTERPRETATION       │                           │
│                      │                         │                           │
│                      │ • Heatmaps by nodegroup │                           │
│                      │ • Time series trends    │                           │
│                      │ • Contributor analysis  │                           │
│                      │ • Action recommendations│                           │
│                      └─────────────────────────┘                           │
│                                                                            │
│                          ANALYSIS LAYER                                    │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
gpu-demand-capacity-analytics/
├── README.md                      # This file
├── LICENSE                        # MIT License
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Project configuration
│
├── data/
│   └── synthetic/                 # Generated synthetic datasets
│       ├── manifest.json          # Generation metadata (seed, scenario, timestamps)
│       ├── kueue_metrics.csv      # Synthetic Kueue LocalQueue metrics
│       ├── dcgm_metrics.csv       # Synthetic NVIDIA DCGM metrics
│       └── nodepool_state.csv     # Synthetic nodepool inventory
│
├── docs/
│   ├── DATA_DICTIONARY.md         # Metric definitions and formulas
│   ├── ASSUMPTIONS.md             # Assumptions and limitations
│   ├── PROMPTS.md                 # LLM prompts used to generate this project
│   └── rfcs/
│       └── RFC_TEMPLATE.md        # Template for proposing changes
│
├── notebooks/
│   └── demand_capacity_analysis.ipynb  # Primary analysis notebook
│
├── src/
│   ├── __init__.py
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── synthetic_generator.py # Main synthetic data generator
│   │   ├── scenarios.py           # Scenario definitions
│   │   └── validators.py          # Data validation checks
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── metrics.py             # Derived metric calculations
│   │   ├── imbalance.py           # Imbalance metric implementations
│   │   └── aggregations.py        # Time-indexed aggregations
│   └── visualization/
│       ├── __init__.py
│       ├── charts.py              # Chart generation functions
│       └── styles.py              # Consistent styling
│
├── tests/
│   ├── __init__.py
│   ├── test_generators.py         # Generator unit tests
│   └── test_metrics.py            # Metric calculation tests
│
├── examples/
│   └── quick_start.py             # Command-line quick start script
│
├── CONTRIBUTING.md                # Contribution guidelines
│
└── .github/
    └── ISSUE_TEMPLATE/
        ├── bug_report.md
        ├── metric_proposal.md
        ├── visualization_request.md
        └── data_schema_change.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip or conda

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/gpu-demand-capacity-analytics.git
cd gpu-demand-capacity-analytics

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Generate Synthetic Data

```bash
# Generate default "balanced" scenario
python -m src.generators.synthetic_generator

# Generate specific scenarios
python -m src.generators.synthetic_generator --scenario demand_exceeds_capacity
python -m src.generators.synthetic_generator --scenario capacity_fragmentation
python -m src.generators.synthetic_generator --scenario balanced

# Custom parameters
python -m src.generators.synthetic_generator \
    --seed 42 \
    --days 7 \
    --gpus 100 \
    --scenario balanced \
    --output data/synthetic/
```

### Run the Analysis Notebook

```bash
jupyter notebook notebooks/demand_capacity_analysis.ipynb
```

### Quick Start (CLI)

```bash
python examples/quick_start.py
```

---

## 📈 Step-by-Step Analysis Logic

The analysis notebook follows this logical flow:

### 1. **Load and Validate Synthetic Data**
- Load Kueue, DCGM, and nodepool datasets
- Validate schema, check for missing values
- Report row counts and date ranges

### 2. **Build Unified Time-Indexed Model**
- Join datasets on `(nodegroup, timestamp_hour)`
- Aggregate metrics to hourly granularity
- Handle label mismatches gracefully

### 3. **Calculate Demand Signals** (from Kueue)
- `total_pending_workloads`: Sum of pending across queues per nodegroup
- `avg_admission_wait_sec`: Average time from submission to admission
- `queue_pressure_score`: Composite of pending + wait time

### 4. **Calculate Capacity Signals** (from DCGM + Nodepool)
- `total_gpu_capacity`: GPU count per nodegroup
- `avg_gpu_utilization`: Mean GPU utilization %
- `avg_power_intensity_factor (PIF)`: Power / Max Power
- `realized_tflops_utilization (RFU)`: Actual computational throughput

### 5. **Compute Imbalance Metrics**
- `demand_capacity_ratio (DCR)`: Pending workloads / Available GPU capacity
- `efficiency_gap`: GPU Utilization % - RFU %
- `composite_imbalance_score`: Weighted combination of demand and efficiency signals

### 6. **Visualize and Interpret**
- Heatmaps: Imbalance by nodegroup over time
- Time series: Trends of DCR, efficiency gap
- Bar charts: Top contributors (queues, namespaces)
- Scatter plots: Utilization vs Power Intensity

### 7. **Recommend Actions**
- Identify specific nodegroups/queues with persistent imbalances
- Suggest capacity adjustments or workload redistribution

---

## 📊 Key Metrics Defined

| Metric | Formula | What It Measures |
|--------|---------|------------------|
| **Demand Capacity Ratio (DCR)** | `pending_workloads / available_gpu_slots` | Ratio of unmet demand to supply |
| **Queue Pressure Score (QPS)** | `0.6 × norm(pending) + 0.4 × norm(wait_time)` | Composite demand urgency |
| **Power Intensity Factor (PIF)** | `current_power / max_gpu_power` | Proxy for actual computational work |
| **Realized TFLOPS Utilization (RFU)** | `achievable_tflops × PIF` | True throughput efficiency |
| **Efficiency Gap** | `gpu_utilization_% - rfu_%` | Hidden productivity loss |
| **Composite Imbalance Score** | `0.5 × DCR + 0.3 × efficiency_gap + 0.2 × QPS` | Overall imbalance indicator |

See [DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) for complete definitions.

---

## 🧪 Synthetic Data Scenarios

The generator supports multiple illustrative scenarios:

### 1. **Balanced** (default)
- Demand roughly matches capacity
- Healthy queue dynamics, moderate utilization
- Expected: Low imbalance scores, small efficiency gaps

### 2. **Demand Exceeds Capacity**
- More workloads submitted than can be scheduled
- Growing queues, long wait times
- Expected: High DCR, elevated queue pressure

### 3. **Capacity Fragmentation**
- GPUs exist but can't be effectively scheduled
- Resource hoarding, anti-affinity constraints simulated
- Expected: Low utilization despite demand, high efficiency gap

### 4. **I/O Bottleneck**
- GPUs report high utilization but low power draw
- Data-starved workloads (slow storage, network)
- Expected: High utilization %, low RFU, large efficiency gap

See [scenarios.py](src/generators/scenarios.py) for implementation details.

---

## ⚠️ Assumptions & Limitations

### What This Project Does
- Demonstrates analytical methodology using synthetic data
- Provides reusable code patterns for metric calculation
- Shows how to combine Kueue + DCGM + nodepool signals

### What This Project Does NOT Do
- Use any real production data
- Provide production-ready monitoring dashboards
- Account for all real-world scheduling complexities

### Key Simplifications

| Aspect | Synthetic Assumption | Real-World Reality |
|--------|---------------------|-------------------|
| **Scrape intervals** | Uniform 1-minute intervals | Variable, may have gaps |
| **Label cardinality** | Fixed set of nodegroups/namespaces | Dynamic, can change |
| **GPU types** | A10G, A100, H100 only | Many more SKUs |
| **Queue-to-GPU mapping** | Explicit via labels | Often requires relabeling |
| **Network effects** | Simulated as power drop | Complex latency patterns |

See [ASSUMPTIONS.md](docs/ASSUMPTIONS.md) for complete details.

---

## 📖 Interpreting Results

### What "Imbalance" Means

An **imbalance** indicates a mismatch between workload demand and effective GPU capacity. This can manifest as:

1. **Supply-side imbalance**: Not enough GPUs for the submitted workloads
   - *Symptom*: High DCR, growing queues, long wait times
   - *Action*: Add capacity, prioritize workloads, or redistribute demand

2. **Efficiency imbalance**: Capacity exists but isn't productively used
   - *Symptom*: High utilization but low RFU (large efficiency gap)
   - *Action*: Investigate I/O bottlenecks, optimize data pipelines, tune batch sizes

3. **Fragmentation imbalance**: Capacity exists but can't be scheduled
   - *Symptom*: Low utilization despite queued demand
   - *Action*: Review pod affinity/anti-affinity, bin-packing, resource requests

### Chart Interpretation Guide

Each visualization in the notebook includes a **"So What"** interpretation explaining:
- What the chart shows
- What patterns to look for
- What actions those patterns suggest

---

## 🤝 Contributing

We welcome contributions! This project is designed for **community feedback and consensus**.

### How to Contribute

1. **Feedback**: Open an issue or discussion
2. **Bug fixes**: Submit a PR with tests
3. **New metrics**: Use the [RFC process](docs/rfcs/RFC_TEMPLATE.md)
4. **Visualizations**: Submit with interpretation guidance

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### RFC Process for Metric Changes

Proposing new imbalance metrics or changing existing ones requires an RFC:

1. Copy `docs/rfcs/RFC_TEMPLATE.md` to `docs/rfcs/RFC-NNN-your-proposal.md`
2. Fill out all sections (Problem, Proposal, Rationale, Alternatives)
3. Open a PR for discussion
4. Achieve rough consensus before merging

---

## 📚 Related Resources

- [Kueue Documentation](https://kueue.sigs.k8s.io/)
- [NVIDIA DCGM Documentation](https://docs.nvidia.com/datacenter/dcgm/)
- [Kubernetes Metrics Server](https://github.com/kubernetes-sigs/metrics-server)

---

## 📄 License

This project is released under the [MIT License](LICENSE).

---

## 🙋 Questions or Feedback?

- **GitHub Issues**: For bugs, feature requests, metric proposals
- **GitHub Discussions**: For questions, ideas, community dialogue
- **RFC Process**: For proposing significant changes

---

## 📝 Citation

If you use this work in research or production:

```bibtex
@software{gpu_demand_capacity_analytics,
  title = {GPU Demand vs Capacity Analytics},
  author = {Community Contributors},
  year = {2026},
  url = {https://github.com/yourusername/gpu-demand-capacity-analytics}
}
```

---

**Built for transparency, reproducibility, and community consensus.**

*Making GPU demand-versus-capacity imbalances visible and actionable.*
