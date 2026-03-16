"""Tests for scene-building visualization helpers."""

from __future__ import annotations

from src.proximity_query import proximity_query
from src.viewer import (
    create_mesh_scene,
    create_pointshell_scene,
    create_query_scene,
    create_voxelmap_scene,
)


def test_viewer_creates_scenes(
    sample_mesh,
    synthetic_voxelmap,
    synthetic_pointshell,
) -> None:
    """Viewer helpers should return trimesh scenes with geometry."""

    mesh_scene = create_mesh_scene(sample_mesh)
    voxel_scene = create_voxelmap_scene(synthetic_voxelmap)
    pointshell_scene = create_pointshell_scene(synthetic_pointshell)
    query = proximity_query(synthetic_voxelmap, synthetic_pointshell, n=2)
    query_scene = create_query_scene(synthetic_voxelmap, synthetic_pointshell, query)

    assert len(mesh_scene.geometry) == 1
    assert len(voxel_scene.geometry) == 1
    assert len(pointshell_scene.geometry) == 1
    assert len(query_scene.geometry) >= 2
