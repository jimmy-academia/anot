#!/usr/bin/env python3
"""Abstract base class for all evaluation methods."""

import os
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class BaseMethod(ABC):
    """Abstract base class for evaluation methods."""

    name: str = "base"

    def __init__(self, run_dir: str = None, defense: bool = False, verbose: bool = True, **kwargs):
        self.run_dir = run_dir
        self.defense = defense
        self.verbose = verbose
        self._debug_log_file = None
        self._debug_log_lock = threading.Lock()

        # Initialize debug log for non-ANoT methods (ANoT has its own debug logging)
        if run_dir and self.name != "anot":
            try:
                log_path = os.path.join(run_dir, "debug.log")
                self._debug_log_file = open(log_path, "w", buffering=1)
                self._debug_log_file.write(f"=== {self.name} Debug Log @ {datetime.now().isoformat()} ===\n\n")
            except Exception:
                pass

    def __del__(self):
        """Close debug log file on cleanup."""
        if hasattr(self, '_debug_log_file') and self._debug_log_file:
            try:
                self._debug_log_file.close()
            except Exception:
                pass

    def _log_llm_call(self, step: str, prompt: str, response: str, system: str = None, request_id: str = None):
        """Log LLM response to debug file (thread-safe). No-op for ANoT.

        Only logs output (response) to keep debug files compact.
        """
        if not self._debug_log_file:
            return
        with self._debug_log_lock:
            try:
                ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                req_str = request_id or "?"
                self._debug_log_file.write(f"[{ts}] {req_str} | {step}\n")
                self._debug_log_file.write(f"{response}\n")
                self._debug_log_file.write(f"{'-'*40}\n")
                self._debug_log_file.flush()
            except Exception:
                pass

    @abstractmethod
    def evaluate(self, query: Any, context: str) -> int:
        """Evaluate item against request.

        Args:
            query: User request text (what user is searching for)
            context: Restaurant data (str or dict)

        Returns:
            1 (recommend), 0 (neutral), -1 (not recommend)
        """
        pass

    def evaluate_ranking(self, query: str, context: str, k: int = 1) -> str:
        """Evaluate ranking task. Optional method for methods that support ranking.

        Args:
            query: User request text (what user is searching for)
            context: All restaurants formatted with indices
            k: Number of top predictions to return

        Returns:
            String with top-k indices (e.g., "3" or "3, 1, 5")
        """
        # Default implementation: just return "1"
        return "1"

    def __call__(self, query: Any, context: str) -> int:
        """Allow method to be called as function."""
        return self.evaluate(query, context)

    def __repr__(self) -> str:
        """Show method info."""
        info = f"{self.__class__.__name__}(defense={self.defense}"
        if self.run_dir:
            info += f", run_dir={self.run_dir}"
        info += ")"
        return info
