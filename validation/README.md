# MEMORA (Samsung Anchor) — Runtime Reliability & System Validation Framework

**Phase 18 Implementation** — Production Reliability, Subsystem Benchmarking, Resource Monitoring & Fault Recovery Harness.

---

## Overview

The **MEMORA Validation Framework** is a standalone engineering validation engine designed to evaluate the continuous runtime stability, memory footprint, subsystem latency, and fault recovery of MEMORA (Samsung Anchor) independently of unit tests.

---

## Directory Architecture

```
validation/
├── __init__.py
├── README.md                          # Framework Documentation & Usage Manual
├── benchmarks/
│   ├── __init__.py
│   └── benchmark_suite.py            # Latency, throughput, and P95 performance benchmarks
├── telemetry/
│   ├── __init__.py
│   └── telemetry_collector.py        # Real-time resource (CPU, RAM, threads) & telemetry monitoring
├── fault_injection/
│   ├── __init__.py
│   └── fault_injector.py             # Hardware failure, missing data, and frame fault injection
├── runner/
│   ├── __init__.py
│   └── validation_runner.py          # Master continuous session runner & report generator
├── reports/                           # Output directory for structured Markdown reports
├── logs/                              # Output directory for runtime validation logs
└── artifacts/                         # Output directory for evidence packages (`summary.json`)
```

---

## Execution Instructions

### One-Command Runtime Validation CLI

```bash
# Execute standard validation session (5 seconds)
python validate_runtime.py

# Execute custom duration session (e.g. 60 seconds)
python validate_runtime.py --duration 60

# Execute module directly
python -m validation.runner.validation_runner
```

---

## Key Metrics Evaluated

1. **Subsystem Benchmarks**:
   - `Identity Lookup Latency` (avg, min, max, p95, ops/sec)
   - `FAISS Vector Search Latency` (128D index search)
   - `Face Recognition Frame Latency`
   - `Object Location Logging Latency`
   - `Database State Commit Latency`
   - `Memory Retrieval Latency`
   - `Episode Creation Latency`

2. **Resource & Telemetry Monitoring**:
   - Process RAM usage (MB)
   - Process CPU utilization (%)
   - Active OS thread count
   - Frame rate throughput (FPS)

3. **Fault Injection Scenarios**:
   - `Corrupted Frame Handling` (bad shape, None, NaN arrays)
   - `Missing Identity Lookup` (non-existent identity query isolation)
   - `Camera Hardware Fallback` (invalid device index 9999 recovery)
   - `Microphone Hardware Fallback` (audio HAL exception isolation)
   - `Database Schema Recovery` (schema clear and re-initialization)

---

## Evidence Package Generation

Every validation run automatically generates:
1. **Markdown Validation Report**: Saved to `validation/reports/validation_report_<timestamp>.md`.
2. **Evidence Artifact Package**: Saved to `validation/artifacts/evidence_<timestamp>/summary.json` containing complete system info, Git commit hash, environment details, benchmark metrics, and fault test logs.
