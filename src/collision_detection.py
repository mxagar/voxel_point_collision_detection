"""Penalty-based collision detection built on top of proximity queries."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .pointshell import Pointshell
from .proximity_query import ProximityQueryResult, proximity_query
from .voxelmap import Voxelmap

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


@dataclass(frozen=True)
class CollisionResult:
    """Collision query output."""

    is_colliding: bool
    colliding_point_ids: IntArray
    penetrations: FloatArray
    total_force: FloatArray
    total_torque: FloatArray
    proximity: ProximityQueryResult


def detect_collision(
    voxelmap: Voxelmap,
    pointshell: Pointshell,
    *,
    transform: FloatArray | None = None,
    stiffness: float = 1.0,
    sphere_percentage: float = 1.0,
    point_percentage: float = 1.0,
    lod_level: int | None = None,
) -> CollisionResult:
    """Detect collisions and accumulate a penalty-based wrench."""

    proximity = proximity_query(
        voxelmap,
        pointshell,
        transform=transform,
        n=pointshell.point_count,
        sphere_percentage=sphere_percentage,
        point_percentage=point_percentage,
        lod_level=lod_level,
    )

    mask = proximity.signed_distances > 0.0
    colliding_point_ids = proximity.point_ids[mask]
    penetrations = proximity.signed_distances[mask]
    total_force = np.zeros(3, dtype=np.float64)
    total_torque = np.zeros(3, dtype=np.float64)

    if np.any(mask):
        forces = stiffness * penetrations[:, None] * proximity.normals[mask]
        center = proximity.positions.mean(axis=0)
        total_force = forces.sum(axis=0)
        total_torque = np.cross(proximity.positions[mask] - center, forces).sum(axis=0)

    return CollisionResult(
        is_colliding=bool(np.any(mask)),
        colliding_point_ids=colliding_point_ids,
        penetrations=penetrations,
        total_force=total_force,
        total_torque=total_torque,
        proximity=proximity,
    )
