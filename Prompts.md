# Prompts

## 1

Show me a tree of all the files you see in the project folder.

### Output

```
voxel_point_collision_detection
├── .vscode
│   └── settings.json
├── admin
│   └── README.md
├── assets
│   └── README.md
├── cpp
│   ├── CMakeLists.txt
│   ├── CollisionDetection.cpp
│   ├── CollisionDetection.h
│   ├── Mesh.cpp
│   ├── Mesh.h
│   ├── Pointshell.cpp
│   ├── Pointshell.h
│   ├── ProximityQuery.cpp
│   ├── ProximityQuery.h
│   ├── README.md
│   ├── Viewer.cpp
│   ├── Viewer.h
│   ├── Voxelmap.cpp
│   └── Voxelmap.h
├── data
│   ├── models
│   │   ├── monkey.mtl
│   │   ├── monkey.obj
│   │   ├── monkey.ply
│   │   └── monkey.stl
│   ├── .DS_Store
│   └── README.md
├── doc
│   ├── README.md
│   └── Sagardia_PhD_Chapter3_2019.pdf
├── notebooks
│   ├── algorithms_tests.ipynb
│   ├── numpy_tests.ipynb
│   ├── open3d_tests.ipynb
│   └── trimesh_tests.ipynb
├── python
│   ├── __init__.py
│   ├── collision_detection.py
│   ├── generate_pointshell.py
│   ├── generate_voxelmap.py
│   ├── mesh.py
│   ├── pointshell.py
│   ├── proximity_query.py
│   ├── viewer.py
│   └── voxelmap.py
├── tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_collision_detection.py
│   ├── test_generate_pointshell.py
│   ├── test_generate_voxelmap.py
│   ├── test_mesh.py
│   ├── test_pointshell.py
│   ├── test_proximity_query.py
│   ├── test_viewer.py
│   └── test_voxelmap.py
├── .DS_Store
├── .gitconfig
├── .gitignore
├── Prompts.md
├── pyproject.toml
├── README.md
├── requirements.in
└── requirements.txt

```

## 2

I would like to re-implement proximity and collision detection queries using the voxelmap-pointshell algorithm, or a version of it. I have laid the PDF doc/Sagardia_PhD_Chapter3_2019.pdf where the original algorithm and its implementation are explained in detail. I don't want that precise implementation, but that's a sort of reference. Please, look at the PDF and make a technical summary in it (you can add small pieces of python code) which you will save in that same folder doc/Sagardia_PhD_Chapter3_Summary.md. You are going to be using that summary as reference later.

Before finishing the summary, have a look at the notebooks/ folder. I Have some Jupyter notebooks which are relevant, as they contain some tests.

### Output

[`Sagardia_PhD_Chapter3_Summary.md`](./doc/Sagardia_PhD_Chapter3_Summary.md)

## 3

Now, I would like to start with the re-implementation. I want to use Python for that, and I want to use numpy for the data structures and algorithms. I also want to use TriMesh and Open3D for 3D input parsing and visualization, but I prefer TriMesh. However, the implementation of the data structures and the algorithms should be done by hand, using numpy for the data structures and algorithms.

Use the definitions in the notebook notebooks/numpy_tests.ipynb and the summary doc/Sagardia_PhD_Chapter3_Summary.md as reference for the data structures and the algorithms. 
However, the summary is only a reference, and you should not use it as a strict guide.

In general, I see these major steps need to be carried out:

1. Implement the data structures in mesh.py, voxelmap.py, and pointshell.py. The file mesh.py should contain a mesh of 3d model wrapper which is going to use a library underneath (e.g., Trimesh) to parse the 3D model and to provide some basic functionalities, but the triangle mesh data structure should be implemented by hand using numpy. The voxelmap.py and pointshell.py files should contain the data structures for the voxelmap and the pointshell, respectively, which should also be implemented by hand using numpy.
2. Implement the algorithms: proximity_query.py and collision_detection.py.
3. Implement the generation modules: generate_voxelmap.py and generate_pointshell.py, which should be able to generate the voxelmap and the pointshell from a given mesh, respectively.
4. Implement the viewer.py, which should be able to visualize the mesh, the voxelmap, and the pointshell, as well as the results of the proximity and collision queries.

As you implement a step, please write the corresponding tests in the tests/ folder, and make sure they pass.

Notes on Step 1: Basic data structures:

- The Voxelmap should be a 3D grid of voxels, where each voxel contains a integer. The integer should be 0 if the voxel contains triangles, and the we should use layer values, positive inwards, negative outwards. The Voxelmap class does not store triangles neither it has the capability of creating the Voxelmap. However, it is able to store the Voxelmap data structure as an ASCII, load it, and it has all the basic functionalities necessary to run the downstream algorithms.
- The Pointshell should be a set of 6D points, where each point contains a 3d position and a normal vector; additionally, those points are contained in N (disjoint) spheres. The points should be sampled on the surface of the mesh, and they should be distributed in a way that they cover the surface of the mesh uniformly. The Pointshell class does not store the mesh neither it has the capability of creating the Pointshell. However, it is able to store the Pointshell data structure as an ASCII, load it, and it has all the basic functionalities necessary to run the downstream algorithms.
- The Mesh class should be a wrapper around a 3D model, which is able to parse the 3D model using a library (e.g., Trimesh), and it should provide some basic functionalities, such as getting the vertices, the faces, the normals, etc. However, the triangle mesh data structure should be implemented by hand using numpy. The Mesh is not passed to the Voxelmap neither to the Pointshell.
- The structure of the pointshell is a bit more complex, as it contains the points, the normals, and the spheres. The algorithms to traverse the pointshell will start visiting the spheres, and for each sphere, they will visit the points contained in that sphere. The default number of spheres will be N = 256.

