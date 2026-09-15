"""
Structured Output Transport using Groq Native Strict JSON Schema Mode.

Purpose:
    Provides a unified, reliable structured output transport that bypasses
    LangChain tool/function calling for AI debate analysis agents.
    Includes process-wide LLM concurrency control and rolling TPM admission budgeting.
"""

import collections
import re
import threading
import time
from typing import Type, TypeVar, List, Union, Dict, Any
from pydantic import BaseModel
from groq import Groq
from app.core.config import settings

T = TypeVar("T", bound=BaseModel)

_groq_client = None
_llm_semaphore = threading.Semaphore(2)

STRUCTURED_OUTPUT_MAX_TOKENS: Dict[str, int] = {
    "FallacyDetectionResponse": 4096,
    "ArgumentAnalysisResponse": 2560,
    "CounterargumentResponse": 1536,
    "AIDebateOpponentResponse": 1536,
    "CoachingResponse": 1536,
    "RecommendationResponse": 1024,
    "LearningPathResponse": 1024,
}


def get_groq_client() -> Groq:
    """Return a singleton Groq API client instance."""
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    return _groq_client


def prepare_strict_json_schema(pydantic_model: Type[T], name: str) -> Dict[str, Any]:
    """
    Generate an OpenAI/Groq Strict JSON Schema from a Pydantic model.
    Enforces additionalProperties=False and populates required property lists
    recursively across main schema and all $defs objects.
    """
    schema = pydantic_model.model_json_schema()

    def sanitize(node):
        if isinstance(node, dict):
            for k in ["title", "default", "description"]:
                node.pop(k, None)

            if node.get("type") == "object" or "properties" in node:
                node["type"] = "object"
                node["additionalProperties"] = False
                props = list(node.get("properties", {}).keys())
                node["required"] = props

            for key, value in list(node.items()):
                sanitize(value)
        elif isinstance(node, list):
            for item in node:
                sanitize(item)

    sanitize(schema)
    return {
        "name": name,
        "strict": True,
        "schema": schema,
    }


class TPMAdmissionController:
    """
    Centralized process-wide token budget admission controller for Groq API calls.
    Tracks a rolling 60-second window of token consumption and active reservations
    to enforce a safe TPM ceiling (e.g., 7,000 tokens/min against an 8,000 TPM limit).
    """

    def __init__(
        self,
        tpm_limit: int = 8000,
        safety_margin: int = 1000,
    ):
        self.tpm_limit = tpm_limit
        self.safety_margin = safety_margin
        self.safe_ceiling = max(1000, tpm_limit - safety_margin)
        self.lock = threading.Lock()
        self.consumed_history = collections.deque()  # (timestamp, actual_tokens)
        self.active_reservations = {}  # req_id -> estimated_tokens
        self.req_counter = 0
        self.pause_until = 0.0

    def admit_and_reserve(self, estimated_tokens: int) -> int:
        """
        Blocks the calling thread until there is sufficient headroom in the 60s window.
        Returns a unique reservation ID.
        """
        while True:
            now = time.time()
            with self.lock:
                # 1. Prune history older than 60s
                while self.consumed_history and (now - self.consumed_history[0][0] > 60.0):
                    self.consumed_history.popleft()

                # 2. Check if globally paused due to TPM 429 reset window
                if now < self.pause_until:
                    sleep_time = self.pause_until - now + 0.1
                else:
                    # 3. Calculate current utilization
                    used_in_window = sum(t for _, t in self.consumed_history)
                    reserved_now = sum(self.active_reservations.values())
                    current_total = used_in_window + reserved_now

                    if current_total + estimated_tokens <= self.safe_ceiling:
                        # Admitted! Reserve tokens
                        self.req_counter += 1
                        req_id = self.req_counter
                        self.active_reservations[req_id] = estimated_tokens
                        return req_id

                    # Need to wait for oldest record in history to expire
                    if self.consumed_history:
                        oldest_ts = self.consumed_history[0][0]
                        sleep_time = max(0.2, (oldest_ts + 60.0) - now + 0.1)
                    else:
                        sleep_time = 0.5

            time.sleep(sleep_time)

    def reconcile(self, req_id: int, actual_tokens: Union[int, None], estimated_tokens: int):
        """
        Reconciles a completed request: releases active reservation and logs actual token usage.
        """
        now = time.time()
        with self.lock:
            self.active_reservations.pop(req_id, None)
            tokens_to_record = actual_tokens if (isinstance(actual_tokens, int) and actual_tokens > 0) else estimated_tokens
            self.consumed_history.append((now, tokens_to_record))

    def release(self, req_id: int):
        """
        Releases a cancelled or failed reservation without recording token consumption.
        """
        with self.lock:
            self.active_reservations.pop(req_id, None)

    def set_pause(self, seconds: float):
        """
        Pauses all admissions for `seconds` when a TPM rate limit error occurs.
        """
        with self.lock:
            self.pause_until = max(self.pause_until, time.time() + seconds)


