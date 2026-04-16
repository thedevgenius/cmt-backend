import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

@dataclass
class AppError:
    component: str
    message: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

class AppState:
    """Thread-safe registry of in-process application errors."""

    def __init__(self):
        self._lock = threading.Lock()
        self._errors: dict[str, AppError] = {}

    def set_error(self, component: str, message: str) -> None:
        with self._lock:
            self._errors[component] = AppError(component, message)

    def clear_error(self, component: str) -> None:
        with self._lock:
            self._errors.pop(component, None)

    def get_errors(self) -> dict[str, dict]:
        with self._lock:
            return {
                k: {"message": v.message, "since": v.timestamp}
                for k, v in self._errors.items()
            }

    @property
    def is_healthy(self) -> bool:
        with self._lock:
            return not self._errors


# singleton — import this everywhere
app_state = AppState()
