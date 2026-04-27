"""
Loop Control
Prevents agents from running forever: max iterations + timeout + circuit breaker.

Without loop control, agents can:
  - Loop indefinitely when tools keep failing
  - Consume thousands of tokens on a stuck task
  - Exhaust API quotas
  - Never return a response to the user

Run: python 04_resiliency/loop_control.py
"""
import sys
import time
import signal
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from core.logger import get_logger

log = get_logger(__name__)


# ── Custom exceptions ─────────────────────────────────────────────────────────

class MaxIterationsError(Exception):
    def __init__(self, max_iter: int, last_action: str = ""):
        self.max_iter = max_iter
        self.last_action = last_action
        super().__init__(f"Agent exceeded {max_iter} iterations. Last action: {last_action!r}")


class AgentTimeoutError(Exception):
    def __init__(self, timeout_seconds: float):
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Agent exceeded {timeout_seconds}s timeout")


class StuckLoopError(Exception):
    """Raised when the agent repeats the same action without progress."""
    def __init__(self, repeated_action: str, count: int):
        super().__init__(f"Agent stuck: '{repeated_action}' repeated {count} times with no progress")


# ── Loop Controller ───────────────────────────────────────────────────────────

class LoopController:
    """
    Wraps agent loops to enforce max iterations and detect stuck loops.
    """

    def __init__(
        self,
        max_iterations: int = 10,
        max_repeated_actions: int = 3,
    ):
        self.max_iterations = max_iterations
        self.max_repeated_actions = max_repeated_actions
        self._iteration = 0
        self._action_history: list[str] = []

    def tick(self, action_taken: str = "") -> None:
        """Call at the top of each agent loop iteration."""
        self._iteration += 1
        if self._iteration > self.max_iterations:
            raise MaxIterationsError(self.max_iterations, action_taken)

        if action_taken:
            self._action_history.append(action_taken)
            # Detect repeating the same action
            if len(self._action_history) >= self.max_repeated_actions:
                recent = self._action_history[-self.max_repeated_actions:]
                if len(set(recent)) == 1:  # all the same
                    raise StuckLoopError(action_taken, self.max_repeated_actions)

        log.info("loop.tick", iteration=self._iteration, max=self.max_iterations)

    @property
    def iterations_remaining(self) -> int:
        return max(0, self.max_iterations - self._iteration)

    def reset(self) -> None:
        self._iteration = 0
        self._action_history.clear()


# ── Timeout context manager ───────────────────────────────────────────────────

@contextmanager
def agent_timeout(seconds: float) -> Generator[None, None, None]:
    """
    Context manager that raises AgentTimeoutError if the block takes too long.
    Uses SIGALRM (Unix only). On Windows, use threading.Timer instead.
    """
    def _handler(signum, frame):
        raise AgentTimeoutError(seconds)

    try:
        signal.signal(signal.SIGALRM, _handler)
        signal.alarm(int(seconds))
        yield
    except AttributeError:
        # signal.SIGALRM not available on Windows — use thread-based timeout
        import threading

        timer = threading.Timer(seconds, lambda: (_ for _ in ()).throw(AgentTimeoutError(seconds)))
        timer.start()
        try:
            yield
        finally:
            timer.cancel()
    finally:
        try:
            signal.alarm(0)
        except AttributeError:
            pass


# ── Circuit breaker ───────────────────────────────────────────────────────────

class CircuitBreaker:
    """
    Stops calling a failing service after N consecutive failures.
    States: CLOSED (normal) → OPEN (blocking) → HALF_OPEN (testing)

    Prevents wasting time on a service that's clearly down.
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._state = self.CLOSED
        self._failure_count = 0
        self._opened_at: float | None = None

    @property
    def state(self) -> str:
        if self._state == self.OPEN:
            if time.time() - (self._opened_at or 0) > self.recovery_timeout:
                self._state = self.HALF_OPEN
        return self._state

    def call(self, fn, *args, **kwargs):
        if self.state == self.OPEN:
            raise RuntimeError(f"Circuit is OPEN — service unavailable. Retry after {self.recovery_timeout}s")

        try:
            result = fn(*args, **kwargs)
            if self._state == self.HALF_OPEN:
                self._state = self.CLOSED
                self._failure_count = 0
                log.info("circuit_breaker.recovered")
            return result
        except Exception as e:
            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                self._state = self.OPEN
                self._opened_at = time.time()
                log.error("circuit_breaker.opened", failures=self._failure_count)
            raise


if __name__ == "__main__":
    print("=== LOOP CONTROL DEMO ===\n")

    # ── Demo 1: Max iterations ───────────────────────────────────────────────
    print("--- Demo 1: Max Iterations ---")
    controller = LoopController(max_iterations=5)
    try:
        for i in range(100):  # would run forever
            controller.tick(action_taken=f"tool_call_{i}")
            print(f"  Iteration {i+1}: {controller.iterations_remaining} remaining")
            time.sleep(0.01)
    except MaxIterationsError as e:
        print(f"  ✓ Caught: {e}")

    # ── Demo 2: Stuck loop detection ────────────────────────────────────────
    print("\n--- Demo 2: Stuck Loop Detection ---")
    controller2 = LoopController(max_iterations=20, max_repeated_actions=3)
    actions = ["web_search", "web_search", "web_search", "web_search"]  # stuck
    try:
        for action in actions:
            controller2.tick(action_taken=action)
            print(f"  Action: {action}")
    except StuckLoopError as e:
        print(f"  ✓ Caught: {e}")

    # ── Demo 3: Circuit breaker ──────────────────────────────────────────────
    print("\n--- Demo 3: Circuit Breaker ---")
    call_count = 0

    def flaky_service():
        global call_count
        call_count += 1
        raise ConnectionError("Service unavailable")

    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5.0)
    for i in range(6):
        try:
            cb.call(flaky_service)
        except ConnectionError:
            print(f"  Call {i+1}: Service error (state={cb.state})")
        except RuntimeError as e:
            print(f"  Call {i+1}: {e}")

    print(f"\n  Total calls to service: {call_count} (circuit stopped more)")

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n--- Loop Control Checklist ---")
    controls = [
        ("max_iterations", "Every agent loop MUST have this. No exceptions."),
        ("timeout", "Wall-clock limit per task. Prevents hung agents."),
        ("stuck detection", "Detect same action repeated → break loop + log"),
        ("circuit breaker", "Stop hammering a failing service immediately"),
        ("cost limit", "Stop if token budget exceeded (optional but wise)"),
    ]
    for name, desc in controls:
        print(f"  {name:<20} {desc}")
