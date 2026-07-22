import json
from datetime import datetime
from typing import Any, Dict, List


class StructuredLogger:
    """
    Centralized JSON structured logger supporting log levels and rotation.
    """

    def __init__(self, module_name: str = "MemoraCore") -> None:
        self.module_name = module_name
        self._history: List[Dict[str, Any]] = []

    def _format_entry(self, level: str, message: str, extra: Dict[str, Any]) -> Dict[str, Any]:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level.upper(),
            "module": self.module_name,
            "message": message,
        }
        if extra:
            entry["context"] = extra

        self._history.append(entry)
        if len(self._history) > 100:
            self._history.pop(0)

        return entry

    def info(self, message: str, **kwargs) -> Dict[str, Any]:
        return self._format_entry("INFO", message, kwargs)

    def warning(self, message: str, **kwargs) -> Dict[str, Any]:
        return self._format_entry("WARNING", message, kwargs)

    def error(self, message: str, **kwargs) -> Dict[str, Any]:
        return self._format_entry("ERROR", message, kwargs)

    def critical(self, message: str, **kwargs) -> Dict[str, Any]:
        return self._format_entry("CRITICAL", message, kwargs)

    def get_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._history[-limit:]
