import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

np = pytest.importorskip("numpy")

from src.core.guideline_service import GuidelineService


@pytest.fixture
def patched_service(tmp_path):
    sources = [str(tmp_path / "guidelines.txt")]
    (tmp_path / "guidelines.txt").write_text(
        "This is a Medicare guideline about documentation.",
        encoding="utf-8",
    )

    # Mock faiss and joblib before they are imported by the service
    sys.modules["faiss"] = MagicMock()
    sys.modules["joblib"] = MagicMock()

    # Configure the faiss mock that will be used
    mock_index = MagicMock()
    mock_index.search.return_value = (
        np.array([[0.9, 0.5, 0.1]], dtype="float32"),
        np.array([[0, -1, -1]]),
    )
    sys.modules["faiss"].IndexFlatIP.return_value = mock_index

    with (
        patch("src.core.guideline_service.SentenceTransformer") as mock_st_cls,
        patch("src.core.guideline_service.get_settings") as mock_get_settings,
        patch.object(GuidelineService, "_load_or_build_index", return_value=None),
    ):
        mock_get_settings.return_value = SimpleNamespace(
            models=SimpleNamespace(retriever="sentence-transformers/test"),
            retrieval_settings=SimpleNamespace(similarity_top_k=3),
        )

        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(1, 384).astype("float32")
        mock_st_cls.return_value = mock_model

        service = GuidelineService(sources=sources, cache_dir=str(tmp_path))
        service.guideline_chunks = [
            ("This is a Medicare guideline about documentation.", "guidelines.txt"),
        ]
        service.faiss_index = mock_index
        service.is_index_ready = True
        service.model = mock_model

        yield service

    # Clean up the mocks
    if "faiss" in sys.modules:
        del sys.modules["faiss"]
    if "joblib" in sys.modules:
        del sys.modules["joblib"]


def test_search_returns_results(patched_service: GuidelineService):
    results = patched_service.search("documentation guidance")
    patched_service.model.encode.assert_called_once()
    patched_service.faiss_index.search.assert_called_once()
    assert results
    assert results[0]["source"] == "guidelines.txt"


def test_search_empty_when_not_ready(patched_service: GuidelineService):
    patched_service.is_index_ready = False
    assert patched_service.search("irrelevant") == []
