"""Dense integer voxelmap with coordinate conversion helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int32]
IndexArray = NDArray[np.int64]


@dataclass(frozen=True)
class Voxelmap:
    """Regular dense voxel grid storing integer layer values."""

    values: IntArray
    voxel_size: float
    origin: FloatArray
    axis_order: tuple[str, str, str] = ("x", "y", "z")

    def __post_init__(self) -> None:
        values = np.asarray(self.values, dtype=np.int32)
        origin = np.asarray(self.origin, dtype=np.float64)
        if values.ndim != 3:
            raise ValueError("values must have shape (nx, ny, nz)")
        if origin.shape != (3,):
            raise ValueError("origin must have shape (3,)")
        if self.voxel_size <= 0.0:
            raise ValueError("voxel_size must be positive")
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "origin", origin)

    @property
    def shape(self) -> tuple[int, int, int]:
        """Grid shape as (nx, ny, nz)."""

        return tuple(int(dim) for dim in self.values.shape)

    @property
    def bounds(self) -> FloatArray:
        """Axis-aligned bounds of the grid in world coordinates."""

        max_corner = (
            self.origin
            + np.array(self.shape, dtype=np.float64) * self.voxel_size
        )
        return np.vstack([self.origin, max_corner])

    @property
    def center(self) -> FloatArray:
        """Center of the voxelmap bounding box."""

        bounds = self.bounds
        return 0.5 * (bounds[0] + bounds[1])

    def contains_index(self, index: tuple[int, int, int] | IndexArray) -> bool:
        """Return whether an index lies inside the grid."""

        idx = np.asarray(index, dtype=np.int64)
        return bool(np.all(idx >= 0) and np.all(idx < np.asarray(self.shape)))

    def contains_point(self, point: FloatArray | tuple[float, float, float]) -> bool:
        """Return whether a point lies inside the voxelmap bounds."""

        p = np.asarray(point, dtype=np.float64)
        return bool(np.all(p >= self.bounds[0]) and np.all(p < self.bounds[1]))

    def point_to_index(
        self,
        point: FloatArray | tuple[float, float, float],
    ) -> tuple[int, int, int]:
        """Convert a point to the containing voxel index."""

        p = np.asarray(point, dtype=np.float64)
        idx = np.floor((p - self.origin) / self.voxel_size).astype(np.int64)
        return tuple(int(value) for value in idx)

    def index_to_point(self, index: tuple[int, int, int] | IndexArray) -> FloatArray:
        """Return the voxel-center world coordinate for a grid index."""

        idx = np.asarray(index, dtype=np.float64)
        return self.origin + (idx + 0.5) * self.voxel_size

    def get_value(self, index: tuple[int, int, int] | IndexArray) -> int:
        """Return one voxel value."""

        idx = np.asarray(index, dtype=np.int64)
        if not self.contains_index(idx):
            raise IndexError(
                f"index {tuple(idx)} outside voxelmap with shape {self.shape}"
            )
        return int(self.values[tuple(idx)])

    def sample_points(
        self,
        points: FloatArray,
        *,
        outside_offset: float = 1.0,
    ) -> FloatArray:
        """Sample signed values for a batch of points.

        Points outside the voxelmap are assigned a negative value based on how far
        they lie from the bounding box measured in voxel-size units, keeping the
        sign convention consistent with the layer field.
        """

        pts = np.asarray(points, dtype=np.float64)
        if pts.ndim != 2 or pts.shape[1] != 3:
            raise ValueError("points must have shape (n_points, 3)")

        indices = np.floor((pts - self.origin) / self.voxel_size).astype(np.int64)
        valid = np.all(indices >= 0, axis=1) & np.all(
            indices < np.asarray(self.shape, dtype=np.int64),
            axis=1,
        )

        sampled = np.empty(pts.shape[0], dtype=np.float64)
        if np.any(valid):
            valid_indices = indices[valid]
            sampled[valid] = self.values[
                valid_indices[:, 0],
                valid_indices[:, 1],
                valid_indices[:, 2],
            ].astype(np.float64)

        if np.any(~valid):
            bounds = self.bounds
            delta_min = np.maximum(bounds[0] - pts[~valid], 0.0)
            delta_max = np.maximum(pts[~valid] - bounds[1], 0.0)
            distance = np.linalg.norm(delta_min + delta_max, axis=1) / self.voxel_size
            sampled[~valid] = -(outside_offset + distance)

        return sampled

    def to_ascii(self, path: str | Path) -> None:
        """Serialize the voxelmap to a plain-text JSON file."""

        payload = {
            "format": "voxelmap-ascii-v1",
            "voxel_size": float(self.voxel_size),
            "origin": self.origin.tolist(),
            "shape": list(self.shape),
            "axis_order": list(self.axis_order),
            "dtype": str(self.values.dtype),
            "values": self.values.tolist(),
        }
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def from_ascii(cls, path: str | Path) -> "Voxelmap":
        """Load a voxelmap from a plain-text JSON file."""

        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("format") != "voxelmap-ascii-v1":
            raise ValueError("unsupported voxelmap format")
        return cls(
            values=np.asarray(payload["values"], dtype=np.int32),
            voxel_size=float(payload["voxel_size"]),
            origin=np.asarray(payload["origin"], dtype=np.float64),
            axis_order=tuple(payload["axis_order"]),
        )
