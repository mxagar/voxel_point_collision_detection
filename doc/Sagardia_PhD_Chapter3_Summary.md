# Sagardia PhD Chapter 3 Summary

This note summarizes the ideas from `doc/Sagardia_PhD_Chapter3_2019.pdf` with an emphasis on what is useful for a Python reimplementation in this repository. It is not a literal restatement of the chapter; it is a technical extraction of the core concepts, data structures, and algorithms behind voxelmap-pointshell proximity and collision queries.

Before writing this summary I also reviewed the notebooks in `notebooks/`:

- `numpy_tests.ipynb`: useful for vectorized point/normal transforms, voxel lookup, and force accumulation with NumPy.
- `algorithms_tests.ipynb`: useful for 3D flood-fill ideas that relate to marking inner/outer voxel regions.
- `trimesh_tests.ipynb` and `open3d_tests.ipynb`: useful as mesh IO / sampling / visualization references, not as the core algorithm.

## 1. Main idea

The chapter presents a penalty-based proximity and collision method between two rigid objects using two complementary discrete representations:

- `voxelmap`: a regular 3D grid attached to one object, storing occupancy/layer or distance information.
- `pointshell`: a point cloud attached to the other object, where each point has an inward normal.

At runtime, the pointshell is transformed into the voxelmap frame. Each point is queried against the voxelmap. Positive signed distance means penetration; negative means separation. Colliding point normals are weighted by penetration and accumulated into:

- a total force
- a total torque
- closest features
- optionally a contact manifold

The original motivation is high-rate haptics, but the data structures are also a solid basis for general collision/proximity queries.

## 2. Core offline data structures

### 2.1 Primitive voxelmap

The basic voxelmap is a dense 3D array over the mesh bounding box.

Each voxel stores an integer layer value:

- `0`: surface voxel
- `> 0`: inside the object, increasing with depth
- `< 0`: outside the object, decreasing away from the surface

The chapter first detects surface voxels by triangle-voxel intersection. Then it fills inner and outer layers using a 3D scanline/fill process. In practice, for Python, a flood-fill or BFS/DFS from known exterior seeds is the easiest equivalent.

Useful properties:

- `O(1)` random access for point queries
- fixed spatial resolution
- direct mapping from continuous point coordinates to voxel indices
- layer values can already support a coarse signed distance approximation

### 2.2 Primitive pointshell

The primitive pointshell is built from the voxelized surface, not directly from arbitrary mesh vertices.

Pipeline:

1. Take surface voxel centers.
2. Project each center to the closest triangle.
3. Keep one representative projected point per local region to avoid duplicates that are too close.
4. Compute an inward normal for each point using the gradient of voxel values in a local neighborhood.

This is an important design choice:

- the pointshell is tied to the voxelmap resolution
- point normals are derived from the voxel field, which helps keep normals consistent even if mesh normals are bad

### 2.3 Enhanced voxelmap

The chapter improves the primitive voxelmap with extra per-voxel information. Conceptually, each voxel may store:

- a coarse signed layer value
- a floating-point distance from the voxel center to the surface
- a reference to the closest surface voxel / closest surface sample
- enough local information to evaluate more accurate signed distance functions

This leads to three query styles with different cost/accuracy tradeoffs:

1. `VL`: layered value based distance
2. `VS`: closest surface point based distance
3. `VI`: interpolated distance using neighboring voxel values

For a first Python implementation, `VL` is the best starting point.

### 2.4 Enhanced pointshell: point-sphere hierarchy

The chapter does not stop at a flat point cloud. It organizes points into a multi-resolution hierarchy:

- leaf level: original pointshell points
- upper levels: clusters of nearby points
- each cluster has a representative parent point
- each cluster is bounded by a sphere

This gives a point-sphere tree. It enables:

- broad-phase style pruning
- level-of-detail traversal
- time-budgeted queries
- cheaper distance/collision evaluation than checking every point every frame

This hierarchy is one of the main differences between the classic flat VPS idea and the improved implementation in the chapter.

## 3. Offline generation details worth reusing

### 3.1 Voxelization

The chapter uses triangle-voxel overlap tests and mentions SAT-based checks. For Python we probably do not want to reproduce that exact low-level implementation first.

Practical equivalent options:

- use `trimesh` or `open3d` tools to voxelize a watertight mesh
- or implement a simpler triangle rasterization path if external voxelization becomes a bottleneck

What matters for the later algorithm is that we end up with:

- a regular grid
- a surface mask
- inside/outside labeling
- ideally a signed scalar field

### 3.2 Inner/outer labeling

The chapter describes scanline filling and layered propagation from the surface.

In this repo, `notebooks/algorithms_tests.ipynb` already points in the right direction with a 3D flood-fill prototype. A practical approach is:

1. mark surface voxels
2. flood-fill from the volume boundary to mark exterior
3. unvisited non-surface voxels become interior
4. propagate integer layer depth inward/outward if needed

### 3.3 Surface projection for pointshell points

