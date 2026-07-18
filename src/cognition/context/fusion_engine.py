import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
from datetime import datetime

from src.interaction.events import PresenceEvent
from src.cognition.context.provider import ProviderResponse
from src.cognition.context.registry import ContextProviderRegistry
from src.cognition.context.models import (
    CognitiveContext, 
    IdentityContext, 
    MemoryContext, 
    TemporalContext,
    ConflictTrace
)

class ContextFusionEngine:
    """
    Executes context providers concurrently, enforces timeouts, 
    resolves conflicts, and yields a unified CognitiveContext.
    """
    def __init__(self, registry: ContextProviderRegistry, timeout_sec: float = 0.5):
        self.registry = registry
        self.timeout_sec = timeout_sec
        # Allow enough workers for all active providers
        self.executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="ContextFusion")
        
    def fuse_context(self, event: PresenceEvent) -> CognitiveContext:
        """
        The core Context Lifecycle.
        """
        active_providers = self.registry.get_active_providers()
        
        provider_latencies: Dict[str, float] = {}
        dropped_providers: List[str] = []
        responses: List[ProviderResponse] = []
        
        # 1. Concurrent Execution
        start_time = time.perf_counter()
        
        # Submit all tasks
        future_to_provider = {
            self.executor.submit(p.fetch_context, event): p 
            for p in active_providers
        }
        
        import concurrent.futures
        
        # Collect with timeout
        try:
            for future in as_completed(future_to_provider.keys(), timeout=self.timeout_sec):
                p = future_to_provider[future]
                try:
                    resp = future.result()
                    responses.append(resp)
                    provider_latencies[p.name] = resp.latency_ms
                except Exception as e:
                    print(f"[ContextFusionEngine] Provider {p.name} failed: {e}")
                    dropped_providers.append(p.name)
        except concurrent.futures.TimeoutError:
            print(f"[ContextFusionEngine] Timeout of {self.timeout_sec}s reached. Dropping slow providers.")
                
        # Identify providers that timed out
        for future, p in future_to_provider.items():
            if not future.done():
                print(f"[ContextFusionEngine] Provider {p.name} TIMED OUT (> {self.timeout_sec}s)")
                dropped_providers.append(p.name)
                # We can't cancel running threads in Python, but we ignore their output
                
        # 2. Conflict Resolution & Normalization
        # For this milestone, we map directly to domains since we only have one provider per domain.
        # Future implementations will group responses by domain and resolve conflicts here.
        identity_ctx = None
        memory_ctx = None
        temporal_ctx = None
        conflict_traces = []
        
        for r in responses:
            if r.is_missing or r.error:
                continue
                
            if r.domain == "identity":
                identity_ctx = r.data
            elif r.domain == "memory":
                memory_ctx = r.data
            elif r.domain == "temporal":
                temporal_ctx = r.data
                
        # 3. Snapshot Generation
        return CognitiveContext(
            timestamp=datetime.now(),
            identity=identity_ctx,
            memory=memory_ctx,
            temporal=temporal_ctx,
            conflict_traces=conflict_traces,
            provider_latencies=provider_latencies,
            dropped_providers=dropped_providers
        )
