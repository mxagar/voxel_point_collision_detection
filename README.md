# Re-Implementation of the Voxelmap Pointshell Algorithm in Python

This repository contains a package which is able to detect collisions between voxelized and point-sampled objects following the Voxelmap Pointshell Algorithm (VPS) by McNeely et al.

:construction: *On-going work...*

:warning: *Pet project for fun, no guarantees...*

## Setup

In order to use the code, first, you need to set a Python environment and then install the dependencies.
A quick recipe to getting started by using [conda](https://conda.io/projects/conda/en/latest/index.html) is the following:

```bash
# Set proxy, if required

# Create environment, e.g., with conda, to control Python version
conda create -n vps python=3.10 pip
conda activate vps

# Install pip-tools
python -m pip install -U pip-tools

# Generate pinned requirements.txt
pip-compile requirements.in

# Install pinned requirements, as always
python -m pip install -r requirements.txt

# If required, add new dependencies to requirements.in and sync
# i.e., update environment
pip-compile requirements.in
pip-sync requirements.txt
python -m pip install -r requirements.txt

# Optional (in the future): To install the package
python -m pip pip install .

# Optional: if you's like to export you final conda environment config
conda env export > environment.yml
# Optional: If required, to delete the conda environment
conda remove --name vps --all
```

## References

There are many works in the haptics literature which deal 

- McNeely
- Barbic
- Sagardia

## Interesting Links

TBD.

## Authorship

Mikel Sagardia, 2024.  
No guarantees.