The PDF derives an exact constrained projection of a voxel center onto a triangle. The important implementation point is not the exact derivation but the behavior:

- each pointshell sample should lie on or very near the true mesh surface
- each sample should have a reliable associated normal
- samples should be roughly uniform at the chosen voxel resolution

For Python, a perfectly acceptable first version is:

- use the center of each surface voxel
- or project it to the nearest point on the mesh if a robust nearest-point API is available

Projected points give smoother distance/force behavior than raw voxel centers.

### 3.4 Normal estimation

The chapter estimates inward normals from the local gradient of the voxel value field. This is very relevant for us because it avoids relying on mesh normals.

A central-difference approximation is enough:

```python
import numpy as np

def estimate_normal(field, i, j, k):
    gx = float(field[i + 1, j, k]) - float(field[i - 1, j, k])
    gy = float(field[i, j + 1, k]) - float(field[i, j - 1, k])
    gz = float(field[i, j, k + 1]) - float(field[i, j, k - 1])
    g = np.array([gx, gy, gz], dtype=np.float32)
    n = g / (np.linalg.norm(g) + 1e-12)
    return n
```

The sign convention matters. We should document whether:

- positive values mean interior penetration
- normals point inward

and keep that convention everywhere.

## 4. Runtime query algorithm

At runtime, we transform the pointshell into the voxelmap reference frame and query the signed distance field pointwise or clusterwise.

### 4.1 Minimal flat version

The simplest useful runtime algorithm is:

1. transform points and normals into voxelmap coordinates
2. convert point coordinates to voxel indices
3. read signed value at each index
4. treat positive values as penetration
5. accumulate force and torque over colliding points
6. also track the closest point pair / minimum separation

This is the direct flat VPS style and matches the spirit of `notebooks/numpy_tests.ipynb`.

Minimal force accumulation:

```python
import numpy as np

def accumulate_wrench(points, normals, signed_distance, center):
    colliding = signed_distance > 0.0
    if not np.any(colliding):
        return np.zeros(3), np.zeros(3)

    p = points[colliding]
    n = normals[colliding]
    d = signed_distance[colliding, None]

    forces = d * n
    total_force = forces.sum(axis=0)
    total_torque = np.cross(p - center, forces).sum(axis=0)
    return total_force, total_torque
```

This ignores stiffness, damping, safety margin, and force scaling, but it captures the core VPS penalty idea.

### 4.2 Signed distance semantics

The chapter uses one scalar query function `V(P)` with this meaning:

- `V(P) < 0`: point is outside, distance to surface
- `V(P) = 0`: point is on the surface
- `V(P) > 0`: point is inside, penetration depth

This same scalar is enough to support both:

- proximity queries
- collision response queries

That unification is one of the strongest ideas in the chapter.

### 4.3 Closest features

The global object-object proximity value is obtained from the point with the highest signed distance:

- if all values are negative, the least negative / closest-to-zero value gives separation
- if some are positive, the maximum value gives penetration

The corresponding pointshell point is a closest feature on the moving object. The associated closest point on the voxelmap surface depends on the chosen field representation:

- approximate from the voxel center and normal for `VL`
- retrieve a precomputed closest surface point for `VS`
- reconstruct more accurately with local interpolation for `VI`

### 4.4 Force and torque

Per-point contribution:

- force direction: point normal
- force magnitude: penetration depth, optionally scaled by stiffness
- torque: moment arm from object center to point crossed with point force

So the total wrench is just the sum of all point contributions.

This is a penalty method, not an exact contact solver. It is simple and fast, but sensitive to resolution, sampling density, and scaling gains.

## 5. Hierarchical traversal

The improved algorithm in the chapter does not always check every point. Instead:

1. start from the root cluster of the point-sphere hierarchy
2. test whether the cluster sphere is close enough to the voxelmap
3. if it is not, prune the whole subtree
4. if it is, descend to children
5. at a critical level, evaluate representative points or leaf points

The traversal is breadth-first and supports time-critical operation.

This is important because it turns the method from a purely flat point query into a scalable proximity engine.

### Practical takeaway for this repo

We should probably implement in stages:

1. flat pointshell + layered voxelmap
2. vectorized NumPy query path
3. closest-feature tracking
4. point-sphere hierarchy
5. optional higher-accuracy distance variants

That order matches both the complexity curve and what the current notebooks already explore.

## 6. Distance variants from the chapter

### 6.1 `VL`: layered value distance

This is the cheapest query. It uses:

- the voxel layer value
- optionally a local correction based on point position inside the voxel

Pros:

- simplest
- robust
- fast
- easiest to store compactly

Cons:

- distance is quantized by voxel resolution
- accuracy near curved surfaces is limited

Recommendation: use this first.

### 6.2 `VS`: closest surface point distance

This augments the field with a nearest-surface sample and computes distance relative to that sample.

Pros:

- often better surface accuracy than pure layers

Cons:

- more memory
- more preprocessing
- quality depends on the nearest-surface assignment

