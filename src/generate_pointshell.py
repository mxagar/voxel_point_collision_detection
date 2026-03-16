"""Generate hierarchical pointshells from meshes."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .generate_voxelmap import generate_voxelmap
from .mesh import Mesh
from .pointshell import Pointshell

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


def _estimate_surface_normals(
    points: FloatArray,
    voxelmap_values: NDArray[np.int32],
) -> FloatArray:
    normals = np.zeros_like(points)
    for idx, point in enumerate(points):
        i, j, k = point
        i = int(i)
        j = int(j)
        k = int(k)
        gx = float(
            voxelmap_values[min(i + 1, voxelmap_values.shape[0] - 1), j, k]
        ) - float(voxelmap_values[max(i - 1, 0), j, k])
        gy = float(
            voxelmap_values[i, min(j + 1, voxelmap_values.shape[1] - 1), k]
        ) - float(voxelmap_values[i, max(j - 1, 0), k])
        gz = float(
            voxelmap_values[i, j, min(k + 1, voxelmap_values.shape[2] - 1)]
        ) - float(voxelmap_values[i, j, max(k - 1, 0)])
        normals[idx] = np.array([gx, gy, gz], dtype=np.float64)
    norms = np.linalg.norm(normals, axis=1, keepdims=True)
    return normals / np.where(norms > 0.0, norms, 1.0)


def _cluster_points(points: FloatArray, target_spheres: int) -> IntArray:
    point_count = points.shape[0]
    sphere_count = max(1, min(target_spheres, point_count))
    order = np.lexsort((points[:, 2], points[:, 1], points[:, 0]))
    cluster_ids = np.empty(point_count, dtype=np.int64)
    chunk = int(np.ceil(point_count / sphere_count))
    for cluster_id in range(sphere_count):
        start = cluster_id * chunk
        stop = min((cluster_id + 1) * chunk, point_count)
        cluster_ids[order[start:stop]] = cluster_id
    return cluster_ids


def _lod_boundaries_for_count(start: int, stop: int) -> tuple[int, ...]:
    count = stop - start
    if count <= 1:
        return (start, stop)
    coarse = start + 1
    medium = start + max(1, int(np.ceil(count * 0.5)))
    medium = min(max(coarse, medium), stop)
    boundaries = [start, coarse]
    if medium not in boundaries:
        boundaries.append(medium)
    if stop not in boundaries:
        boundaries.append(stop)
    return tuple(boundaries)


def generate_pointshell(
    mesh: Mesh,
    *,
    voxel_size: float,
    target_spheres: int = 256,
) -> Pointshell:
    """Generate a pointshell using surface voxel centers and voxel-field normals."""

    voxelmap = generate_voxelmap(mesh, voxel_size=voxel_size)
    surface_indices = np.argwhere(voxelmap.values == 0)
    if surface_indices.size == 0:
        raise ValueError("voxelmap has no surface voxels")

    points = np.array(
        [voxelmap.index_to_point(tuple(index)) for index in surface_indices],
        dtype=np.float64,
    )
    normals = _estimate_surface_normals(
        surface_indices.astype(np.float64),
        voxelmap.values,
    )

    cluster_ids = _cluster_points(points, target_spheres=target_spheres)
    order = np.lexsort((points[:, 2], points[:, 1], points[:, 0], cluster_ids))
    points = points[order]
    normals = normals[order]
    cluster_ids = cluster_ids[order]

    unique_ids, counts = np.unique(cluster_ids, return_counts=True)
    sphere_offsets = np.concatenate([[0], np.cumsum(counts)]).astype(np.int64)
    sphere_centers = np.zeros((len(unique_ids), 3), dtype=np.float64)
    sphere_radii = np.zeros(len(unique_ids), dtype=np.float64)
    lod_boundaries: list[tuple[int, ...]] = []

    for sphere_id, (start, stop) in enumerate(
        zip(sphere_offsets[:-1], sphere_offsets[1:])
    ):
        sphere_points = points[start:stop]
        center = sphere_points.mean(axis=0)
        sphere_centers[sphere_id] = center
        sphere_radii[sphere_id] = np.linalg.norm(
            sphere_points - center,
            axis=1,
        ).max()
        lod_boundaries.append(_lod_boundaries_for_count(int(start), int(stop)))

    sphere_ids = np.repeat(np.arange(len(unique_ids), dtype=np.int64), counts)
    return Pointshell(
        points=points,
        normals=normals,
        sphere_ids=sphere_ids,
        sphere_offsets=sphere_offsets,
        sphere_centers=sphere_centers,
        sphere_radii=sphere_radii,
        lod_boundaries=tuple(lod_boundaries),
    )
