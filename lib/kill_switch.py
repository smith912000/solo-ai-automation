"""
Kill Switch Module

Universal halt mechanism for all automations.
Prevents runaway costs, infinite loops, and cascade failures.
"""

import time
import logging
from typing import Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class KillCondition:
    """A single condition that can trigger a kill switch."""
    name: str
    check_fn: Callable[[], bool]
    message: str = ""
    severity: str = "critical"  # critical, high, medium


@dataclass
class KillSwitchState:
    """Current state of the kill switch."""
    is_killed: bool = False
    killed_at: Optional[datetime] = None
    killed_by: Optional[str] = None
    kill_reason: Optional[str] = None
    
    # Tracking
    tokens_used: int = 0
    api_failures: int = 0
    step_executions: dict = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)


class KillSwitch:
    """
    Universal kill switch for automation safety.
    
    Usage:
        ks = KillSwitch(max_tokens=5000, max_time=300)
        
        # Track usage
        ks.add_tokens(500)
        ks.record_step("qualification")
        
        # Check conditions
        if ks.should_kill():
            raise KillSwitchTriggered(ks.state.kill_reason)
    """
    
    def __init__(
        self,
        max_tokens: int = 5000,
        max_cost_usd: float = 0.50,
        max_time_seconds: int = 300,
        max_retries_per_step: int = 2,
        max_consecutive_api_failures: int = 2,
        token_spike_multiplier: float = 2.0,
        expected_tokens: int = 1000,
    ):
        self.max_tokens = max_tokens
        self.max_cost_usd = max_cost_usd
        self.max_time_seconds = max_time_seconds
        self.max_retries_per_step = max_retries_per_step
        self.max_consecutive_api_failures = max_consecutive_api_failures
        self.token_spike_multiplier = token_spike_multiplier
        self.expected_tokens = expected_tokens
        
        self.state = KillSwitchState()
        self._alert_callbacks: list[Callable[[str], None]] = []
    
    def add_alert_callback(self, callback: Callable[[str], None]):
        """Add a callback to be called when kill switch triggers."""
        self._alert_callbacks.append(callback)
    
    def add_tokens(self, count: int):
        """Record token usage."""
        self.state.tokens_used += count
    
    def record_step(self, step_name: str):
        """Record that a step was executed."""
        if step_name not in self.state.step_executions:
            self.state.step_executions[step_name] = 0
        self.state.step_executions[step_name] += 1
    
    def record_api_failure(self):
        """Record an API failure."""
        self.state.api_failures += 1
    
    def reset_api_failures(self):
        """Reset API failure count after successful call."""
        self.state.api_failures = 0
    
    def should_kill(self) -> bool:
        """
        Check all kill conditions.
        Returns True if any condition is met.
        """
        if self.state.is_killed:
            return True
        
        # Check each condition
        conditions = [
            self._check_token_limit,
            self._check_token_spike,
            self._check_timeout,
            self._check_step_loops,
            self._check_api_failures,
        ]
        
        for check in conditions:
            result, reason = check()
            if result:
                self._trigger_kill(reason)
                return True
        
        return False
    
    def _check_token_limit(self) -> tuple[bool, str]:
        """Check if token limit exceeded."""
        if self.state.tokens_used > self.max_tokens:
            return True, f"token_limit_exceeded ({self.state.tokens_used} > {self.max_tokens})"
        return False, ""
    
    def _check_token_spike(self) -> tuple[bool, str]:
        """Check if tokens spiked unexpectedly."""
        threshold = self.expected_tokens * self.token_spike_multiplier
        if self.state.tokens_used > threshold:
            return True, f"token_spike ({self.state.tokens_used} > {threshold:.0f} expected)"
        return False, ""
    
    def _check_timeout(self) -> tuple[bool, str]:
        """Check if execution time exceeded."""
        elapsed = time.time() - self.state.start_time
        if elapsed > self.max_time_seconds:
            return True, f"timeout ({elapsed:.0f}s > {self.max_time_seconds}s)"
        return False, ""
    
    def _check_step_loops(self) -> tuple[bool, str]:
        """Check if any step executed too many times."""
        for step, count in self.state.step_executions.items():
            if count > self.max_retries_per_step:
                return True, f"step_loop_detected ({step} executed {count} times)"
        return False, ""
    
    def _check_api_failures(self) -> tuple[bool, str]:
        """Check if too many consecutive API failures."""
        if self.state.api_failures >= self.max_consecutive_api_failures:
            return True, f"api_failure_cascade ({self.state.api_failures} consecutive failures)"
        return False, ""
    
    def _trigger_kill(self, reason: str):
        """Trigger the kill switch."""
        self.state.is_killed = True
        self.state.killed_at = datetime.utcnow()
        self.state.killed_by = "kill_switch"
        self.state.kill_reason = reason
        
        logger.warning(f"Kill switch triggered: {reason}")
        
        # Alert callbacks
        for callback in self._alert_callbacks:
            try:
                callback(reason)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    def get_status(self) -> dict:
        """Get current status for logging."""
        return {
            "is_killed": self.state.is_killed,
            "killed_by": self.state.killed_by,
            "kill_reason": self.state.kill_reason,
            "tokens_used": self.state.tokens_used,
            "api_failures": self.state.api_failures,
            "step_executions": self.state.step_executions,
            "elapsed_seconds": time.time() - self.state.start_time,
        }


class KillSwitchTriggered(Exception):
    """Exception raised when kill switch is triggered."""
    
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Kill switch triggered: {reason}")


def create_default_kill_switch() -> KillSwitch:
    """Create a kill switch with default settings from environment."""
    import os
    
    return KillSwitch(
        max_tokens=int(os.getenv("MAX_TOKENS_PER_RUN", "5000")),
        max_cost_usd=float(os.getenv("MAX_COST_PER_RUN_USD", "0.50")),
        max_time_seconds=int(os.getenv("MAX_EXECUTION_TIME_SECONDS", "300")),
        max_retries_per_step=int(os.getenv("MAX_RETRIES_PER_STEP", "2")),
    )
