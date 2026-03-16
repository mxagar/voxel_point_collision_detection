"""Tests for voxelmap generation from meshes."""

from __future__ import annotations

import numpy as np

from python.generate_voxelmap import generate_voxelmap
from python.mesh import Mesh


def test_generate_voxelmap_from_box(box_mesh_path) -> None:
    """Generated voxelmaps should contain surface and interior layers."""

    mesh = Mesh.from_file(box_mesh_path)
    voxelmap = generate_voxelmap(mesh, voxel_size=0.5)

    assert voxelmap.values.ndim == 3
    assert np.any(voxelmap.values == 0)
    assert np.any(voxelmap.values > 0)
    assert np.any(voxelmap.values < 0)
