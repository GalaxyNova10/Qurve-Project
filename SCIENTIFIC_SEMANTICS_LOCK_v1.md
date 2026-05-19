# SCIENTIFIC SEMANTICS LOCK (v1.0)

This document establishes the **authoritative semantic contract** for all QURVE AI benchmarks. These rules are non-negotiable and invariant. Future changes must be additive-only.

## 1. Energy Semantics
- **Raw Energy**: The direct output from the solver.
- **Repaired Energy**: The energy after constraint repair logic. This is the **authoritative energy** used for ranking.
- **Normalized Energy**: A visualization-only field (0-1). It MUST NOT be used for ranking or certification.
- **Comparable Energy**: Only results with the same `benchmark_fingerprint` and `normalization_version` are comparable.

## 2. Ranking Semantics
Ranking MUST follow this priority:
1. **Feasibility**: Feasible solutions always outrank infeasible ones.
2. **Comparability**: Comparable solutions outrank non-comparable ones.
3. **Energy**: Lower repaired energy is better.
4. **Latency**: A secondary tie-breaker if energy is identical.

## 3. Certification Semantics
Certification is split into two independent axes:

### A. Operational Certification
- **CERTIFIED**: Success/Fallback + Latency < 30s.
- **DEGRADED**: Success/Fallback but High Latency or Fallback triggered.
- **FAILED**: Execution error or timeout.

### B. Scientific Certification
- **CERTIFIED**: Feasible + High Approx Ratio (>0.8).
- **RESEARCH_GRADE**: Feasible but requires repair logic.
- **UX_GRADE**: Infeasible but reconstructible.
- **NON_COMPARABLE**: Decode integrity failure.

## 4. Provenance & Replay Semantics
- **Fingerprint Integrity**: Any benchmark missing a `benchmark_fingerprint` is considered `DELEGATED_LEGACY` and is not suitable for scientific regression.
- **Deterministic Replay**: A replay with the same `fingerprint` and `seed` MUST produce a 1:1 identical bitstream and energy result.

## 5. Invariant Rules
- **No Silent Normalization**: Invalid or infeasible runs MUST NOT be silently adjusted to appear successful.
- **No Hidden Fallbacks**: Every fallback MUST be logged in the `execution_provenance`.
- **Forensic Traceability**: Every result MUST carry proof of execution (ARN or LocalID).

---
**LOCK STATUS: ACTIVE (v1.0)**
**DATE: 2026-05-15**
