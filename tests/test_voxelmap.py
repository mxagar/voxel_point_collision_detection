"""Tests for the integer voxelmap container."""

from __future__ import annotations

import numpy as np

from src.voxelmap import Voxelmap


def test_coordinate_index_roundtrip(synthetic_voxelmap: Voxelmap) -> None:
    """World coordinates should map to indices and voxel centers consistently."""

    index = synthetic_voxelmap.point_to_index((1.2, 2.2, 3.2))
    assert index == (1, 2, 3)

    center = synthetic_voxelmap.index_to_point(index)
    assert np.allclose(center, np.array([1.5, 2.5, 3.5]))


def test_bounds_and_sampling(synthetic_voxelmap: Voxelmap) -> None:
    """Sampling should return grid values inside and negative values outside."""

    inside = synthetic_voxelmap.sample_points(np.array([[2.5, 2.5, 2.5]]))
    outside = synthetic_voxelmap.sample_points(np.array([[10.0, 10.0, 10.0]]))

    assert inside[0] == 1.0
    assert outside[0] < 0.0
    assert synthetic_voxelmap.contains_index((4, 4, 4))
    assert not synthetic_voxelmap.contains_index((5, 5, 5))


def test_ascii_roundtrip(tmp_path, synthetic_voxelmap: Voxelmap) -> None:
    """ASCII save/load should preserve the voxelmap."""

    path = tmp_path / "voxelmap.json"
    synthetic_voxelmap.to_ascii(path)
    loaded = Voxelmap.from_ascii(path)

    assert loaded.voxel_size == synthetic_voxelmap.voxel_size
    assert np.array_equal(loaded.values, synthetic_voxelmap.values)
    assert np.allclose(loaded.origin, synthetic_voxelmap.origin)
