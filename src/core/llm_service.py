"""LLM Service for managing local language models."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from threading import Lock
from typing import Any

# NOTE: Avoid importing torch at module import time; import lazily inside methods
# to prevent ImportError in lightweight environments/tests where torch is absent.

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
        llm_settings: dict[str, Any] | None = None,
        revision: str | None = None,
        local_model_path: str | None = None,
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

    def _resolve_model_source(self) -> tuple[str, str | None]:
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
            logger.info("LLM loaded successfully", extra={"backend": self.backend, "model": self.model_repo_id})
        except Exception as exc:
            logger.critical("Fatal error: Failed to load LLM", exc_info=True, extra={"error": str(exc)})
            self.llm = None
            self.tokenizer = None
        finally:
            self.is_loading = False

    def _load_ctransformers_model(self) -> None:
        try:
            from ctransformers import AutoModelForCausalLM  # type: ignore[import-untyped]
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("ctransformers backend requested but not installed") from exc

        if not self.model_repo_id:
            raise ValueError("Model repository ID is required for ctransformers backend.")

        source, model_file = self._resolve_model_source()

        # For GGUF models, use local file path if available
        if self.local_model_path and self.local_model_path.exists():
            if self.local_model_path.is_file():
                source = str(self.local_model_path)
                model_file = None  # Don't specify model_file when using direct file path
            else:
                # Directory with model file
                source = str(self.local_model_path)
                model_file = model_file or "*.gguf"  # Let ctransformers find the GGUF file

        model_kwargs: dict[str, Any] = {
            "model_type": self.settings.get("hf_model_type", "llama"),
            "context_length": self.settings.get("context_length", 2048),
        }

        # Only add model_file if we have a specific file
        if model_file and model_file != "*.gguf":
            model_kwargs["model_file"] = model_file

        for key in ("gpu_layers", "threads", "batch_size"):
            value = self.settings.get(key)
            if value is not None:
                model_kwargs[key] = value
        model_kwargs = {k: v for k, v in model_kwargs.items() if v not in (None, "")}

        try:
            logger.info(f"Loading ctransformers model from: {source}")
            self.llm = AutoModelForCausalLM.from_pretrained(source, **model_kwargs)
            self.tokenizer = None
            self.seq2seq = False
        except Exception as e:
            logger.warning("ctransformers failed to load model, falling back to transformers: %s", e)
            # Fall back to transformers backend
            self._load_transformers_model()

    def _load_transformers_model(self) -> None:
        model_id, _ = self._resolve_model_source()
        if not model_id:
            model_id = "google/flan-t5-small"

        try:
            import torch  # lazy import
            from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer  # type: ignore[import-untyped]
        except Exception as exc:  # pragma: no cover - allow import-time fallback
            logger.warning("Transformers/torch unavailable: %s", exc)
            self.llm = None
            self.tokenizer = None
            self.seq2seq = False
            return

        tokenizer_kwargs: dict[str, Any] = {}
        if self.revision:
            tokenizer_kwargs["revision"] = self.revision

        self.tokenizer = AutoTokenizer.from_pretrained(model_id, **tokenizer_kwargs)
        model_kwargs: dict[str, Any] = {"low_cpu_mem_usage": True}
        if self.revision:
            model_kwargs["revision"] = self.revision
        model_kwargs["torch_dtype"] = torch.float16 if torch.cuda.is_available() else torch.float32

        try:
            self.llm = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)
            self.seq2seq = False
        except Exception:
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
        cached_response = LLMResponseCache.get_llm_response(model_identifier, prompt)
        if cached_response is not None:
            logger.debug("Cache hit for LLM response (model: %s)", model_identifier)
            return cached_response

        start_time = time.time()
        gen_params = dict(self.settings.get("generation_params", {}))
        gen_params.update(kwargs)

        max_new_tokens = int(gen_params.pop("max_new_tokens", 256))  # Reduced for faster generation
        temperature = float(gen_params.pop("temperature", 0.1))
        top_p = float(gen_params.pop("top_p", 0.8))  # Slightly more focused
        top_k = int(gen_params.pop("top_k", 20))  # Reduced for faster sampling
        repetition_penalty = float(gen_params.pop("repeat_penalty", 1.1))
        stop_sequences = gen_params.pop("stop_sequences", None)

        # Safety limits to prevent infinite generation
        max_new_tokens = min(max_new_tokens, 1024)  # Hard limit to prevent runaway generation
        if not stop_sequences:
            stop_sequences = ["</analysis>", "\n\n---", "\n\n\n", "###", "##", "#"]

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

                # Safety check: prevent corrupted or infinite text
                if len(result) > 2000:  # If response is too long, truncate it
                    result = result[:2000] + "... [truncated]"
                if result.count(result[:50]) > 3:  # If text repeats too much, clean it
                    result = result[:500] + "... [repetitive content detected]"

                # Cache the result for future use
                generation_time = time.time() - start_time
                ttl_hours = 6.0 if generation_time > 5.0 else 12.0  # Longer TTL for quick responses
                LLMResponseCache.set_llm_response(model_identifier, prompt, result, ttl_hours)

                logger.debug("LLM generation completed in %ss, cached with TTL {ttl_hours}h", generation_time)
                return result

            # Transformers backend
            from transformers import StoppingCriteria, StoppingCriteriaList  # type: ignore[import-untyped]
            import torch  # lazy import

            if self.tokenizer is None or self.llm is None:
                logger.error("Tokenizer/LLM not initialised for transformers backend")
                return "Error: tokenizer unavailable."

            inputs = self.tokenizer(
                prompt, return_tensors="pt", truncation=True, max_length=int(self.settings.get("context_length", 512))
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

                class _StopOnSequences(StoppingCriteria):
                    def __init__(self, sequence_token_ids):
                        self.sequence_token_ids = sequence_token_ids

                    def __call__(self, input_ids, scores, **kwargs):  # type: ignore[override]
                        tokens = input_ids[0].tolist()
                        for sequence in self.sequence_token_ids:
                            if len(tokens) >= len(sequence) and tokens[-len(sequence) :] == sequence:
                                return True
                        return False

                stop_token_ids = []
                for sequence in stop_sequences:
                    if not sequence:
                        continue
                    encoded = self.tokenizer(
                        sequence, add_special_tokens=False, return_attention_mask=False, return_token_type_ids=False
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

            # Safety check: prevent corrupted or infinite text
            if len(result) > 2000:  # If response is too long, truncate it
                result = result[:2000] + "... [truncated]"
            if result.count(result[:50]) > 3:  # If text repeats too much, clean it
                result = result[:500] + "... [repetitive content detected]"

            # Cache the result for future use
            generation_time = time.time() - start_time
            ttl_hours = 6.0 if generation_time > 5.0 else 12.0  # Longer TTL for quick responses
            LLMResponseCache.set_llm_response(model_identifier, prompt, result, ttl_hours)

            logger.debug("LLM generation completed in %ss, cached with TTL {ttl_hours}h", generation_time)
            return result

        except Exception as exc:
            logger.error("An error occurred during text generation", exc_info=True, extra={"error": str(exc)})
            return "An error occurred during text generation."

    def generate_analysis(self, prompt: str, **kwargs) -> str:
        return self.generate(prompt, **kwargs)
