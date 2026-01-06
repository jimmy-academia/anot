#!/usr/bin/env python3
"""
utils/llm.py
Unified LLM API wrapper.

Fixes:
- Reuse a single sync OpenAI client (prevents "Too many open files")
- Reuse a single async OpenAI client
- Cap httpx connection pool sizes
- Add simple retry/backoff on transient network/429/5xx errors
"""

import os
import json
import time
import random
import threading
from pathlib import Path
from typing import Optional

import httpx

from utils.usage import get_usage_tracker

# httpx/httpcore logging suppression moved to main.py (after basicConfig)

# -----------------------------
# Global rate limiter
# -----------------------------
_api_semaphore: Optional[threading.Semaphore] = None
_async_semaphore = None  # asyncio.Semaphore, created lazily
_max_concurrent = 200  # safer default than 500 (override via init_rate_limiter)


def init_rate_limiter(max_concurrent: int = 200):
    """Initialize global rate limiter. Call from main() before evaluation."""
    global _api_semaphore, _max_concurrent, _async_semaphore
    _max_concurrent = int(max_concurrent)
    _api_semaphore = threading.Semaphore(_max_concurrent)
    _async_semaphore = None  # Reset async semaphore to be recreated with new limit


def _get_semaphore() -> threading.Semaphore:
    """Get or create the rate limiter semaphore."""
    global _api_semaphore
    if _api_semaphore is None:
        init_rate_limiter(_max_concurrent)
    return _api_semaphore


def _get_async_semaphore():
    """Get or create the async rate limiter semaphore."""
    import asyncio
    global _async_semaphore
    if _async_semaphore is None:
        _async_semaphore = asyncio.Semaphore(_max_concurrent)
    return _async_semaphore


# -----------------------------
# API key loading
# -----------------------------
def _load_api_key():
    """Load API key from file if not in environment."""
    if os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"):
        return
    # Try to load from ../../.openaiapi (one level above project root)
    key_file = Path(__file__).parent.parent.parent / ".openaiapi"
    if key_file.exists():
        key = key_file.read_text().strip()
        if key:
            os.environ["OPENAI_API_KEY"] = key


_load_api_key()

# -----------------------------
# Model configuration by role
# -----------------------------
MODEL_CONFIG = {
    "planner": "gpt-5-nano",
    "worker": "gpt-5-nano",
    "default": "gpt-5-nano",
}

# -----------------------------
# Token limits by model
# -----------------------------
# MODEL_CONTEXT_LIMITS: Total context window (input + output).
# Used with formula: input_budget = context - output_reserve - safety_margin
MODEL_CONTEXT_LIMITS = {
    # OpenAI
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo": 16385,
    "o1": 200000,
    "o1-mini": 128000,
    "o3-mini": 200000,
    # Anthropic
    "claude-3-5-sonnet-20241022": 200000,
    "claude-3-opus-20240229": 200000,
    "claude-3-sonnet-20240229": 200000,
    "claude-3-haiku-20240307": 200000,
}

# Default context limit for unknown models
DEFAULT_CONTEXT_LIMIT = 128000

# MODEL_INPUT_LIMITS: Fixed input token budgets for models with explicit caps.
# These override the formula calculation in get_token_budget().
# Use when a model has a hard input limit separate from context window.
MODEL_INPUT_LIMITS = {
    "gpt-5-nano": 270000,  # 400k context, but 270k input / 32k output split
}


def get_token_budget(model: str = None, output_reserve: int = 2000, safety_pct: float = 0.05) -> int:
    """Get input token budget for a model.

    Args:
        model: Model name. If None, uses configured model.
        output_reserve: Tokens to reserve for output (default: 2000)
        safety_pct: Safety margin as fraction of limit (default: 5%)

    Returns:
        Max input tokens to use
    """
    if model is None:
        model = _config.get("model") or MODEL_CONFIG.get("default", "gpt-4o")

    # Check for fixed input limit first
    if model in MODEL_INPUT_LIMITS:
        return MODEL_INPUT_LIMITS[model]

    # Otherwise use formula: context - output - margin
    limit = MODEL_CONTEXT_LIMITS.get(model, DEFAULT_CONTEXT_LIMIT)
    safety_margin = int(limit * safety_pct)
    return limit - output_reserve - safety_margin


def get_configured_model() -> str:
    """Get the currently configured model name."""
    return _config.get("model") or MODEL_CONFIG.get("default", "gpt-4o")

# -----------------------------
# Global config (set via configure())
# -----------------------------
_config = {
    "temperature": 0.0,
    "max_tokens": 1024,
    "max_tokens_reasoning": 4096,
    "provider": "openai",
    "model": None,  # None = use role-based MODEL_CONFIG
    "base_url": "",  # empty => use SDK default
    "request_timeout": 90.0,
    "max_retries": 6,
}


