"""Einfache Bremse gegen Passwort-Raten beim Login.

Zählt Fehlversuche je Schlüssel (Benutzername + Client-Adresse) in einem
Zeitfenster. Der Zustand liegt im Prozess: bei mehreren Workern zählt jeder
für sich, für den Pilot reicht das, später gehört das in einen gemeinsamen
Speicher (Redis) oder an den Reverse Proxy.
"""

import threading
import time
from collections.abc import Callable


class LoginThrottle:
    def __init__(
        self,
        max_failures: int = 5,
        window_seconds: float = 900,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.max_failures = max_failures
        self.window = window_seconds
        self._clock = clock
        self._failures: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _recent(self, key: str) -> list[float]:
        cutoff = self._clock() - self.window
        recent = [t for t in self._failures.get(key, []) if t > cutoff]
        if recent:
            self._failures[key] = recent
        else:
            self._failures.pop(key, None)
        return recent

    def retry_after(self, key: str) -> int:
        """Sekunden, die der Schlüssel noch gesperrt ist; 0 = nicht gesperrt."""
        with self._lock:
            recent = self._recent(key)
            if len(recent) < self.max_failures:
                return 0
            return max(1, int(recent[0] + self.window - self._clock()) + 1)

    def failure(self, key: str) -> None:
        with self._lock:
            self._recent(key)
            self._failures.setdefault(key, []).append(self._clock())

    def success(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)


login_throttle = LoginThrottle()
