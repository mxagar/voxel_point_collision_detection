"""Tests for hierarchical proximity queries."""

from __future__ import annotations

import numpy as np

from python.proximity_query import proximity_query


def test_proximity_query_returns_deepest_points(
    synthetic_voxelmap,
    synthetic_pointshell,
) -> None:
    """Hits should be sorted from deepest to least deep."""

    result = proximity_query(synthetic_voxelmap, synthetic_pointshell, n=2)

    assert len(result.hits) == 2
    assert result.hits[0].signed_distance >= result.hits[1].signed_distance
    assert result.hits[0].signed_distance > 0.0


def test_proximity_query_respects_transform(
    synthetic_voxelmap,
    synthetic_pointshell,
) -> None:
    """Moving the pointshell away should make the query non-colliding."""

    transform = np.eye(4)
    transform[:3, 3] = np.array([10.0, 0.0, 0.0])
    result = proximity_query(
        synthetic_voxelmap,
        synthetic_pointshell,
        transform=transform,
        n=1,
    )

    assert len(result.hits) == 1
    assert result.hits[0].signed_distance < 0.0
