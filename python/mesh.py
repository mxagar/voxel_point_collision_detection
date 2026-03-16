"""Mesh container backed by NumPy arrays controlled by this package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import trimesh
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


def _normalize_rows(vectors: FloatArray) -> FloatArray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    safe = np.where(norms > 0.0, norms, 1.0)
    return vectors / safe


def _compute_face_normals(vertices: FloatArray, faces: IntArray) -> FloatArray:
    triangles = vertices[faces]
    edge_a = triangles[:, 1] - triangles[:, 0]
    edge_b = triangles[:, 2] - triangles[:, 0]
    normals = np.cross(edge_a, edge_b)
    return _normalize_rows(normals.astype(np.float64, copy=False))


def _compute_vertex_normals(
    vertices: FloatArray,
    faces: IntArray,
    face_normals: FloatArray,
) -> FloatArray:
    normals = np.zeros_like(vertices)
    for corner in range(3):
        np.add.at(normals, faces[:, corner], face_normals)
    return _normalize_rows(normals)


@dataclass(frozen=True)
class Mesh:
    """Triangle mesh representation owned by this package."""

    vertices: FloatArray
    faces: IntArray
    face_normals: FloatArray
    vertex_normals: FloatArray
    bounds: FloatArray
    centroid: FloatArray
    source_path: str | None = None

    def __post_init__(self) -> None:
        vertices = np.asarray(self.vertices, dtype=np.float64)
        faces = np.asarray(self.faces, dtype=np.int64)
        face_normals = np.asarray(self.face_normals, dtype=np.float64)
        vertex_normals = np.asarray(self.vertex_normals, dtype=np.float64)
        bounds = np.asarray(self.bounds, dtype=np.float64)
        centroid = np.asarray(self.centroid, dtype=np.float64)

        if vertices.ndim != 2 or vertices.shape[1] != 3:
            raise ValueError("vertices must have shape (n_vertices, 3)")
        if faces.ndim != 2 or faces.shape[1] != 3:
            raise ValueError("faces must have shape (n_faces, 3)")
        if face_normals.shape != (faces.shape[0], 3):
            raise ValueError("face_normals must have shape (n_faces, 3)")
        if vertex_normals.shape != vertices.shape:
            raise ValueError("vertex_normals must have shape (n_vertices, 3)")
        if bounds.shape != (2, 3):
            raise ValueError("bounds must have shape (2, 3)")
        if centroid.shape != (3,):
            raise ValueError("centroid must have shape (3,)")
        if faces.size and (faces.min() < 0 or faces.max() >= vertices.shape[0]):
            raise ValueError("faces contain invalid vertex indices")

        object.__setattr__(self, "vertices", vertices)
        object.__setattr__(self, "faces", faces)
        object.__setattr__(self, "face_normals", _normalize_rows(face_normals))
        object.__setattr__(self, "vertex_normals", _normalize_rows(vertex_normals))
        object.__setattr__(self, "bounds", bounds)
        object.__setattr__(self, "centroid", centroid)

    @classmethod
    def from_file(cls, path: str | Path) -> "Mesh":
        """Load a mesh from disk and convert it to package-owned arrays."""

        loaded = trimesh.load(Path(path), force="mesh")
        if not isinstance(loaded, trimesh.Trimesh):
            raise ValueError(f"expected a single mesh in {path!s}")

        loaded = loaded.copy()
        if loaded.faces is None or loaded.vertices is None:
            raise ValueError(f"mesh at {path!s} is missing vertices or faces")

        vertices = np.asarray(loaded.vertices, dtype=np.float64).copy()
        faces = np.asarray(loaded.faces, dtype=np.int64).copy()
        face_normals = _compute_face_normals(vertices, faces)

        if (
            getattr(loaded, "vertex_normals", None) is not None
            and len(loaded.vertex_normals) == len(vertices)
        ):
            vertex_normals = _normalize_rows(
                np.asarray(loaded.vertex_normals, dtype=np.float64).copy()
            )
        else:
            vertex_normals = _compute_vertex_normals(vertices, faces, face_normals)

        bounds = np.vstack([vertices.min(axis=0), vertices.max(axis=0)])
        centroid = vertices.mean(axis=0)
        return cls(
            vertices=vertices,
            faces=faces,
            face_normals=face_normals,
            vertex_normals=vertex_normals,
            bounds=bounds,
            centroid=centroid,
            source_path=str(path),
        )

    @property
    def triangle_count(self) -> int:
        """Return the number of triangular faces."""

        return int(self.faces.shape[0])

    @property
    def vertex_count(self) -> int:
        """Return the number of vertices."""

        return int(self.vertices.shape[0])

    @property
    def extents(self) -> FloatArray:
        """Axis-aligned bounding box size."""

        return self.bounds[1] - self.bounds[0]

    def triangles(self) -> FloatArray:
        """Return the face vertex positions with shape (n_faces, 3, 3)."""

        return self.vertices[self.faces]

    def validate(self) -> None:
        """Raise if the mesh contains invalid values."""

        if not np.isfinite(self.vertices).all():
            raise ValueError("vertices contain non-finite values")
        if not np.isfinite(self.face_normals).all():
            raise ValueError("face_normals contain non-finite values")
        if not np.isfinite(self.vertex_normals).all():
            raise ValueError("vertex_normals contain non-finite values")
