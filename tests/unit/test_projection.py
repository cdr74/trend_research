"""Unit tests for the 2D projection and dimensionality reduction module."""

import numpy as np
import pytest

from radar.presentation.projection import project_embeddings_to_2d


def test_project_embeddings_empty_and_single() -> None:
    assert project_embeddings_to_2d([]) == []
    assert project_embeddings_to_2d([[0.1, 0.2, 0.3]]) == [(0.0, 0.0)]


def test_project_embeddings_small_sample_pca_fallback() -> None:
    # 3 vectors in 8 dimensions (triggers n_samples < 4 SVD PCA fallback)
    embeddings = [
        [1.0, 0.0, 0.0, 0.0, 0.5, 0.2, 0.1, 0.0],
        [0.0, 1.0, 0.0, 0.0, 0.1, 0.8, 0.2, 0.0],
        [0.0, 0.0, 1.0, 0.0, 0.0, 0.1, 0.9, 0.0],
    ]
    coords = project_embeddings_to_2d(embeddings)
    assert len(coords) == 3
    for x, y in coords:
        assert -1.0 <= x <= 1.0
        assert -1.0 <= y <= 1.0


def test_project_embeddings_umap_manifold() -> None:
    # 6 vectors in 16 dimensions
    rng = np.random.default_rng(42)
    embeddings = rng.normal(size=(6, 16)).tolist()

    coords = project_embeddings_to_2d(embeddings)
    assert len(coords) == 6
    for x, y in coords:
        assert -1.0 <= x <= 1.0
        assert -1.0 <= y <= 1.0


def test_project_embeddings_umap_exception_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    # Monkeypatch umap.UMAP to raise RuntimeError
    import umap  # type: ignore[import-untyped]

    def mock_umap_fail(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("Simulated UMAP decomposition failure")

    monkeypatch.setattr(umap, "UMAP", mock_umap_fail)

    rng = np.random.default_rng(101)
    embeddings = rng.normal(size=(5, 12)).tolist()

    coords = project_embeddings_to_2d(embeddings)
    assert len(coords) == 5
    for x, y in coords:
        assert -1.0 <= x <= 1.0
        assert -1.0 <= y <= 1.0
