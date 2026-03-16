"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import trimesh

from src.mesh import Mesh
from src.pointshell import Pointshell
from src.voxelmap import Voxelmap


@pytest.fixture()
def model_path() -> Path:
    """Path to a sample mesh bundled with the repository."""

    return Path("data/models/monkey.stl")


@pytest.fixture()
def box_mesh_path(tmp_path: Path) -> Path:
    """Write a deterministic watertight box mesh to disk."""

    path = tmp_path / "box.stl"
    mesh = trimesh.creation.box(extents=(2.0, 2.0, 2.0))
    mesh.export(path)
    return path


@pytest.fixture()
def sample_mesh(model_path: Path) -> Mesh:
    """Loaded sample mesh."""

    return Mesh.from_file(model_path)


@pytest.fixture()
def synthetic_voxelmap() -> Voxelmap:
    """Simple layered voxelmap for algorithm tests."""

    values = np.full((5, 5, 5), -2, dtype=np.int32)
    values[1:4, 1:4, 1:4] = 1
    values[1, 1:4, 1:4] = 0
    values[3, 1:4, 1:4] = 0
    values[1:4, 1, 1:4] = 0
    values[1:4, 3, 1:4] = 0
    values[1:4, 1:4, 1] = 0
    values[1:4, 1:4, 3] = 0
    return Voxelmap(values=values, voxel_size=1.0, origin=np.array([0.0, 0.0, 0.0]))


@pytest.fixture()
def synthetic_pointshell() -> Pointshell:
    """Small pointshell with two spheres and explicit LOD boundaries."""

    points = np.array(
        [
            [2.2, 2.2, 2.2],
            [2.6, 2.2, 2.2],
            [2.2, 2.6, 2.2],
            [4.2, 4.2, 4.2],
            [4.2, 4.2, 4.6],
            [4.2, 4.6, 4.2],
        ],
        dtype=np.float64,
    )
    normals = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [-1.0, 0.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, -1.0],
        ],
        dtype=np.float64,
    )
    sphere_offsets = np.array([0, 3, 6], dtype=np.int64)
    sphere_centers = np.array(
        [
            points[0:3].mean(axis=0),
            points[3:6].mean(axis=0),
        ]
    )
    sphere_radii = np.array(
        [
            np.linalg.norm(points[0:3] - sphere_centers[0], axis=1).max(),
            np.linalg.norm(points[3:6] - sphere_centers[1], axis=1).max(),
        ]
    )
    return Pointshell(
        points=points,
        normals=normals,
        sphere_ids=np.array([0, 0, 0, 1, 1, 1], dtype=np.int64),
        sphere_offsets=sphere_offsets,
        sphere_centers=sphere_centers,
        sphere_radii=sphere_radii,
        lod_boundaries=((0, 1, 3), (3, 4, 6)),
    )
