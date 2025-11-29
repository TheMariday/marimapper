# Marimapper Development Context

## Virtual Environment
- **Location:** `$(pwd)/.venv`
- **Python at time of writing:** 3.12
- **Package Manager:** Use `uv pip` with `-p /path/to/venv/bin/python` flag
  - Example: `uv pip install -p /path/to/venv/bin/python package_name`
- **Deps Already Installed:** `uv pip freeze`
- **Check present transitive deps, ASK FIRST to require installing new ones**

## Key Dependencies
- numpy, opencv-python, tqdm, open3d
- pycolmap==3.11.1 (do NOT update - breaks on > 3.12)
