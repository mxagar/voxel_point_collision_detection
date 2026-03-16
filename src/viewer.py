"""Visualization helpers built around trimesh scenes."""

from __future__ import annotations

import numpy as np
import trimesh
from numpy.typing import NDArray

from .mesh import Mesh
from .pointshell import Pointshell
from .proximity_query import ProximityQueryResult, transform_points
from .voxelmap import Voxelmap

FloatArray = NDArray[np.float64]


def create_mesh_scene(mesh: Mesh) -> trimesh.Scene:
    """Create a trimesh scene for a triangle mesh."""

    tri_mesh = trimesh.Trimesh(
        vertices=mesh.vertices.copy(),
        faces=mesh.faces.copy(),
        process=False,
    )
    scene = trimesh.Scene()
    scene.add_geometry(tri_mesh, geom_name="mesh")
    return scene


def create_voxelmap_scene(
    voxelmap: Voxelmap,
    *,
    mode: str = "surface",
) -> trimesh.Scene:
    """Create a scene showing selected voxel centers as a point cloud."""

    if mode == "surface":
        indices = np.argwhere(voxelmap.values == 0)
        color = np.array([220, 80, 80, 255], dtype=np.uint8)
    elif mode == "interior":
        indices = np.argwhere(voxelmap.values > 0)
        color = np.array([80, 180, 80, 255], dtype=np.uint8)
    elif mode == "all":
        indices = np.argwhere(voxelmap.values != 0)
        color = np.array([80, 80, 220, 255], dtype=np.uint8)
    else:
        raise ValueError("mode must be 'surface', 'interior', or 'all'")

    points = np.array(
        [voxelmap.index_to_point(index) for index in indices],
        dtype=np.float64,
    )
    cloud = trimesh.points.PointCloud(points, colors=np.tile(color, (len(points), 1)))
    scene = trimesh.Scene()
    scene.add_geometry(cloud, geom_name="voxelmap")
    return scene


def create_pointshell_scene(pointshell: Pointshell) -> trimesh.Scene:
    """Create a scene for a pointshell."""

    colors = np.zeros((pointshell.point_count, 4), dtype=np.uint8)
    colors[:, 0] = 255
    colors[:, 3] = 255
    cloud = trimesh.points.PointCloud(pointshell.points.copy(), colors=colors)
    scene = trimesh.Scene()
    scene.add_geometry(cloud, geom_name="pointshell")
    return scene


def create_query_scene(
    voxelmap: Voxelmap,
    pointshell: Pointshell,
    query: ProximityQueryResult,
    *,
    transform: FloatArray | None = None,
) -> trimesh.Scene:
    """Create a scene combining voxelmap, transformed pointshell, and top hits."""

    scene = create_voxelmap_scene(voxelmap, mode="surface")

    transformed_points = transform_points(pointshell.points, transform)
    shell_cloud = trimesh.points.PointCloud(
        transformed_points,
        colors=np.tile(
            np.array([50, 120, 255, 255], dtype=np.uint8),
            (pointshell.point_count, 1),
        ),
    )
    hit_points = np.array([hit.position for hit in query.hits], dtype=np.float64)
    hit_cloud = trimesh.points.PointCloud(
        hit_points,
        colors=np.tile(
            np.array([255, 215, 0, 255], dtype=np.uint8),
            (len(hit_points), 1),
        ),
    )

    scene.add_geometry(shell_cloud, geom_name="transformed_pointshell")
    if len(hit_points):
        scene.add_geometry(hit_cloud, geom_name="query_hits")
    return scene
