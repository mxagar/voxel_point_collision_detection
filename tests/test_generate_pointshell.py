"""Tests for pointshell generation from meshes."""

from __future__ import annotations

import numpy as np

from src.generate_pointshell import generate_pointshell
from src.mesh import Mesh


def test_generate_pointshell_from_box(box_mesh_path) -> None:
    """Generated pointshells should be non-empty and internally consistent."""

    mesh = Mesh.from_file(box_mesh_path)
    pointshell = generate_pointshell(mesh, voxel_size=0.5, target_spheres=8)

    assert pointshell.point_count > 0
    assert pointshell.sphere_count <= 8
    assert np.allclose(np.linalg.norm(pointshell.normals, axis=1), 1.0, atol=1e-6)
    assert np.all(pointshell.sphere_radii >= 0.0)
