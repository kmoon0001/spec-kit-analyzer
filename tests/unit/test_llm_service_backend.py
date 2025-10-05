from types import SimpleNamespace
import sys

import torch

from src.core.llm_service import LLMService


def test_ctransformers_load_uses_expected_kwargs(mocker):
    fake_auto = mocker.Mock()
    fake_module = SimpleNamespace(AutoModelForCausalLM=fake_auto)
    mocker.patch.dict(sys.modules, {"ctransformers": fake_module})

    service = LLMService(
        model_repo_id="TheBloke/meditron-7B-GGUF",
        model_filename="meditron-7b.Q4_K_M.gguf",
        llm_settings={"model_type": "ctransformers", "context_length": 4096, "gpu_layers": 20},
    )

    service._load_ctransformers_model()

    fake_auto.from_pretrained.assert_called_once()
    _, kwargs = fake_auto.from_pretrained.call_args
    assert kwargs["model_file"] == "meditron-7b.Q4_K_M.gguf"
    assert kwargs["context_length"] == 4096
    assert kwargs["gpu_layers"] == 20
    assert kwargs["model_type"] == "llama"


class DummyTokenizer:
    def __call__(self, text, **kwargs):
        if kwargs.get("return_tensors") == "pt":
            return {
                "input_ids": torch.tensor([[7, 8]]),
                "attention_mask": torch.tensor([[1, 1]]),
            }
        return {"input_ids": [[42, 43]]}

    def decode(self, token_ids, skip_special_tokens=True):
        return "decoded"


def test_transformers_generate_applies_stop_sequences(mocker):
    service = LLMService(
        model_repo_id="hf-internal-testing/tiny-random-gpt2",
        model_filename="",
        llm_settings={"model_type": "transformers", "generation_params": {}},
    )
    service._ensure_model_loaded = lambda: None
    service.llm = mocker.Mock()
    service.llm.parameters.return_value = iter([SimpleNamespace(device=torch.device("cpu"))])
    service.llm.generate.return_value = torch.tensor([[1, 2, 3]])
    service.tokenizer = DummyTokenizer()

    result = service.generate("hello", stop_sequences=["END"])

    assert result == "decoded"
    assert service.llm.generate.called
    _, kwargs = service.llm.generate.call_args
    assert "stopping_criteria" in kwargs and kwargs["stopping_criteria"] is not None