def configure(
    temperature: float = None,
    max_tokens: int = None,
    max_tokens_reasoning: int = None,
    provider: str = None,
    model: str = None,
    base_url: str = None,
    request_timeout: float = None,
    max_retries: int = None,
):
    """Configure LLM settings. Call from main() before evaluation."""
    if temperature is not None:
        _config["temperature"] = float(temperature)
    if max_tokens is not None:
        _config["max_tokens"] = int(max_tokens)
    if max_tokens_reasoning is not None:
        _config["max_tokens_reasoning"] = int(max_tokens_reasoning)
    if provider is not None:
        _config["provider"] = str(provider)
    if model is not None:
        _config["model"] = str(model)
    if base_url is not None:
        _config["base_url"] = str(base_url).strip()
    if request_timeout is not None:
        _config["request_timeout"] = float(request_timeout)
    if max_retries is not None:
        _config["max_retries"] = int(max_retries)


def get_model(role: str = "default") -> str:
    """Get model for a specific role. Uses _config['model'] override if set."""
    if _config["model"]:
        return _config["model"]
    return MODEL_CONFIG.get(role, MODEL_CONFIG["default"])


# -----------------------------
# OpenAI client reuse (SYNC)
# -----------------------------
_openai_client = None
_openai_http_client = None
_openai_client_lock = threading.Lock()


def _get_openai_client():
    """
    Get or create a singleton OpenAI sync client.
    Critical: do NOT create a new OpenAI() client per call.
    """
    global _openai_client, _openai_http_client
    if _openai_client is not None:
        return _openai_client

    with _openai_client_lock:
        if _openai_client is not None:
            return _openai_client

        import openai

        # Cap connection pool sizes to avoid FD blow-ups.
        limits = httpx.Limits(max_connections=50, max_keepalive_connections=20)
        _openai_http_client = httpx.Client(
            timeout=_config["request_timeout"],
            limits=limits,
            # trust_env=True by default; set False if you want to ignore proxy env vars
            trust_env=True,
        )

        base_url = (_config.get("base_url") or "").strip()
        if base_url:
            _openai_client = openai.OpenAI(http_client=_openai_http_client, base_url=base_url)
        else:
            _openai_client = openai.OpenAI(http_client=_openai_http_client)

        return _openai_client


# -----------------------------
# OpenAI client reuse (ASYNC)
# -----------------------------
_async_openai_client = None
_async_openai_http_client = None
_async_openai_lock = threading.Lock()


def _get_async_openai_client():
    """Get or create a singleton OpenAI async client."""
    global _async_openai_client, _async_openai_http_client
    if _async_openai_client is not None:
        return _async_openai_client

    with _async_openai_lock:
        if _async_openai_client is not None:
            return _async_openai_client

        import openai

        limits = httpx.Limits(max_connections=50, max_keepalive_connections=20)
        _async_openai_http_client = httpx.AsyncClient(
            timeout=_config["request_timeout"],
            limits=limits,
            trust_env=True,
        )

        base_url = (_config.get("base_url") or "").strip()
        if base_url:
            _async_openai_client = openai.AsyncOpenAI(http_client=_async_openai_http_client, base_url=base_url)
        else:
            _async_openai_client = openai.AsyncOpenAI(http_client=_async_openai_http_client)

        return _async_openai_client


# -----------------------------
# Anthropic client reuse (optional)
# -----------------------------
_async_anthropic_client = None
_anthropic_client = None
_anthropic_lock = threading.Lock()


def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is not None:
        return _anthropic_client
    with _anthropic_lock:
        if _anthropic_client is None:
            import anthropic
            _anthropic_client = anthropic.Anthropic()
        return _anthropic_client


def _get_async_anthropic_client():
    global _async_anthropic_client
    if _async_anthropic_client is not None:
        return _async_anthropic_client
    with _anthropic_lock:
        if _async_anthropic_client is None:
            import anthropic
            _async_anthropic_client = anthropic.AsyncAnthropic()
        return _async_anthropic_client


# -----------------------------
# Retry helpers
# -----------------------------
def _should_retry_openai_exc(e: Exception) -> bool:
    # We avoid importing exception classes directly to be version-tolerant.
    name = e.__class__.__name__
    if name in {
        "APIConnectionError",
        "APITimeoutError",
        "RateLimitError",
        "InternalServerError",
        "ServiceUnavailableError",
    }:
        return True

    # Some SDKs wrap HTTP status errors as APIStatusError with status_code
    status = getattr(e, "status_code", None)
    if status in {429, 500, 502, 503, 504}:
        return True

    return False


