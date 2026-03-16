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

