# QURVE AI - DEPENDENCY COMPATIBILITY MATRIX

## OVERVIEW

This document tracks compatibility between core dependencies and provides guidance for stable production deployment.

## CURRENT COMPATIBILITY STATUS

### ✅ COMPATIBLE DEPENDENCIES

| Dependency | Version | Status | Notes |
|------------|--------|-------|-------|
| Python | 3.14 | ✅ STABLE | Latest stable version |
| FastAPI | 0.128.0 | ✅ STABLE | Production-ready |
| Pydantic | 2.12.5 | ✅ STABLE | V2, stable API |
| NumPy | 1.26.4 | ✅ STABLE | Latest stable |
| SciPy | 1.14.1 | ✅ STABLE | Latest stable |
| Qiskit | 1.3.0 | ✅ STABLE | Compatible with Pydantic V2 |
| DWave Neal | 0.12.0 | ✅ STABLE | Latest stable |
| Asyncio | Built-in | ✅ STABLE | Python 3.14 compatible |

### ⚠️ COMPATIBILITY ISSUES

| Dependency | Issue | Impact | Mitigation |
|------------|-------|--------|------------|
| Amazon Braket SDK | 1.117.1 | Pydantic V1/V2 conflict | Isolated adapter layer |
| Braket LocalSimulator | 1.117.1 | Validator registration errors | Safe lazy loading |

## VERSION CONSTRAINTS

### HARD REQUIREMENTS
- Python >= 3.12 (3.14 recommended)
- Pydantic >= 2.0 (V2 required)
- FastAPI >= 0.100.0
- NumPy >= 1.24.0
- SciPy >= 1.10.0

### SOFT REQUIREMENTS
- Qiskit >= 1.0.0 (for quantum execution)
- DWave Ocean >= 0.12.0 (for quantum annealing)
- Amazon Braket SDK >= 1.100.0 (with adapter layer)

### COMPATIBILITY MATRIX

| Python | FastAPI | Pydantic | Qiskit | DWave | Braket | Status |
|--------|----------|----------|--------|-------|--------|--------|
| 3.12 | 0.128.0 | 2.0+ | 1.0+ | 0.12.0+ | 1.100.0+ | ✅ STABLE |
| 3.13 | 0.128.0 | 2.0+ | 1.0+ | 0.12.0+ | 1.100.0+ | ✅ STABLE |
| 3.14 | 0.128.0 | 2.0+ | 1.0+ | 0.12.0+ | 1.100.0+ | ⚠️ BRAKET ISSUES |

## DEPENDENCY-SPECIFIC ISSUES

### AMAZON BRAKET SDK
**Issue**: Pydantic V1/V2 compatibility conflict
**Root Cause**: Braket SDK 1.117.1 uses Pydantic V1 validators incompatible with Pydantic V2.12.5
**Impact**: LocalSimulator and circuit creation fail with validator registration errors
**Mitigation**: 
- Isolated adapter layer prevents import failures
- Safe lazy loading with try/except around all imports
- Graceful fallback to classical solvers
- Environment validation endpoint for monitoring

### QISKIT INTEGRATION
**Issue**: Sparse matrix dtype compatibility
**Root Cause**: Qiskit AerSimulator strict dtype validation
**Mitigation**:
- Integer mapping for variable names
- Forced float conversion for weights
- Consistent variable indexing throughout conversion

### DWAVE NEAL INTEGRATION
**Status**: ✅ FULLY COMPATIBLE
**Notes**: 
- No compatibility issues detected
- Stable performance and execution
- Proper fallback behavior

## PRODUCTION DEPLOYMENT GUIDELINES

### RECOMMENDED VERSION LOCK
```
# Core dependencies
python>=3.12,<3.15
fastapi==0.128.0
pydantic==2.12.5
numpy==1.26.4
scipy==1.14.1

# Quantum dependencies (optional)
qiskit>=1.0.0
dwave-ocean>=0.12.0
amazon-braket-sdk>=1.100.0

# Development dependencies
pytest>=7.0.0
black>=23.0.0
mypy>=1.0.0
```

### VALIDATION REQUIREMENTS

Before production deployment, verify:

1. **Python Environment**: `python --version` >= 3.12
2. **Core Dependencies**: All imports succeed without warnings
3. **Quantum Solvers**: 
   - Qiskit: Basic circuit execution works
   - Neal: Simulated annealing works
   - Braket: Adapter layer handles compatibility
4. **Telemetry**: Structured logging with correlation IDs
5. **Concurrency**: Thread pool execution without deadlocks
6. **Fallbacks**: Graceful degradation when quantum solvers fail

### MONITORING CHECKPOINTS

#### Runtime Monitoring
- [ ] Memory usage < 2GB per benchmark
- [ ] Execution time < 60 seconds per solver
- [ ] Thread count < CPU cores * 2
- [ ] Error rate < 5% per solver type

#### Health Endpoints
- [ ] `/api/v1/system/health` - System health
- [ ] `/api/v1/system/braket-health` - Braket compatibility
- [ ] `/api/v1/system/quantum-health` - Quantum solver status

#### Log Monitoring
- [ ] Structured JSON logs with correlation IDs
- [ ] Telemetry consistency > 95%
- [ ] Error tracking with fallback chains
- [ ] Performance metrics collection

## TROUBLESHOOTING GUIDE

### COMMON ISSUES

#### Braket Import Failures
**Symptoms**: `Validators defined with incorrect fields` errors
**Solutions**:
1. Check adapter layer isolation
2. Verify lazy loading implementation
3. Monitor `/api/v1/system/braket-health` endpoint
4. Review Pydantic version compatibility

#### Qiskit Dtype Errors
**Symptoms**: `scipy.sparse does not support dtype <U32>` errors
**Solutions**:
1. Verify integer mapping in qubo_model.py
2. Check variable name consistency
3. Validate float conversion for weights
4. Test with small problem sizes first

#### Thread Safety Issues
**Symptoms**: Deadlocks, race conditions, memory leaks
**Solutions**:
1. Review thread pool configuration
2. Check async/await usage
3. Verify proper context management
4. Monitor worker pool statistics

#### Performance Degradation
**Symptoms**: Slow execution, high memory usage
**Solutions**:
1. Check solver parameter tuning
2. Verify resource guardrails
3. Review concurrent execution limits
4. Analyze performance metrics

## FUTURE COMPATIBILITY ROADMAP

### Q2 2026
- [ ] Upgrade to Braket SDK 1.120+ (if Pydantic V2 compatible)
- [ ] Migrate to Qiskit 1.4+ (performance improvements)
- [ ] Add quantum hardware validation

### Q3 2026
- [ ] Full Pydantic V2 migration across all dependencies
- [ ] Multi-threaded quantum solver execution
- [ ] Advanced error recovery mechanisms

---

**Last Updated**: 2026-05-10
**Next Review**: 2026-06-01
**Owner**: Qurve AI Engineering Team
