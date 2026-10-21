"""Simulated-runtime soak. Usage: python deployment/benchmarks/soak_runtime.py SECONDS [OUT.csv]
Samples every 500 cycles: RSS, threads, queue depth, dropped events, episodes, cycle latency p50/p95."""
import contextlib, io, os, sys, threading, time, csv
os.environ.setdefault("MEMORA_DB_PATH", os.path.join(os.environ.get("TMPDIR", "/tmp"), "memora_soak", "soak.sqlite"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import psutil
os.makedirs(os.path.dirname(os.environ["MEMORA_DB_PATH"]), exist_ok=True)
from src.application.factory import build_application
from src.runtime.runtime import AnchorRuntime

DURATION = float(sys.argv[1]) if len(sys.argv) > 1 else 1200
proc = psutil.Process()
sink = io.StringIO()
with contextlib.redirect_stdout(sink):
    coord = build_application(live_hardware=False)
    # Synthetic database: grant consent so face tracking and storage are exercised.
    from src.clinical.clinical_models import ConsentFeature
    for feature in (ConsentFeature.FACE_RECOGNITION, ConsentFeature.CONVERSATION_STORAGE):
        coord.pipeline.consent_mgr.update_consent(feature, True)
    rt = AnchorRuntime(coord); rt.initialize(); rt.start()
out = open(sys.argv[2] if len(sys.argv) > 2 else "soak_samples.csv", "w", newline="")
w = csv.writer(out); w.writerow(["t_s", "cycles", "rss_mb", "threads", "qdepth", "dropped", "episodes", "p50_ms", "p95_ms"])
t0 = time.time(); lat = []
while time.time() - t0 < DURATION:
    with contextlib.redirect_stdout(sink):
        c0 = time.perf_counter()
        rt.run_once()
        coord.consume_actions()
        lat.append((time.perf_counter() - c0) * 1000)
    if rt.cycle_count % 500 == 0:
        lat.sort()
        w.writerow([round(time.time() - t0, 1), rt.cycle_count, round(proc.memory_info().rss / 2**20, 1),
                    threading.active_count(), coord._cognitive_queue.qsize(), coord.dropped_events_count,
                    coord.database.episode_repo.count(), round(lat[len(lat)//2], 2), round(lat[int(len(lat)*0.95)], 2)])
        out.flush(); lat = []
        sink.seek(0); sink.truncate()
    time.sleep(0.05)
with contextlib.redirect_stdout(sink):
    rt.shutdown()
print("done", rt.cycle_count, "cycles", round(time.time() - t0), "s")
