"""Generate integer voxelmaps from meshes."""

from __future__ import annotations

from collections import deque

import numpy as np
import trimesh
from numpy.typing import NDArray

from .mesh import Mesh
from .voxelmap import Voxelmap

BoolArray = NDArray[np.bool_]
IntArray = NDArray[np.int32]

_NEIGHBORS = (
    (1, 0, 0),
    (-1, 0, 0),
    (0, 1, 0),
    (0, -1, 0),
    (0, 0, 1),
    (0, 0, -1),
)


def _flood_fill_exterior(surface: BoolArray) -> BoolArray:
    shape = surface.shape
    exterior = np.zeros(shape, dtype=bool)
    queue: deque[tuple[int, int, int]] = deque()

    boundary_mask = np.zeros(shape, dtype=bool)
    boundary_mask[0, :, :] = True
    boundary_mask[-1, :, :] = True
    boundary_mask[:, 0, :] = True
    boundary_mask[:, -1, :] = True
    boundary_mask[:, :, 0] = True
    boundary_mask[:, :, -1] = True

    seeds = np.argwhere(boundary_mask & ~surface)
    for seed in seeds:
        idx = tuple(int(value) for value in seed)
        exterior[idx] = True
        queue.append(idx)

    while queue:
        i, j, k = queue.popleft()
        for di, dj, dk in _NEIGHBORS:
            ni, nj, nk = i + di, j + dj, k + dk
            if (
                0 <= ni < shape[0]
                and 0 <= nj < shape[1]
                and 0 <= nk < shape[2]
                and not surface[ni, nj, nk]
                and not exterior[ni, nj, nk]
            ):
                exterior[ni, nj, nk] = True
                queue.append((ni, nj, nk))

    return exterior


def _bfs_layers(mask: BoolArray, surface: BoolArray) -> IntArray:
    layers = np.full(mask.shape, -1, dtype=np.int32)
    queue: deque[tuple[int, int, int]] = deque()
    seeds = np.argwhere(surface)

    for seed in seeds:
        idx = tuple(int(value) for value in seed)
        layers[idx] = 0
        queue.append(idx)

    while queue:
        i, j, k = queue.popleft()
        current = int(layers[i, j, k])
        for di, dj, dk in _NEIGHBORS:
            ni, nj, nk = i + di, j + dj, k + dk
            if (
                0 <= ni < mask.shape[0]
                and 0 <= nj < mask.shape[1]
                and 0 <= nk < mask.shape[2]
                and mask[ni, nj, nk]
                and layers[ni, nj, nk] == -1
            ):
                layers[ni, nj, nk] = current + 1
                queue.append((ni, nj, nk))

    return layers


def generate_voxelmap(
    mesh: Mesh,
    *,
    voxel_size: float,
    padding: int = 1,
) -> Voxelmap:
    """Generate a layered voxelmap from a mesh.

    The surface occupancy comes from `trimesh` voxelization, while the layer semantics
    and inside/outside propagation are implemented here.
    """

    if voxel_size <= 0.0:
        raise ValueError("voxel_size must be positive")
    if padding < 1:
        raise ValueError("padding must be at least 1")

    trimesh_mesh = trimesh.Trimesh(
        vertices=mesh.vertices.copy(),
        faces=mesh.faces.copy(),
        process=False,
    )
    surface_grid = trimesh_mesh.voxelized(pitch=voxel_size)

    surface = np.asarray(surface_grid.matrix, dtype=bool)
    surface = np.pad(surface, padding, mode="constant", constant_values=False)

    origin = (
        np.asarray(surface_grid.transform[:3, 3], dtype=np.float64)
        - padding * voxel_size
    )
    exterior = _flood_fill_exterior(surface)
    interior = ~surface & ~exterior

    values = np.zeros(surface.shape, dtype=np.int32)
    exterior_layers = _bfs_layers(exterior, surface)
    interior_layers = _bfs_layers(interior, surface)
    values[exterior] = -np.maximum(exterior_layers[exterior], 1)
    values[interior] = np.maximum(interior_layers[interior], 1)

    return Voxelmap(values=values, voxel_size=voxel_size, origin=origin)