def _retry_delay(attempt: int) -> float:
    """Calculate retry delay with exponential backoff and jitter."""
    base = 1.0 * (2 ** attempt)
    jitter = random.random()
    return min(30.0, base + jitter)


def _build_messages(prompt: str, system: str) -> list:
    """Build messages list for chat completions."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


def _record_usage(
    model: str,
    provider: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: float,
    context: dict = None,
    prompt: str = None,
    response_text: str = None,
):
    """Record usage statistics for an LLM call."""
    tracker = get_usage_tracker()
    tracker.record(
        model=model,
        provider=provider,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=latency_ms,
        context=context,
        prompt_preview=prompt[:200] if prompt else None,
        response_preview=response_text[:200] if response_text else None,
    )


# -----------------------------
# Provider-specific implementations
# -----------------------------
def _call_openai_sync(client, messages: list, model: str, prompt: str = None, context: dict = None) -> str:
    """Call OpenAI API with retry logic (sync)."""
    is_new_model = ("gpt-5" in model) or ("o1" in model) or ("o3" in model)

    last_err = None
    for attempt in range(max(1, _config["max_retries"])):
        try:
            start_time = time.time()
            if is_new_model:
                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_completion_tokens=_config["max_tokens_reasoning"],
                )
            else:
                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=_config["temperature"],
                    max_tokens=_config["max_tokens"],
                )
            latency_ms = (time.time() - start_time) * 1000
            response_text = resp.choices[0].message.content or ""

            if resp.usage:
                _record_usage(
                    model=model,
                    provider="openai",
                    prompt_tokens=resp.usage.prompt_tokens,
                    completion_tokens=resp.usage.completion_tokens,
                    latency_ms=latency_ms,
                    context=context,
                    prompt=prompt,
                    response_text=response_text,
                )

            return response_text
        except Exception as e:
            last_err = e
            if _should_retry_openai_exc(e) and attempt < _config["max_retries"] - 1:
                time.sleep(_retry_delay(attempt))
                continue
            raise

    raise last_err


async def _call_openai_async(client, messages: list, model: str, prompt: str = None, context: dict = None) -> tuple:
    """Call OpenAI API with retry logic (async).

    Returns:
        tuple: (response_text, prompt_tokens, completion_tokens)
    """
    import asyncio

    is_new_model = ("gpt-5" in model) or ("o1" in model) or ("o3" in model)

    last_err = None
    for attempt in range(max(1, _config["max_retries"])):
        try:
            start_time = time.time()
            if is_new_model:
                resp = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_completion_tokens=_config["max_tokens_reasoning"],
                )
            else:
                resp = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=_config["temperature"],
                    max_tokens=_config["max_tokens"],
                )
            latency_ms = (time.time() - start_time) * 1000
            response_text = resp.choices[0].message.content or ""

            prompt_tokens = 0
            completion_tokens = 0
            if resp.usage:
                prompt_tokens = resp.usage.prompt_tokens
                completion_tokens = resp.usage.completion_tokens
                _record_usage(
                    model=model,
                    provider="openai",
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    latency_ms=latency_ms,
                    context=context,
                    prompt=prompt,
                    response_text=response_text,
                )

            return response_text, prompt_tokens, completion_tokens
        except Exception as e:
            last_err = e
            if _should_retry_openai_exc(e) and attempt < _config["max_retries"] - 1:
                await asyncio.sleep(_retry_delay(attempt))
                continue
            raise

    raise last_err


def _call_anthropic_sync(prompt: str, system: str, model: str, context: dict = None) -> str:
    """Call Anthropic API (sync)."""
    client = _get_anthropic_client()
    if "claude" not in model.lower():
        model = "claude-sonnet-4-20250514"

    start_time = time.time()
    resp = client.messages.create(
        model=model,
        max_tokens=_config["max_tokens"],
        system=system or "",
        messages=[{"role": "user", "content": prompt}],
    )
    latency_ms = (time.time() - start_time) * 1000
    response_text = resp.content[0].text

    if resp.usage:
        _record_usage(
            model=model,
            provider="anthropic",
            prompt_tokens=resp.usage.input_tokens,
            completion_tokens=resp.usage.output_tokens,
            latency_ms=latency_ms,
            context=context,
            prompt=prompt,
            response_text=response_text,
        )

    return response_text


async def _call_anthropic_async(prompt: str, system: str, model: str, context: dict = None) -> tuple:
    """Call Anthropic API (async).

    Returns:
        tuple: (response_text, prompt_tokens, completion_tokens)
    """
    client = _get_async_anthropic_client()
    if "claude" not in model.lower():
        model = "claude-sonnet-4-20250514"

    start_time = time.time()
    resp = await client.messages.create(
        model=model,
        max_tokens=_config["max_tokens"],
        system=system or "",
        messages=[{"role": "user", "content": prompt}],
    )
    latency_ms = (time.time() - start_time) * 1000
    response_text = resp.content[0].text

    prompt_tokens = 0
    completion_tokens = 0
    if resp.usage:
        prompt_tokens = resp.usage.input_tokens
        completion_tokens = resp.usage.output_tokens
        _record_usage(
            model=model,
            provider="anthropic",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            context=context,
            prompt=prompt,
            response_text=response_text,
        )

    return response_text, prompt_tokens, completion_tokens


def _call_local(prompt: str, system: str, model: str) -> str:
    """Call local/custom endpoint."""
    import urllib.request

    base_url = (_config["base_url"] or "").strip()
    if not base_url:
        raise ValueError("provider='local' requires base_url to be set via configure(..., base_url=...)")

    url = base_url.rstrip("/") + "/v1/chat/completions"
    messages = _build_messages(prompt, system)

    payload = {
        "model": model,
        "messages": messages,
        "temperature": _config["temperature"],
        "max_tokens": _config["max_tokens"],
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=int(_config["request_timeout"])) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"]


# -----------------------------
# Public API (sync)
# -----------------------------
def call_llm(prompt: str, system: str = "", provider: str = None, model: str = None, role: str = "default", context: dict = None) -> str:
    """Call LLM API. Uses role-based model selection if model not specified.

    Args:
        prompt: The user prompt
        system: Optional system prompt
        provider: LLM provider ("openai", "anthropic", "local")
        model: Model name (uses role-based selection if not specified)
        role: Role for model selection ("planner", "worker", "default")
        context: Optional dict for debugging (e.g., {"method": "anot", "phase": 1, "step": "0"})
    """
    if provider is None:
        provider = _config["provider"]
    if model is None:
        model = get_model(role)

    sem = _get_semaphore()
    with sem:
        if provider == "openai":
            client = _get_openai_client()
            messages = _build_messages(prompt, system)
            return _call_openai_sync(client, messages, model, prompt=prompt, context=context)
        elif provider == "anthropic":
            return _call_anthropic_sync(prompt, system, model, context=context)
        elif provider == "local":
            return _call_local(prompt, system, model)
        else:
            raise ValueError(f"Unknown provider: {provider}")


# -----------------------------
# Public API (async)
# -----------------------------
async def call_llm_async(prompt: str, system: str = "", provider: str = None, model: str = None, role: str = "default", context: dict = None, return_usage: bool = False):
    """Async version of call_llm for parallel execution.

    Args:
        prompt: The user prompt
        system: Optional system prompt
        provider: LLM provider ("openai", "anthropic")
        model: Model name (uses role-based selection if not specified)
        role: Role for model selection ("planner", "worker", "default")
        context: Optional dict for debugging (e.g., {"method": "anot", "phase": 1, "step": "0"})
        return_usage: If True, return dict with text and token counts; else return just text

    Returns:
        str: Response text (if return_usage=False)
        dict: {"text": str, "prompt_tokens": int, "completion_tokens": int} (if return_usage=True)
    """
    if provider is None:
        provider = _config["provider"]
    if model is None:
        model = get_model(role)

    sem = _get_async_semaphore()
    async with sem:
        if provider == "openai":
            client = _get_async_openai_client()
            messages = _build_messages(prompt, system)
            text, prompt_tokens, completion_tokens = await _call_openai_async(client, messages, model, prompt=prompt, context=context)
        elif provider == "anthropic":
            text, prompt_tokens, completion_tokens = await _call_anthropic_async(prompt, system, model, context=context)
        else:
            raise ValueError(f"Unknown provider for async: {provider}")

        if return_usage:
            return {"text": text, "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}
        return text


# -----------------------------
# Convenience: configure from argparse
# -----------------------------
def config_llm(args):
    """Configure LLM settings from args (if present)."""
    # Rate limiter
    max_conc = getattr(args, "max_concurrent", None)
    if max_conc is not None:
        init_rate_limiter(max_conc)
    else:
        init_rate_limiter(_max_concurrent)

    configure(
        temperature=getattr(args, "temperature", None),
        max_tokens=getattr(args, "max_tokens", None),
        max_tokens_reasoning=getattr(args, "max_tokens_reasoning", None),
        provider=getattr(args, "provider", None),
        model=getattr(args, "model", None),
        base_url=getattr(args, "base_url", None),
        request_timeout=getattr(args, "request_timeout", None),
        max_retries=getattr(args, "max_retries", None),
    )
