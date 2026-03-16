# Voxelmap-Pointshell Collision Detection in Python

This repository contains a Python-first reimplementation of a voxelmap-pointshell proximity and collision framework inspired by the VPS approach.

The current package provides:

- mesh loading into package-owned NumPy arrays
- integer voxelmap generation
- hierarchical pointshell generation
- proximity queries between a transformed pointshell and a voxelmap
- penalty-based collision detection with force and torque accumulation
- simple `trimesh` scene builders for visualization

The implementation is intentionally centered on NumPy-backed data structures and explicit geometry logic. `trimesh` is used for mesh IO and visualization support, not for the core runtime query pipeline.

## Installation

### Option 1: use the provided conda environment

```bash
conda env create -f conda.yaml
conda activate vps
python -m pip install -r requirements.txt
python -m pip install -e .
```

### Option 2: use a plain virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

### Development tools

The repository includes `pytest`, `flake8`, and `pytype` in `requirements.txt`.

Validation commands:

```bash
pytest -q
flake8 python tests
pytype python
```

## Project Layout

- [python/](/Users/mxagar/nexo/git_repositories/voxel_point_collision_detection/python): package source code
- [tests/](/Users/mxagar/nexo/git_repositories/voxel_point_collision_detection/tests): pytest suite
- [notebooks/](/Users/mxagar/nexo/git_repositories/voxel_point_collision_detection/notebooks): exploratory notebooks and usage examples
- [data/models/](/Users/mxagar/nexo/git_repositories/voxel_point_collision_detection/data/models): sample meshes
- [doc/Sagardia_PhD_Chapter3_Summary.md](/Users/mxagar/nexo/git_repositories/voxel_point_collision_detection/doc/Sagardia_PhD_Chapter3_Summary.md): implementation-oriented technical summary of the reference chapter

## Minor Usage Examples

### Load a mesh

```python
from python.mesh import Mesh

mesh = Mesh.from_file("data/models/monkey.stl")
print(mesh.vertex_count, mesh.triangle_count)
print(mesh.bounds)
```

### Generate a voxelmap and pointshell

```python
from python.generate_pointshell import generate_pointshell
from python.generate_voxelmap import generate_voxelmap

voxelmap = generate_voxelmap(mesh, voxel_size=0.2)
pointshell = generate_pointshell(mesh, voxel_size=0.2, target_spheres=32)

print(voxelmap.shape)
print(pointshell.point_count, pointshell.sphere_count)
```

### Run a proximity query

```python
import numpy as np

from python.proximity_query import proximity_query

transform = np.eye(4)
transform[:3, 3] = np.array([0.1, 0.0, 0.0])

query = proximity_query(
    voxelmap,
    pointshell,
    transform=transform,
    n=5,
    sphere_percentage=0.5,
    point_percentage=0.5,
)

for hit in query.hits:
    print(hit.point_id, hit.sphere_id, hit.signed_distance)
```

### Run a collision query

```python
from python.collision_detection import detect_collision

collision = detect_collision(
    voxelmap,
    pointshell,
    transform=transform,
    stiffness=2.0,
)

print(collision.is_colliding)
print(collision.total_force)
print(collision.total_torque)
```

### Build visualization scenes

```python
from python.viewer import (
    create_mesh_scene,
    create_pointshell_scene,
    create_query_scene,
    create_voxelmap_scene,
)

mesh_scene = create_mesh_scene(mesh)
voxel_scene = create_voxelmap_scene(voxelmap)
pointshell_scene = create_pointshell_scene(pointshell)
query_scene = create_query_scene(voxelmap, pointshell, query, transform=transform)

# In a local interactive session:
# mesh_scene.show()
# voxel_scene.show()
# pointshell_scene.show()
# query_scene.show()
```

## Notebook Example

A small end-to-end notebook is available at [notebooks/usage_examples.ipynb](/Users/mxagar/nexo/git_repositories/voxel_point_collision_detection/notebooks/usage_examples.ipynb). It covers:

- generation
- visualization
- proximity queries
- collision queries
- serialization

## Notes and Limitations

- The current voxelmap stores only the integer layer field.
- Pointshell generation currently uses surface voxel centers and voxel-gradient normals.
- The hierarchical traversal is intentionally simple and compatible with later refinement.
- This is a research/prototyping codebase, not yet a production collision engine.

## References

- McNeely et al., original VPS work
- Sagardia, Chapter 3 reference material summarized in [doc/Sagardia_PhD_Chapter3_Summary.md](/Users/mxagar/nexo/git_repositories/voxel_point_collision_detection/doc/Sagardia_PhD_Chapter3_Summary.md)
- `trimesh`: https://github.com/mikedh/trimesh

## Authorship

Mikel Sagardia, 2024.  
Repository implementation updated with a Python package structure, tests, and examples.
