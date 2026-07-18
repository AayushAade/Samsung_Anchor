from src.cognition.episode import Episode
from src.cognition.memory_consolidator import MemoryConsolidator
from src.cognition.forgetting_strategy import ForgettingStrategy
from src.llm.reasoning_client import ReasoningClient
import concurrent.futures

class CognitiveMemoryManager:
    """
    The master orchestrator for the Memory Lifecycle.
    Listens for new episodes and asynchronously consolidates them.
    Also handles periodic forgetting (decay).
    """
    def __init__(self, session_factory, llm_client: ReasoningClient):
        self.consolidator = MemoryConsolidator(session_factory, llm_client)
        self.forgetting_strategy = ForgettingStrategy(session_factory)
        # Dedicated thread pool for heavy extraction tasks
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

    def process_episode(self, episode: Episode):
        """
        Submits the episode for asynchronous consolidation so the main thread
        (or even the cognitive worker) isn't blocked by the LLM extraction.
        """
        self.executor.submit(self.consolidator.consolidate, episode)

    def trigger_decay(self):
        """
        Manually trigger the decay process (usually run on a CRON schedule).
        """
        self.executor.submit(self.forgetting_strategy.decay_memories)

    def shutdown(self):
        self.executor.shutdown(wait=False)
