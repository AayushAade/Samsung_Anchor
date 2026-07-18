import queue
import threading
import logging
from typing import Callable, Any, Dict

logger = logging.getLogger(__name__)

class EventBus:
    """
    Thread-safe synchronous event bus for passing messages
    between the Vision thread (Producer) and Cognitive thread (Consumer).
    """
    def __init__(self):
        self.subscribers: Dict[str, list[Callable]] = {}
        self.lock = threading.Lock()

    def subscribe(self, topic: str, callback: Callable[[Any], None]):
        """Register a callback for a specific topic."""
        with self.lock:
            if topic not in self.subscribers:
                self.subscribers[topic] = []
            if callback not in self.subscribers[topic]:
                self.subscribers[topic].append(callback)

    def publish(self, topic: str, payload: Any):
        """
        Immediately invoke all registered callbacks for the topic.
        If the callback needs to be processed asynchronously, the callback
        itself should push the payload into a thread-safe Queue.
        """
        with self.lock:
            callbacks = self.subscribers.get(topic, []).copy()

        for callback in callbacks:
            try:
                callback(payload)
            except Exception as e:
                logger.error(f"Error in EventBus subscriber for topic '{topic}': {e}")