### 6.3 `VI`: interpolated distance

This uses neighboring voxel values to interpolate a smoother signed distance.

Pros:

- best accuracy among the three approaches discussed in the chapter
- smoother contact signal

Cons:

- more expensive query
- more implementation detail
- still only locally accurate up to grid resolution

Recommendation: add only after the flat `VL` pipeline works and tests are stable.

## 7. Resolution and accuracy lessons

The chapter repeatedly emphasizes that voxel size and point density dominate behavior.

Important qualitative results:

- finer pointshells usually matter more than finer voxelmaps for force smoothness
- layered distance can be surprisingly good at moderate resolution
- interpolation improves local distance accuracy but costs more
- hierarchy strongly reduces runtime versus checking all points
- collision forces on thin or non-watertight geometry are problematic

That last point is especially important for this repo:

- watertight meshes are strongly preferred
- voxelmaps can sometimes still represent shapes that are awkward for a pointshell
- thin shells require special care because a penalty method based on penetration volume can underbehave

## 8. Implications for the current repository

The notebooks already suggest a practical NumPy-oriented architecture:

- store pointshell data as an `N x 6` array: `xyz + normal`
- transform points and normals in batch
- compute voxel indices in batch
- fetch signed values with advanced indexing
- accumulate force and torque with vectorized operations

This aligns very well with the chapter.

Two concrete implementation notes:

1. `numpy_tests.ipynb` already contains a useful pattern for batch transforms:

```python
data[:, :3] = data[:, :3] @ R.T + t
data[:, 3:] = data[:, 3:] @ R.T
```

2. The same notebook also sketches the flat collision idea:

- convert point coordinates to discrete voxel indices
- clamp to bounds
- fetch voxel values
- keep positive values as penetration
- sum `penetration * normal`

That is exactly the right baseline.

## 9. Recommended reimplementation roadmap

For this project, the chapter suggests the following staged design.

### Stage A: robust baseline

- Build a dense voxelmap from a watertight mesh.
- Store at least occupancy plus signed layer values.
- Generate a pointshell from surface voxels.
- Estimate inward normals from the voxel field.
- Implement flat vectorized point queries.
- Return:
  - signed distance / penetration
  - colliding point indices
  - total force
  - total torque
  - closest point on pointshell

### Stage B: better distance quality

- Add per-voxel floating distances or nearest-surface samples.
- Implement a smoother `V(P)` call.
- Track closest point on the voxelmap surface too.

### Stage C: performance scaling

- Build a point-sphere hierarchy.
- Add breadth-first traversal and pruning.
- Support a query budget or critical depth.

### Stage D: optional extras

- contact manifold extraction
- time-critical query modes
- adaptive culling of low-information clusters
- force scaling and damping for simulation/haptics

## 10. Suggested simplified mathematical model for our version

A practical simplification of the chapter for this repository is:

- object A: voxelmap with signed scalar field
- object B: pointshell with inward normals
- query:
  - transform pointshell into voxelmap frame
  - sample scalar field at all points
  - `p = max(V(P_i))`
  - if `p <= 0`, report separation
  - else compute penalty wrench from all `V(P_i) > 0`

In pseudocode:

```python
def query(voxelmap, pointshell_world, T_aw):
    points_a, normals_a = transform_pointshell_to_voxelmap(pointshell_world, T_aw)
    signed = voxelmap.sample(points_a)

    proximity = signed.max()
    colliding = signed > 0.0

    if not np.any(colliding):
        i = np.argmax(signed)
        return {
            "signed_distance": float(proximity),
            "closest_point_shell": points_a[i],
            "force": np.zeros(3),
            "torque": np.zeros(3),
        }

    force, torque = accumulate_wrench(
        points_a, normals_a, signed, center=np.zeros(3)
    )
    return {
        "signed_distance": float(proximity),
        "colliding_indices": np.flatnonzero(colliding),
        "force": force,
        "torque": torque,
    }
```

This is not the full chapter algorithm, but it is a clean, testable, and faithful first version.

## 11. What to keep and what to simplify

For our reimplementation, the ideas most worth preserving are:

- voxelmap + pointshell dual representation
- one signed query function for both distance and penetration
- pointshell normals derived from the voxel field
- batch point queries
- eventual point hierarchy for speed

The ideas that can be simplified at first are:

- exact triangle projection derivations
- the full enhanced voxelmap family (`VS`, `VI`)
- time-critical haptic-specific machinery
- force normalization heuristics tied to haptic rendering

## 12. Final takeaway

The chapter’s main contribution is not just “sample points against a voxel grid.” The deeper pattern is:

- precompute discrete geometry structures offline
- encode enough local surface information in them
- use the same signed field for proximity and collision
- trade resolution against speed in a controlled way
- optionally recover scalability with a point-sphere hierarchy

For this repository, the best next step is to implement a clear `VL`-style baseline in Python, validate it against the notebooks and tests, and only then add hierarchy and higher-accuracy distance variants.
