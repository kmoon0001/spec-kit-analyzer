"""LLM Service for managing local language models."""
from __future__ import annotations

import logging
import time
from threading import Lock
from typing import Any, Dict, Optional
from pathlib import Path

from src.core.cache_service import LLMResponseCache

logger = logging.getLogger(__name__)


class LLMService:
    """Thread-safe, lazy-loading language model service."""

    _instance = None
    _lock = Lock()

    def __init__(
        self,
        model_repo_id: str,
        model_filename: str,
        llm_settings: Optional[Dict[str, Any]] = None,
        revision: Optional[str] = None,
        local_model_path: Optional[str] = None,
    ) -> None:
        self.model_repo_id = model_repo_id
        self.model_filename = model_filename
        self.settings = llm_settings or {}
        self.revision = revision
        self.local_model_path = Path(local_model_path).expanduser().resolve() if local_model_path else None

        self.backend = (self.settings.get("model_type") or "transformers").lower()
        self.llm = None
        self.tokenizer = None
        self.seq2seq = False
        self.is_loading = False

    def _resolve_model_source(self) -> tuple[str, Optional[str]]:
        """Resolve the repository/directory and optional model file for loading."""
        source = self.model_repo_id
        model_file = self.model_filename or None
        if self.local_model_path:
            candidate = self.local_model_path
            if candidate.is_file():
                source = str(candidate.parent)
                model_file = model_file or candidate.name
            else:
                source = str(candidate)
        return source, model_file

    def _load_model(self) -> None:
        if self.llm:
            return

        self.is_loading = True
        try:
            if self.backend == "ctransformers":
                self._load_ctransformers_model()
            else:
                self._load_transformers_model()
            logger.info(
                "LLM loaded successfully",
                extra={"backend": self.backend, "model": self.model_repo_id},
            )
        except Exception as exc:  # noqa: BLE001 - preserve error detail for operators
            logger.critical(
                "Fatal error: Failed to load LLM",
                exc_info=True,
                extra={"error": str(exc)},
            )
            self.llm = None
            self.tokenizer = None
        finally:
            self.is_loading = False

    def _load_ctransformers_model(self) -> None:
        try:
            from ctransformers import AutoModelForCausalLM
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("ctransformers backend requested but not installed") from exc

        if not self.model_repo_id:
            raise ValueError("Model repository ID is required for ctransformers backend.")

        source, model_file = self._resolve_model_source()
        model_kwargs: Dict[str, Any] = {
            "model_file": model_file,
            "model_type": self.settings.get("hf_model_type", "llama"),
            "context_length": self.settings.get("context_length", 2048),
        }
        for key in ("gpu_layers", "threads", "batch_size"):
            value = self.settings.get(key)
            if value is not None:
                model_kwargs[key] = value
        model_kwargs = {k: v for k, v in model_kwargs.items() if v not in (None, "")}

        self.llm = AutoModelForCausalLM.from_pretrained(
            source,
            **model_kwargs,
        )
        self.tokenizer = None
        self.seq2seq = False

    def _load_transformers_model(self) -> None:
        model_id, _ = self._resolve_model_source()
        if not model_id:
            model_id = "google/flan-t5-small"

        from transformers import (
            AutoModelForCausalLM,
            AutoModelForSeq2SeqLM,
            AutoTokenizer,
        )

        import torch

        tokenizer_kwargs: Dict[str, Any] = {}
        if self.revision:
            tokenizer_kwargs["revision"] = self.revision

        self.tokenizer = AutoTokenizer.from_pretrained(model_id, **tokenizer_kwargs)
        model_kwargs: Dict[str, Any] = {"low_cpu_mem_usage": True}
        if self.revision:
            model_kwargs["revision"] = self.revision
        model_kwargs["torch_dtype"] = (
            torch.float16 if torch.cuda.is_available() else torch.float32
        )

        try:
            self.llm = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)
            self.seq2seq = False
        except Exception:  # noqa: BLE001 - fallback to seq2seq architectures
            self.llm = AutoModelForSeq2SeqLM.from_pretrained(model_id, **model_kwargs)
            self.seq2seq = True

        device = "cuda" if torch.cuda.is_available() else "cpu"
        if self.llm is not None:
            self.llm.to(device)
            self.llm.eval()

    def _ensure_model_loaded(self) -> None:
        if self.llm or self.is_loading:
            return
        with self._lock:
            if not self.llm:
                self._load_model()

    def is_ready(self) -> bool:
        self._ensure_model_loaded()
        return self.llm is not None and (self.backend == "ctransformers" or self.tokenizer is not None)

    def generate(self, prompt: str, **kwargs) -> str:
        if not self.is_ready():
            logger.error("LLM is not available or failed to load. Cannot generate text.")
            return "Error: LLM service is not available."

        # Check cache first for performance optimization
        model_identifier = f"{self.model_repo_id}_{self.backend}"
        cached_response = LLMResponseCache.get_llm_response(prompt, model_identifier)
        if cached_response is not None:
            logger.debug(f"Cache hit for LLM response (model: {model_identifier})")
            return cached_response

        start_time = time.time()
        gen_params = dict(self.settings.get("generation_params", {}))
        gen_params.update(kwargs)

        max_new_tokens = int(gen_params.pop("max_new_tokens", 512))
        temperature = float(gen_params.pop("temperature", 0.1))
        top_p = float(gen_params.pop("top_p", 0.9))
        top_k = int(gen_params.pop("top_k", 40))
        repetition_penalty = float(gen_params.pop("repeat_penalty", 1.1))
        stop_sequences = gen_params.pop("stop_sequences", None)

        try:
            if self.backend == "ctransformers" and self.llm is not None:
                output = self.llm(  # type: ignore[misc]
                    prompt,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    repetition_penalty=repetition_penalty,
                    stop=stop_sequences,
                    **gen_params,
                )
                result = output.strip() if isinstance(output, str) else str(output)
                
                # Cache the result for future use
                generation_time = time.time() - start_time
                ttl_hours = 6.0 if generation_time > 5.0 else 12.0  # Longer TTL for quick responses
                LLMResponseCache.set_llm_response(prompt, model_identifier, result, ttl_hours)
                
                logger.debug(f"LLM generation completed in {generation_time:.2f}s, cached with TTL {ttl_hours}h")
                return result

            if self.tokenizer is None:
                logger.error("Tokenizer not initialised for transformers backend")
                return "Error: tokenizer unavailable."

            import torch

            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=int(self.settings.get("context_length", 512)),
            )
            device = next(self.llm.parameters()).device  # type: ignore[attr-defined]
            inputs = {key: value.to(device) for key, value in inputs.items()}

            generate_kwargs = {
                "max_new_tokens": max_new_tokens,
                "temperature": max(temperature, 1e-3),
                "top_p": top_p,
                "top_k": top_k,
                "repetition_penalty": repetition_penalty,
                "do_sample": temperature > 0,
            }
            stopping_criteria = None
            if stop_sequences:
                from transformers import StoppingCriteria, StoppingCriteriaList  # type: ignore

                class _StopOnSequences(StoppingCriteria):
                    def __init__(self, sequence_token_ids):
                        super().__init__()
                        self.sequence_token_ids = sequence_token_ids

                    def __call__(self, input_ids, scores, **kwargs):  # type: ignore[override]
                        tokens = input_ids[0].tolist()
                        for sequence in self.sequence_token_ids:
                            if len(tokens) >= len(sequence) and tokens[-len(sequence):] == sequence:
                                return True
                        return False

                stop_token_ids = []
                for sequence in stop_sequences:
                    if not sequence:
                        continue
                    encoded = self.tokenizer(
                        sequence,
                        add_special_tokens=False,
                        return_attention_mask=False,
                        return_token_type_ids=False,
                    )
                    ids = encoded.get("input_ids")
                    if not ids:
                        continue
                    if isinstance(ids[0], list):
                        stop_token_ids.extend(ids)
                    else:
                        stop_token_ids.append(ids)
                if stop_token_ids:
                    stopping_criteria = StoppingCriteriaList([_StopOnSequences(stop_token_ids)])

            if self.seq2seq:
                generate_kwargs["max_length"] = max_new_tokens

            if stopping_criteria is not None:
                generate_kwargs["stopping_criteria"] = stopping_criteria

            with torch.no_grad():
                outputs = self.llm.generate(**inputs, **generate_kwargs)

            result = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
            
            # Cache the result for future use
            generation_time = time.time() - start_time
            ttl_hours = 6.0 if generation_time > 5.0 else 12.0  # Longer TTL for quick responses
            LLMResponseCache.set_llm_response(prompt, model_identifier, result, ttl_hours)
            
            logger.debug(f"LLM generation completed in {generation_time:.2f}s, cached with TTL {ttl_hours}h")
            return result
            
        except Exception as exc:  # noqa: BLE001 - capture inference issues
            logger.error("An error occurred during text generation", exc_info=True, extra={"error": str(exc)})
            return "An error occurred during text generation."

    def generate_analysis(self, prompt: str, **kwargs) -> str:
        return self.generate(prompt, **kwargs)