Notes on Step 2: Proximity and collision detection algorithms:

- The proximity query should deliver the n closest or deepest points in the Pointshell with respect to the Voxelmap, as well as their signed distance value according to the VPS algorithm. The default value of n should be n = 1, i.e., the closest or deepest point. The proximity can optionally return the closest surface voxel id in the Voxelmap. But this need sto be computed in a second step, as it is not required for the collision detection query.
- The collision detection query should first run the proximity query and then compute the penalty-based force, as explained in the doc/Sagardia_PhD_Chapter3_Summary.md file. Only the colliding points (i.e., points with positive penetration values) will be used for the computation of the penalty-based force.
- The overall algorithm is explained in the doc/Sagardia_PhD_Chapter3_Summary.md file: visit the likely closest Pointshell points, transform them into the Voxelmap frame, check their signed distance value in the Voxelmap.
- The likely colliding points will be narrowed down by the Pointshell: by each Pointshell traverse, we will first go through the spheres, which contain disjoint subsets of points. For each sphere, we transform it to the Voxelmap frame, and check whether it's colliding or not, or how far its surface is from the Voxelmap. Then, we create a queue of sphere ids, sorted by their likely collision value, and we start visiting the points contained in those spheres.
- Each sphere should have a similar amount of points. Also, the points will be ordered in level of detail: first come the points with the lowest level of detail, and then the points with the highest level of detail. Each level of detail represents the same surface patch, but for coarser levels of detail the point density is lower, or in other words, the distances between the points of the same level of detail are higher. But all that should be taken care of in the generation of the Pointshell, which is not part of the Pointshell class, but it is a separate module (generate_pointshell.py). What the Pointshell needs to be able to do: we need to be able to travers only a percentage of the points in each sphere. Also, the spheres need to know where the level-of-detail jumps occur (i.e., the point ids).

Notes on Step 3: Generation of the voxelmap and the pointshell:

- The Voxelmap generation should be done by a separate module (generate_voxelmap.py), which should be able to generate the Voxelmap from a given Mesh. You can follow the same strategy as in the original implementation, which is explained in the doc/Sagardia_PhD_Chapter3_Summary.md file. However, you can also use other strategies, as long as they are able to generate a Voxelmap that is compatible with the algorithms.
- The Voxelmap should be a 3D grid of voxels, where each voxel contains an integer, the voxel value. The voxel value should be 0 if the voxel contains triangles (i.e., the voxel collides with triangles), and the we should use layer values, positive inwards, negative outwards. Layer values can be computed using floodfill.
- The Pointshell generation should be done by a separate module (generate_pointshell.py), which should be able to generate the Pointshell from a given Mesh. You can follow the same strategy as in the original implementation, which is explained in the doc/Sagardia_PhD_Chapter3_Summary.md file. However, you can also use other strategies, as long as they are able to generate a Pointshell that is compatible with the algorithms.
- In the original implementation, first a Voxelmap is generated, and then the voxel centers are projected onto the surface of the mesh to create the points of the Pointshell. Then, the points need to be clustered in N patches, containing each patch a similar amount of points and a sphere which contains them. And then, we need to order the points in each patch by level of detail. **HERE**

Notes on Step 4: Visualization:

General notes:

- Modularize the code as much as possible.

Notes on the tech/library stack and the project structure:

- Use the environment specified in conda.yaml and requirements.in.
- Use numpy for the data structures and algorithms; use the python/ folder for that
- Use TriMesh and Open3D for 3D input parsing and visualization; prefer TriMesh. However, the implementation of the data structures and the algorithms should be done by hand, using numpy for the data structures and algorithms.
- Use the data/models/ folder for 3D models.
- Use pytest for testing; use the tests/ folder for that.
- Use flake8 for linting the code, and make sure there are no linting errors.
- Use pytype for type checking, and make sure there are no type checking errors.
- Use pytest for testing, and make sure all the tests pass.

Additional chores and notes:

- Update requirements.in with pinned versions of the dependencies, as you use them in requirements.txt
- Populate pyproject.toml with package metadata
- Prepare everything to create and publish a package in the future
- Ignore the cpp/ folder for now
- If you have any technical/methodological doubts, check the doc/Sagardia_PhD_Chapter3_Summary.md file. You can also check the notebooks/ folder for some tests and experiments. Also, you are encouraged to ask me if you have any doubts.
- Use type hints in the code, and docstrings in the functions and classes. Follow PEP 8 style guide for Python code.

