"""Hierarchical proximity queries between a pointshell and a voxelmap."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .pointshell import Pointshell
from .voxelmap import Voxelmap

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


def _as_transform(transform: FloatArray | None) -> FloatArray:
    if transform is None:
        return np.eye(4, dtype=np.float64)
    matrix = np.asarray(transform, dtype=np.float64)
    if matrix.shape != (4, 4):
        raise ValueError("transform must have shape (4, 4)")
    return matrix


def transform_points(points: FloatArray, transform: FloatArray | None) -> FloatArray:
    """Apply a homogeneous transform to 3D points."""

    matrix = _as_transform(transform)
    rotation = matrix[:3, :3]
    translation = matrix[:3, 3]
    return points @ rotation.T + translation


def transform_normals(normals: FloatArray, transform: FloatArray | None) -> FloatArray:
    """Apply the rotational part of a homogeneous transform to normals."""

    matrix = _as_transform(transform)
    rotation = matrix[:3, :3]
    transformed = normals @ rotation.T
    norms = np.linalg.norm(transformed, axis=1, keepdims=True)
    return transformed / np.where(norms > 0.0, norms, 1.0)


@dataclass(frozen=True)
class ProximityHit:
    """One proximity query hit."""

    point_id: int
    sphere_id: int
    position: FloatArray
    normal: FloatArray
    signed_distance: float


@dataclass(frozen=True)
class ProximityQueryResult:
    """Full proximity query output."""

    hits: tuple[ProximityHit, ...]
    point_ids: IntArray
    sphere_ids: IntArray
    positions: FloatArray
    normals: FloatArray
    signed_distances: FloatArray
    sphere_order: IntArray


def proximity_query(
    voxelmap: Voxelmap,
    pointshell: Pointshell,
    *,
    transform: FloatArray | None = None,
    n: int = 1,
    sphere_percentage: float = 1.0,
    point_percentage: float = 1.0,
    lod_level: int | None = None,
) -> ProximityQueryResult:
    """Return the deepest or closest points from a transformed pointshell.

    Spheres are ranked first using a coarse signed-value estimate sampled at each sphere
    center. Points are then checked sphere by sphere in descending priority order.
    """

    if n <= 0:
        raise ValueError("n must be positive")
    if not 0.0 < sphere_percentage <= 1.0:
        raise ValueError("sphere_percentage must be in (0, 1]")
    if not 0.0 < point_percentage <= 1.0:
        raise ValueError("point_percentage must be in (0, 1]")

    transformed_centers = transform_points(pointshell.sphere_centers, transform)
    center_values = voxelmap.sample_points(transformed_centers)
    priorities = center_values + pointshell.sphere_radii / voxelmap.voxel_size
    sphere_order = np.argsort(priorities)[::-1].astype(np.int64)

    sphere_count = max(1, int(np.ceil(pointshell.sphere_count * sphere_percentage)))
    selected_spheres = sphere_order[:sphere_count]

    point_ids_per_sphere = [
        pointshell.point_ids_for_sphere(
            int(sphere_id),
            percentage=point_percentage,
            lod_level=lod_level,
        )
        for sphere_id in selected_spheres
    ]
    if point_ids_per_sphere:
        point_ids = np.concatenate(point_ids_per_sphere).astype(np.int64, copy=False)
    else:
        point_ids = np.empty(0, dtype=np.int64)

    positions = transform_points(pointshell.points[point_ids], transform)
    normals = transform_normals(pointshell.normals[point_ids], transform)
    signed_distances = voxelmap.sample_points(positions)
    sphere_ids = pointshell.sphere_ids[point_ids]

    order = np.argsort(signed_distances)[::-1]
    top = order[: min(n, point_ids.shape[0])]
    hits = tuple(
        ProximityHit(
            point_id=int(point_ids[idx]),
            sphere_id=int(sphere_ids[idx]),
            position=positions[idx].copy(),
            normal=normals[idx].copy(),
            signed_distance=float(signed_distances[idx]),
        )
        for idx in top
    )

    return ProximityQueryResult(
        hits=hits,
        point_ids=point_ids,
        sphere_ids=sphere_ids,
        positions=positions,
        normals=normals,
        signed_distances=signed_distances,
        sphere_order=sphere_order,
    )