tpm_controller = TPMAdmissionController()


def invoke_structured(
    messages: List[Any],
    pydantic_model: Type[T],
    temperature: float = 0.2,
    max_retries: int = 2,
    max_tokens: Union[int, None] = None
) -> T:
    """
    Invoke Groq LLM using native strict JSON Schema response_format with
    process-wide concurrency limiting and rolling TPM admission control.
    
    Args:
        messages: List of message tuples, dicts, or LangChain Message objects.
        pydantic_model: Target Pydantic model class for response validation.
        temperature: Model sampling temperature.
        max_retries: Maximum attempts for transient network or schema validation errors.
        max_tokens: Optional explicit token budget override.

    Returns:
        Validated instance of pydantic_model.
    """
    if settings.LLM_PROVIDER != "groq" or not settings.GROQ_API_KEY:
        # Fallback for Ollama or local LLM provider using LangChain
        from app.ai.llm.llm import llm
        from langchain_core.prompts import ChatPromptTemplate
        prompt = ChatPromptTemplate.from_messages(messages)
        chain = prompt | llm.with_structured_output(pydantic_model)
        return chain.invoke({})

    name = pydantic_model.__name__
    token_budget = max_tokens if max_tokens is not None else STRUCTURED_OUTPUT_MAX_TOKENS.get(name, 1536)
    strict_schema = prepare_strict_json_schema(pydantic_model, name)

    # Standardize message objects for Groq API
    groq_messages = []
    for m in messages:
        if isinstance(m, tuple):
            role, content = m
            role_name = "user" if role in ["human", "user"] else "system" if role == "system" else "assistant"
            groq_messages.append({"role": role_name, "content": str(content)})
        elif isinstance(m, dict):
            groq_messages.append(m)
        elif hasattr(m, "type") and hasattr(m, "content"):
            role_name = "user" if m.type in ["human", "user"] else "system" if m.type == "system" else "assistant"
            groq_messages.append({"role": role_name, "content": str(m.content)})
        else:
            groq_messages.append({"role": "user", "content": str(m)})

    last_error = None
    client = get_groq_client()

    for attempt in range(max_retries):
        req_id = None
        try:
            with _llm_semaphore:
                req_id = tpm_controller.admit_and_reserve(token_budget)
                try:
                    response = client.chat.completions.create(
                        model=settings.GROQ_MODEL,
                        temperature=temperature,
                        max_completion_tokens=token_budget,
                        response_format={
                            "type": "json_schema",
                            "json_schema": strict_schema,
                        },
                        messages=groq_messages,
                    )
                    content = response.choices[0].message.content
                    if not content or not content.strip():
                        raise ValueError("Groq returned empty response content.")

                    actual_tokens = None
                    if hasattr(response, "usage") and response.usage:
                        actual_tokens = getattr(response.usage, "total_tokens", None)

                    tpm_controller.reconcile(req_id, actual_tokens, token_budget)
                    req_id = None
                    return pydantic_model.model_validate_json(content)

                except Exception as inner_exc:
                    if req_id is not None:
                        tpm_controller.release(req_id)
                        req_id = None
                    raise inner_exc

        except Exception as e:
            last_error = e
            err_str = str(e).lower()

            # Daily quota exhaustion (TPD / RPD / daily limit) -> IMMEDIATELY abort (0 retries)
            is_daily = "tokens per day" in err_str or "requests per day" in err_str or "tpd" in err_str or "rpd" in err_str
            if is_daily:
                raise e

            # Short TPM (Tokens Per Minute) limit
            is_tpm = "tokens per minute" in err_str or "tpm" in err_str or "429" in err_str
            if is_tpm:
                match = re.search(r"try again in ([\d\.]+)s", err_str)
                reset_sec = float(match.group(1)) if match else 3.0
                tpm_controller.set_pause(reset_sec)

                if attempt < max_retries - 1:
                    time.sleep(reset_sec)
                    continue
                else:
                    raise e

            if attempt < max_retries - 1:
                time.sleep(1)

    raise last_error
