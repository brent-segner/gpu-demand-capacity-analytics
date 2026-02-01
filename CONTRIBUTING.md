# Contributing to GPU Demand vs Capacity Analytics

Thank you for your interest in contributing! This project is designed for **community feedback and consensus**. We welcome contributions of all kinds.

---

## Table of Contents

1. [Ways to Contribute](#ways-to-contribute)
2. [Getting Started](#getting-started)
3. [Contribution Types](#contribution-types)
4. [RFC Process](#rfc-process)
5. [Code Style](#code-style)
6. [Pull Request Process](#pull-request-process)
7. [Issue Guidelines](#issue-guidelines)
8. [Community Standards](#community-standards)

---

## Ways to Contribute

### 📝 Feedback & Discussion
- Open issues for questions or suggestions
- Participate in RFC discussions
- Share real-world experiences (anonymized)

### 🐛 Bug Reports
- Report issues with data generation
- Identify calculation errors
- Flag documentation inaccuracies

### 💡 Enhancements
- Propose new metrics (via RFC)
- Suggest visualization improvements
- Add new scenarios

### 📊 Analysis Extensions
- Additional notebook sections
- Alternative aggregation methods
- Cross-cluster analysis

### 📚 Documentation
- Clarify existing docs
- Add examples
- Translate documentation

---

## Getting Started

### Prerequisites

```bash
python >= 3.8
git
```

### Setup

```bash
# Fork the repository on GitHub

# Clone your fork
git clone https://github.com/YOUR-USERNAME/gpu-demand-capacity-analytics.git
cd gpu-demand-capacity-analytics

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL/gpu-demand-capacity-analytics.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests to verify setup
pytest tests/
```

### Verify Installation

```bash
# Generate synthetic data
python -m src.generators.synthetic_generator --scenario balanced

# Run quick analysis
python examples/quick_start.py

# Launch notebook
jupyter notebook notebooks/demand_capacity_analysis.ipynb
```

---

## Contribution Types

### 1. Bug Fixes

**Process:**
1. Open an issue describing the bug
2. Fork and create a branch: `fix/brief-description`
3. Write a failing test (if applicable)
4. Fix the bug
5. Ensure all tests pass
6. Submit PR referencing the issue

**Example commit message:**
```
fix: correct PIF calculation for H100 GPUs

- Fixed max power value from 500W to 700W
- Updated GPU_SPECS dictionary
- Added regression test

Fixes #42
```

### 2. Documentation Improvements

**Process:**
1. Open an issue (optional for small fixes)
2. Fork and create a branch: `docs/brief-description`
3. Make changes
4. Verify rendering (markdown preview)
5. Submit PR

**No RFC needed for:**
- Typo fixes
- Clarifications
- Example additions
- Formatting improvements

### 3. New Scenarios

**Process:**
1. Open an issue describing the scenario
2. Discuss feasibility and value
3. Fork and create a branch: `feature/scenario-name`
4. Implement in `src/generators/scenarios.py`
5. Add tests
6. Update documentation
7. Submit PR

**No RFC needed** for scenarios that use existing metrics.

### 4. New Metrics

**Process:**
1. **Required: Submit RFC** (see [RFC Process](#rfc-process))
2. Wait for community discussion (2-4 weeks)
3. After RFC acceptance, implement
4. Submit PR referencing RFC

**RFC required for:**
- New imbalance metrics
- Changes to existing metric formulas
- New classification schemes
- Changes to normalization methods

### 5. Visualization Improvements

**Process:**
1. Open an issue with mockup/description
2. Fork and create a branch: `feature/viz-description`
3. Implement in `src/visualization/`
4. Add interpretation guidance
5. Update notebook
6. Submit PR

**No RFC needed** for visual style changes. **RFC recommended** for new chart types that change how data is interpreted.

---

## RFC Process

### When to Use an RFC

RFCs are required for changes that:
- Modify how imbalance is calculated
- Add or remove metrics from the data dictionary
- Change the analytical methodology
- Affect interpretation of results

### How to Submit an RFC

1. **Copy the template:**
   ```bash
   cp docs/rfcs/RFC_TEMPLATE.md docs/rfcs/RFC-NNN-your-proposal.md
   ```

2. **Fill out all sections** (see template for guidance)

3. **Open a Pull Request:**
   - Title: `RFC: [Your Title]`
   - Add label: `rfc`

4. **Engage with feedback:**
   - Respond to comments
   - Update RFC as needed
   - Seek rough consensus

5. **Merge when approved:**
   - At least 2 maintainer approvals
   - No unresolved blocking concerns
   - 2-week minimum discussion period

### RFC Lifecycle

```
Draft → Under Review → Accepted/Rejected
                    ↘ Superseded (by newer RFC)
```

---

## Code Style

### Python

```python
# Follow PEP 8
# Use type hints
# Include docstrings

def calculate_demand_capacity_ratio(
    pending_workloads: int,
    available_capacity: int
) -> float:
    """
    Calculate the demand-to-capacity ratio.
    
    Args:
        pending_workloads: Number of workloads waiting for resources
        available_capacity: Number of GPUs available for scheduling
        
    Returns:
        Ratio of pending workloads to available capacity.
        Returns inf if available_capacity is 0.
        
    Example:
        >>> calculate_demand_capacity_ratio(10, 5)
        2.0
    """
    if available_capacity == 0:
        return float('inf')
    return pending_workloads / available_capacity
```

### Documentation

- Use ATX-style headers (`#`, `##`, `###`)
- Include code examples where helpful
- Explain the "why", not just the "what"
- Update DATA_DICTIONARY.md for new metrics

### Notebooks

- Clear, descriptive markdown cells
- Every chart has:
  - Title
  - Axis labels with units
  - "So What" interpretation (2-3 sentences)
- Minimal code per cell (prefer helper functions)
- Include "Sanity Checks" section

---

## Pull Request Process

### Before Submitting

- [ ] Tests pass locally: `pytest tests/`
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] DATA_DICTIONARY.md updated (if new metrics)
- [ ] ASSUMPTIONS.md updated (if new assumptions)
- [ ] Commits are atomic and well-described

### PR Template

```markdown
## Summary
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature (non-breaking)
- [ ] Breaking change
- [ ] Documentation update
- [ ] RFC implementation

## Related Issues
Fixes #NNN
Implements RFC-NNN

## Testing
- [ ] Added new tests
- [ ] All tests pass
- [ ] Tested manually with notebook

## Checklist
- [ ] Code follows project style
- [ ] Self-reviewed changes
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

### Review Process

1. Maintainer assigned within 1 week
2. Review comments addressed
3. At least 1 approval required
4. CI checks pass
5. Squash merge preferred

---

## Issue Guidelines

### Labels

| Label | Description |
|-------|-------------|
| `bug` | Something isn't working |
| `enhancement` | New feature or request |
| `documentation` | Documentation improvements |
| `rfc` | Request for Comments |
| `good-first-issue` | Good for newcomers |
| `help-wanted` | Extra attention needed |
| `question` | Further information requested |
| `metric-proposal` | Proposing new metric |
| `visualization` | Chart/graph related |
| `data-schema` | Changes to data structure |

### Issue Templates

Use the appropriate template from `.github/ISSUE_TEMPLATE/`:

- **Bug Report**: For bugs and errors
- **Metric Proposal**: For new metrics (leads to RFC)
- **Visualization Request**: For new charts
- **Data Schema Change**: For structural changes

### Good Issue Example

```markdown
## Bug Report

### Description
The PIF calculation produces values > 1.0 for some H100 observations.

### Steps to Reproduce
1. Generate data with `--scenario io_bottleneck`
2. Load dcgm_metrics.csv
3. Observe PIF values in notebook cell 5

### Expected Behavior
PIF should be clamped to [0.0, 1.0]

### Actual Behavior
Some values are 1.02-1.05

### Environment
- Python 3.10
- pandas 2.0.0
- macOS 14.0

### Additional Context
May be related to power measurement noise not being filtered.
```

---

## Community Standards

### Code of Conduct

- Be respectful and inclusive
- Focus on the work, not the person
- Assume good intentions
- Welcome newcomers
- Credit contributions

### Decision Making

- Rough consensus preferred over voting
- Maintainers have final say on technical decisions
- RFCs require 2-week minimum discussion
- Silence is not consent—actively seek feedback

### Communication

- GitHub Issues: Bug reports, feature requests
- GitHub Discussions: Questions, ideas, broader topics
- Pull Requests: Code review and technical discussion
- RFCs: Significant methodology changes

---

## Recognition

Contributors are recognized in:
- README.md Contributors section
- Release notes
- Commit history

---

## Questions?

- Open a [Discussion](https://github.com/REPO/discussions)
- Check existing [Issues](https://github.com/REPO/issues)
- Review closed [RFCs](https://github.com/REPO/pulls?q=is%3Apr+label%3Arfc)

---

**Thank you for contributing to making GPU efficiency analytics more transparent and actionable!**
