# Simulated runtime soak — 2026-10-20

**What was run:** `deployment/benchmarks/soak_runtime.py` (simulated camera,
microphone and speaker; one synthetic face continuously in view; cycle delay
50 ms). Machine: macOS 27.0 arm64, Python 3.11.15. Other workloads (test runs,
benchmarks) ran concurrently at times, which explains short-term dips/spikes.

**Scope:** simulated sensors only. This says nothing about real camera/microphone
behaviour, model inference cost, or multi-hour stability.

| Run | Duration | Cycles | RSS (steady) | Threads | Dropped events | Median / p95 cycle latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Before fix (`87f6e94`) | 1200 s | 16,500+ | 130–190 MB | 6 | 0 | **rising**: ~10.6 / 12.0 ms at 500 cycles → 19.4 / 22.0 ms at 16,500 |
| After fix (`609d2e8`) | 600 s | 9,141 | 130.8 MB (flat last 3 min) | 6 | 0 | **flat**: 10.6 / 11.9 ms at 8,500–9,000 |

Cause of the rise: unbounded per-track embedding history in
`src/vision/face_recognizer.py`, averaged twice per frame (fixed in `609d2e8`).

Raw samples: `soak_20261020_before_track_fix.csv`, `soak_20261020_after_track_fix.csv`
(columns: t_s, cycles, rss_mb, threads, qdepth, dropped, episodes, p50_ms, p95_ms;
latency percentiles are per 500-cycle window).

Text-mode turn latency (`pipeline.process` with speech, 400 turns, same machine):
median 2.1 ms, p95 2.6 ms; with 20,000 stored episodes: median 3.5 ms.
Startup (imports + build_application): ~2.2 s.

## Cycle 2 re-run (commit `466be66`-era code, harness at `8699583`)

Consent granted on the synthetic database so face enrolment/tracking and storage are
exercised (with consent off, as in real first use, the face path is skipped entirely).

| Run | Duration | Cycles | RSS (steady) | Threads | Dropped events | Median / p95 cycle latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Consent granted | 1200 s | 19,931 | 47–49 MB after warm-up | 6 (flat) | 0 | 2.8–10.8 / 3.3–12.2 ms per window, no upward trend |
| Consent not granted | 600 s | 10,444 | 31–123 MB (fluctuating, no growth trend) | 3 (flat) | 0 | 2.3–5.4 / 5.8–6.7 ms |

Raw samples: `soak_20261020_cycle2_consent.csv`. Variation between windows tracks other load
on the machine (test runs and container builds ran concurrently for part of the time).
