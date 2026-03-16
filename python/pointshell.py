"""Hierarchical pointshell data container."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


def _normalize_rows(vectors: FloatArray) -> FloatArray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    safe = np.where(norms > 0.0, norms, 1.0)
    return vectors / safe


@dataclass(frozen=True)
class Sphere:
    """Metadata for one pointshell sphere/patch."""

    sphere_id: int
    point_start: int
    point_stop: int
    center: FloatArray
    radius: float
    lod_boundaries: tuple[int, ...]

    @property
    def point_count(self) -> int:
        """Number of points in the sphere."""

        return self.point_stop - self.point_start


@dataclass(frozen=True)
class Pointshell:
    """Hierarchical surface samples grouped into disjoint spheres."""

    points: FloatArray
    normals: FloatArray
    sphere_ids: IntArray
    sphere_offsets: IntArray
    sphere_centers: FloatArray
    sphere_radii: FloatArray
    lod_boundaries: tuple[tuple[int, ...], ...]

    def __post_init__(self) -> None:
        points = np.asarray(self.points, dtype=np.float64)
        normals = _normalize_rows(np.asarray(self.normals, dtype=np.float64))
        sphere_ids = np.asarray(self.sphere_ids, dtype=np.int64)
        sphere_offsets = np.asarray(self.sphere_offsets, dtype=np.int64)
        sphere_centers = np.asarray(self.sphere_centers, dtype=np.float64)
        sphere_radii = np.asarray(self.sphere_radii, dtype=np.float64)

        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError("points must have shape (n_points, 3)")
        if normals.shape != points.shape:
            raise ValueError("normals must have the same shape as points")
        if sphere_ids.shape != (points.shape[0],):
            raise ValueError("sphere_ids must have shape (n_points,)")
        if sphere_offsets.ndim != 1 or sphere_offsets[0] != 0:
            raise ValueError("sphere_offsets must start with 0")
        if sphere_offsets[-1] != points.shape[0]:
            raise ValueError("sphere_offsets must end at n_points")
        if sphere_centers.shape != (len(sphere_offsets) - 1, 3):
            raise ValueError("sphere_centers has inconsistent shape")
        if sphere_radii.shape != (len(sphere_offsets) - 1,):
            raise ValueError("sphere_radii has inconsistent shape")
        if len(self.lod_boundaries) != len(sphere_offsets) - 1:
            raise ValueError("lod_boundaries must match number of spheres")

        expected_sphere_ids = np.repeat(
            np.arange(len(sphere_offsets) - 1, dtype=np.int64),
            np.diff(sphere_offsets),
        )
        if not np.array_equal(sphere_ids, expected_sphere_ids):
            raise ValueError(
                "points must be ordered by sphere and sphere_ids must match offsets"
            )

        for sphere_id, boundaries in enumerate(self.lod_boundaries):
            start = int(sphere_offsets[sphere_id])
            stop = int(sphere_offsets[sphere_id + 1])
            if not boundaries:
                raise ValueError("each sphere must define at least one LOD boundary")
            if boundaries[0] != start or boundaries[-1] != stop:
                raise ValueError("lod boundaries must start/stop at sphere limits")
            if list(boundaries) != sorted(boundaries):
                raise ValueError("lod boundaries must be sorted")

        object.__setattr__(self, "points", points)
        object.__setattr__(self, "normals", normals)
        object.__setattr__(self, "sphere_ids", sphere_ids)
        object.__setattr__(self, "sphere_offsets", sphere_offsets)
        object.__setattr__(self, "sphere_centers", sphere_centers)
        object.__setattr__(self, "sphere_radii", sphere_radii)

    @property
    def point_count(self) -> int:
        """Total number of points."""

        return int(self.points.shape[0])

    @property
    def sphere_count(self) -> int:
        """Total number of spheres."""

        return int(self.sphere_offsets.shape[0] - 1)

    @property
    def centroid(self) -> FloatArray:
        """Mean point position."""

        return self.points.mean(axis=0)

    def sphere(self, sphere_id: int) -> Sphere:
        """Return metadata for one sphere."""

        start = int(self.sphere_offsets[sphere_id])
        stop = int(self.sphere_offsets[sphere_id + 1])
        return Sphere(
            sphere_id=sphere_id,
            point_start=start,
            point_stop=stop,
            center=self.sphere_centers[sphere_id],
            radius=float(self.sphere_radii[sphere_id]),
            lod_boundaries=self.lod_boundaries[sphere_id],
        )

    def iter_spheres(self) -> tuple[Sphere, ...]:
        """Return all sphere descriptors."""

        return tuple(self.sphere(sphere_id) for sphere_id in range(self.sphere_count))

    def point_ids_for_sphere(
        self,
        sphere_id: int,
        *,
        percentage: float = 1.0,
        lod_level: int | None = None,
    ) -> IntArray:
        """Return point ids for one sphere.

        The returned subset can be truncated by LOD level and traversal percentage.
        """

        if not 0.0 < percentage <= 1.0:
            raise ValueError("percentage must be in (0, 1]")

        sphere = self.sphere(sphere_id)
        start, stop = sphere.point_start, sphere.point_stop
        limit = stop
        if lod_level is not None:
            boundaries = sphere.lod_boundaries
            if lod_level < 0 or lod_level >= len(boundaries) - 1:
                raise ValueError("lod_level outside available boundaries")
            limit = boundaries[lod_level + 1]

        count = limit - start
        selected = max(1, int(np.ceil(count * percentage)))
        return np.arange(start, start + selected, dtype=np.int64)

    def to_ascii(self, path: str | Path) -> None:
        """Serialize the pointshell to a plain-text JSON file."""

        payload = {
            "format": "pointshell-ascii-v1",
            "points": self.points.tolist(),
            "normals": self.normals.tolist(),
            "sphere_ids": self.sphere_ids.tolist(),
            "sphere_offsets": self.sphere_offsets.tolist(),
            "sphere_centers": self.sphere_centers.tolist(),
            "sphere_radii": self.sphere_radii.tolist(),
            "lod_boundaries": [list(boundaries) for boundaries in self.lod_boundaries],
        }
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def from_ascii(cls, path: str | Path) -> "Pointshell":
        """Load a pointshell from a plain-text JSON file."""

        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("format") != "pointshell-ascii-v1":
            raise ValueError("unsupported pointshell format")
        return cls(
            points=np.asarray(payload["points"], dtype=np.float64),
            normals=np.asarray(payload["normals"], dtype=np.float64),
            sphere_ids=np.asarray(payload["sphere_ids"], dtype=np.int64),
            sphere_offsets=np.asarray(payload["sphere_offsets"], dtype=np.int64),
            sphere_centers=np.asarray(payload["sphere_centers"], dtype=np.float64),
            sphere_radii=np.asarray(payload["sphere_radii"], dtype=np.float64),
            lod_boundaries=tuple(
                tuple(int(value) for value in boundaries)
                for boundaries in payload["lod_boundaries"]
            ),
        )
