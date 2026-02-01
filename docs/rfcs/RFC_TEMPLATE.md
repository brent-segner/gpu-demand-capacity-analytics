# RFC Template: [Short Title]

**RFC Number**: RFC-NNN  
**Title**: [Descriptive title for this proposal]  
**Author(s)**: [Your name/handle]  
**Status**: Draft | Under Review | Accepted | Rejected | Superseded  
**Created**: YYYY-MM-DD  
**Last Updated**: YYYY-MM-DD  

---

## Summary

*One paragraph summary of the proposal. What are you proposing and why?*

---

## Problem Statement

### Current Behavior
*Describe the current state. What metric, calculation, or visualization exists today?*

### Problem
*What's wrong with the current approach? Be specific about:*
- What scenarios does it fail to capture?
- What false positives/negatives does it produce?
- What operational decisions does it lead to incorrectly?

### Evidence
*Provide concrete examples or data supporting the problem:*
- Specific scenarios where the current approach fails
- Numerical examples showing the issue
- References to real-world experiences (anonymized)

---

## Proposed Change

### Description
*Detailed description of the proposed change. Include:*

#### New/Modified Metric Definition

| Attribute | Current | Proposed |
|-----------|---------|----------|
| **Name** | | |
| **Formula** | | |
| **Units** | | |
| **Range** | | |

#### Formula (if applicable)
```
proposed_metric = ...
```

#### Implementation Notes
*Key implementation considerations:*
- Data sources required
- Aggregation method
- Normalization approach

### Visualization Changes (if applicable)
*How would this change be visualized? Include mockups if possible.*

---

## Rationale

### Why This Approach
*Explain the reasoning behind this specific proposal:*
- Why this formula/threshold/weight?
- What makes this better than alternatives?
- What trade-offs does this make?

### Alignment with Project Goals
*How does this support the project's core analytical question?*

### Backward Compatibility
*Does this change break existing analysis? How should existing dashboards/notebooks be updated?*

---

## Alternatives Considered

### Alternative 1: [Name]
*Description of alternative approach*

**Pros:**
- 

**Cons:**
- 

**Why not chosen:**

### Alternative 2: [Name]
*Description of alternative approach*

**Pros:**
- 

**Cons:**
- 

**Why not chosen:**

### Do Nothing
*What happens if we don't make this change?*

---

## Expected Impact

### Operational Impact
*How will this change affect how operators interpret results?*

| Scenario | Current Interpretation | New Interpretation |
|----------|----------------------|-------------------|
| | | |

### Performance Impact
*Any changes to:*
- Query complexity
- Storage requirements
- Computation cost

### Migration Path
*Steps needed to adopt this change:*
1. 
2. 
3. 

---

## Validation Plan

### How to Test
*Concrete steps to validate this change works as intended:*

1. **Synthetic data test**: 
   - Scenario: 
   - Expected result:
   - Pass criteria:

2. **Edge case test**:
   - Scenario:
   - Expected result:
   - Pass criteria:

3. **Regression test**:
   - Ensure existing scenarios still work
   - Pass criteria:

### Success Metrics
*How will we know this change is successful?*
- Reduced false positives in scenario X
- Better correlation with operator actions
- Clearer interpretation in visualization

---

## Open Questions

*Questions that need discussion/resolution before finalizing:*

1. [Question 1]
2. [Question 2]
3. [Question 3]

---

## References

*Links to related issues, discussions, external resources:*

- Related issue: #NNN
- Prior discussion: [link]
- External reference: [link]

---

## Appendix (Optional)

### Detailed Calculations
*Extended mathematical derivations if needed*

### Sample Data
*Example data showing before/after*

### Historical Context
*Background on why current approach exists*

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| YYYY-MM-DD | Initial draft | Author |

---

## How to Submit This RFC

1. **Fork** this repository
2. **Copy** this template to `docs/rfcs/RFC-NNN-your-proposal.md`
3. **Fill out** all sections (mark N/A if truly not applicable)
4. **Open a Pull Request** with title `RFC: [Your Title]`
5. **Engage** with feedback in PR comments
6. **Iterate** until rough consensus is reached
7. **Merge** when approved by maintainers

### Review Criteria

RFCs will be evaluated on:
- **Clarity**: Is the problem and solution clearly stated?
- **Evidence**: Is there data/examples supporting the need?
- **Completeness**: Are alternatives considered?
- **Testability**: Can we validate this works?
- **Alignment**: Does this support project goals?

### Timeline

- Initial review: Within 1 week
- Discussion period: 2-4 weeks minimum
- Final decision: After reaching rough consensus

---

*Template version: 1.0*
