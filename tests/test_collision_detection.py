"""Tests for penalty-based collision detection."""

from __future__ import annotations

import numpy as np

from src.collision_detection import detect_collision


def test_collision_detection_reports_no_collision_when_separated(
    synthetic_voxelmap,
    synthetic_pointshell,
) -> None:
    """Separated configurations should have zero wrench."""

    transform = np.eye(4)
    transform[:3, 3] = np.array([10.0, 0.0, 0.0])
    result = detect_collision(
        synthetic_voxelmap,
        synthetic_pointshell,
        transform=transform,
    )

    assert not result.is_colliding
    assert result.colliding_point_ids.size == 0
    assert np.allclose(result.total_force, 0.0)
    assert np.allclose(result.total_torque, 0.0)


def test_collision_detection_accumulates_penalty_wrench(
    synthetic_voxelmap,
    synthetic_pointshell,
) -> None:
    """Colliding points should contribute force and torque."""

    result = detect_collision(synthetic_voxelmap, synthetic_pointshell, stiffness=2.0)

    assert result.is_colliding
    assert result.colliding_point_ids.size > 0
    assert np.linalg.norm(result.total_force) > 0.0
