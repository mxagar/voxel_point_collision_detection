"""Tests for mesh loading and validation."""

from __future__ import annotations

import numpy as np

from src.mesh import Mesh


def test_mesh_loads_and_owns_numpy_arrays(model_path) -> None:
    """Mesh data should be loaded into package-owned NumPy arrays."""

    mesh = Mesh.from_file(model_path)

    assert mesh.vertices.ndim == 2
    assert mesh.vertices.shape[1] == 3
    assert mesh.faces.ndim == 2
    assert mesh.faces.shape[1] == 3
    assert mesh.vertices.dtype == np.float64
    assert mesh.faces.dtype == np.int64
    assert mesh.face_normals.shape == (mesh.triangle_count, 3)
    assert mesh.vertex_normals.shape == (mesh.vertex_count, 3)


def test_mesh_bounds_and_normals_are_valid(sample_mesh: Mesh) -> None:
    """Bounds and normals should be finite and normalized."""

    sample_mesh.validate()

    assert sample_mesh.bounds.shape == (2, 3)
    assert np.all(sample_mesh.bounds[1] >= sample_mesh.bounds[0])
    assert np.allclose(
        np.linalg.norm(sample_mesh.face_normals, axis=1),
        1.0,
        atol=1e-6,
    )
    assert np.allclose(
        np.linalg.norm(sample_mesh.vertex_normals, axis=1),
        1.0,
        atol=1e-6,
    )
