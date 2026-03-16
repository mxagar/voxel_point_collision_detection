"""Tests for the hierarchical pointshell container."""

from __future__ import annotations

import numpy as np

from src.pointshell import Pointshell


def test_pointshell_metadata_is_consistent(synthetic_pointshell: Pointshell) -> None:
    """Spheres, normals, and point ownership should be internally consistent."""

    assert synthetic_pointshell.sphere_count == 2
    assert synthetic_pointshell.point_count == 6
    assert np.array_equal(
        synthetic_pointshell.sphere_ids,
        np.array([0, 0, 0, 1, 1, 1]),
    )
    assert np.allclose(
        np.linalg.norm(synthetic_pointshell.normals, axis=1),
        1.0,
        atol=1e-6,
    )

    sphere = synthetic_pointshell.sphere(0)
    assert sphere.point_start == 0
    assert sphere.point_stop == 3
    assert sphere.lod_boundaries == (0, 1, 3)


def test_pointshell_traversal_by_percentage_and_lod(
    synthetic_pointshell: Pointshell,
) -> None:
    """Traversal helpers should expose coarse-to-fine subsets."""

    coarse = synthetic_pointshell.point_ids_for_sphere(0, percentage=1.0, lod_level=0)
    half = synthetic_pointshell.point_ids_for_sphere(1, percentage=0.5)
    full = synthetic_pointshell.point_ids_for_sphere(1, percentage=1.0)

    assert np.array_equal(coarse, np.array([0]))
    assert np.array_equal(half, np.array([3, 4]))
    assert np.array_equal(full, np.array([3, 4, 5]))


def test_pointshell_ascii_roundtrip(tmp_path, synthetic_pointshell: Pointshell) -> None:
    """ASCII serialization should preserve all pointshell arrays."""

    path = tmp_path / "pointshell.json"
    synthetic_pointshell.to_ascii(path)
    loaded = Pointshell.from_ascii(path)

    assert np.array_equal(loaded.points, synthetic_pointshell.points)
    assert np.array_equal(loaded.sphere_offsets, synthetic_pointshell.sphere_offsets)
    assert loaded.lod_boundaries == synthetic_pointshell.lod_boundaries
