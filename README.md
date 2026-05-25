# QURVE - AI + Quantum-Inspired Portfolio Optimization Platform

Welcome to the **QURVE** platform repository. QURVE is a production-grade, hybrid AI and quantum-inspired platform designed for institutional portfolio optimization, scaling beyond classical limitations through hybrid execution pipelines and rigorous scientific validation.

## Core Identity

QURVE stands at the intersection of modern finance, scalable web architecture, and hybrid quantum computing. Our core mission is **AI + Quantum-Inspired Portfolio Optimization**. 

We heavily rely on AWS Braket SV1 as our primary production quantum backend. *Note: Older exploratory TN1 components have been moved into experimental isolation to maintain stability in the primary production orchestration path.*

## Architecture

QURVE's architecture resembles institutional fintech infrastructure with an event-driven core for distributed computing, deep observability, and an integrated solver hierarchy.

The stack utilizes:
- **FastAPI**: High-performance asynchronous backend and orchestration server.
- **React**: Dynamic, telemetry-driven frontend UI.
- **AWS Braket SV1**: Primary production cloud quantum simulator for scalable state vector optimization.
- **Qiskit**: Standardized formulation and gate-based operations.
- **Neal**: State-of-the-art classical simulated annealing for robust fallback and local validation.
- **Event-Driven Orchestration**: Decentralized, robust event routing for multi-solver parallelization.
- **Persistent Analytics**: Long-term metric storage to evaluate solver efficiency and allocation topology.
- **Real Telemetry**: Granular observation of optimization tasks, runtime, and BQM translation parameters.

## Features

- **Portfolio Optimization**: Advanced combinatorial optimization utilizing QUBO formulations to solve large-scale asset allocation.
- **Hybrid Quantum/Classical Routing**: Intelligent fallback and multi-backend routing to guarantee robust execution.
- **Live Telemetry**: Real-time insights into solver states, iteration progress, and Hamiltonian scales.
- **Analytics Engine**: Persistent, institutional-grade analytics spanning multiple historical portfolio rebalances.
- **Websocket Streaming**: Low-latency transmission of live optimization metrics direct to the React frontend.
- **Allocation Validation**: Strict feasibility enforcement protecting against broken invariants; we enforce topology preservation without synthetic repair.
- **Institutional Observability**: Enterprise-level logging, auditing, and performance profiling.

## Scientific Integrity

Our platform is driven by rigorous scientific constraints:
- **Allocation Validation**: The system ensures 100% adherence to defined portfolio constraints.
- **Topology Preservation**: The optimization landscape accurately reflects true market dynamics without artificial landscape shaping.
- **Strict Feasibility Enforcement**: We do not implement synthetic repair, hidden normalizations, or fabricated allocations—only purely valid QUBO outputs are propagated to the end-user.

---

### Installation & Deployment

(WIP: Production deployment manifests are located under `infrastructure/` and `docker/`.)
