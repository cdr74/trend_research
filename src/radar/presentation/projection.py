"""Dimensionality reduction and 2D spatial coordinate projection for radar signals."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def _normalize_coordinates(coords: np.ndarray) -> list[tuple[float, float]]:
    """Normalize 2D coordinates into [-1.0, 1.0] range."""
    n_samples = coords.shape[0]
    if n_samples == 0:
        return []
    if n_samples == 1:
        return [(0.0, 0.0)]

    min_x = float(np.min(coords[:, 0]))
    max_x = float(np.max(coords[:, 0]))
    min_y = float(np.min(coords[:, 1]))
    max_y = float(np.max(coords[:, 1]))

    range_x = max_x - min_x
    range_y = max_y - min_y

    normalized: list[tuple[float, float]] = []
    for i in range(n_samples):
        x = float(coords[i, 0])
        y = float(coords[i, 1])

        norm_x = (2.0 * (x - min_x) / range_x - 1.0) if range_x > 1e-6 else 0.0
        norm_y = (2.0 * (y - min_y) / range_y - 1.0) if range_y > 1e-6 else 0.0

        normalized.append((round(norm_x, 4), round(norm_y, 4)))

    return normalized


def _pca_svd_projection(data: np.ndarray) -> np.ndarray:
    """Project high-dimensional vectors to 2D using SVD PCA."""
    mean = np.mean(data, axis=0)
    centered = data - mean

    # SVD decomposition
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    if vt.shape[0] < 2:
        # If fewer than 2 principal dimensions available, pad with zeros
        projection = centered @ vt[:1].T
        return np.hstack([projection, np.zeros((data.shape[0], 1))])

    projection = centered @ vt[:2].T
    return np.asarray(projection, dtype=np.float64)


def project_embeddings_to_2d(
    embeddings: Sequence[Sequence[float]],
    random_state: int = 42,
) -> list[tuple[float, float]]:
    """Project high-dimensional embeddings down to 2D coordinates [-1.0, 1.0].

    Uses UMAP (Uniform Manifold Approximation and Projection) with cosine metric.
    Gracefully falls back to deterministic SVD PCA if sample size < 4 or UMAP
    fails due to degenerate topologies.
    """
    n_samples = len(embeddings)
    if n_samples == 0:
        return []
    if n_samples == 1:
        return [(0.0, 0.0)]

    data = np.asarray(embeddings, dtype=np.float64)

    # If sample size is very small, UMAP cannot construct valid k-NN graphs
    if n_samples < 4:
        pca_coords = _pca_svd_projection(data)
        return _normalize_coordinates(pca_coords)

    try:
        import umap  # type: ignore[import-untyped]

        n_neighbors = min(15, n_samples - 1)
        reducer: Any = umap.UMAP(
            n_components=2,
            n_neighbors=n_neighbors,
            min_dist=0.1,
            metric="cosine",
            random_state=random_state,
            n_jobs=1,
            n_epochs=100,
        )
        umap_coords: np.ndarray = reducer.fit_transform(data)
        return _normalize_coordinates(umap_coords)
    except Exception as e:
        logger.warning("UMAP projection encountered an error, falling back to SVD PCA: %s", e)
        pca_coords = _pca_svd_projection(data)
        return _normalize_coordinates(pca_coords)
