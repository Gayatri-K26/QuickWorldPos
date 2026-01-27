# QuickWorldPos
**Simplified World Position Extraction for OpenUSD**
A streamlined API for extracting world-space positions from USD prims, reducing the typical 3-step process to a single function call.

**Overview**
When working with OpenUSD, getting a prim's world position traditionally requires three steps:
```python
# Traditional approach (3 steps)
xformable = UsdGeom.Xformable(prim)
world_transform = xformable.ComputeLocalToWorldTransform(time)
position = world_transform.ExtractTranslation()
```

This project simplifies it to one step:
```python
Simplified approach (1 step)
position = get_world_position(prim, time)
```
Result: ~66% reduction in code steps with identical output.

**Features**
Single-function position extraction - Get world position in one call
Batch optimization - XformCache-powered batch queries for 5-10x speedup
Full transform decomposition - Optional function for rotation and scale
Comprehensive test suite - 17 tests with 100% pass rate

**Quick Start**
Installation
```
# Clone the repository
cd OpenUSD-Code-Samples/source/transforms/get-world-transforms

# Install dependencies with Poetry
poetry install

# Run the demo
poetry run python get_world_position.py
```

Basic Usage
```
pythonfrom pxr import Usd, UsdGeom, Gf, Sdf
from get_world_position import get_world_position

# Open a stage
stage = Usd.Stage.Open("scene.usd")

# Get world position of a prim
prim = stage.GetPrimAtPath("/World/Cube")
position = get_world_position(prim)
print(f"World position: {position}")  # (10.0, 20.0, 30.0)
```

Batch Queries (Optimized)
For better performance when querying multiple prims:
```
pythonfrom get_world_position import get_world_positions_batch

# Get all mesh prims
meshes = [p for p in stage.Traverse() if p.IsA(UsdGeom.Mesh)]

# Batch query (uses XformCache internally)
positions = get_world_positions_batch(meshes)

for prim, pos in zip(meshes, positions):
    print(f"{prim.GetName()}: {pos}")
```

**API Reference**
```
get_world_position(prim, time=Usd.TimeCode.Default())
```

Extract world-space position from a single prim.
Parameters:

- prim (Usd.Prim): The USD prim to query
- time (Usd.TimeCode): Time code for animated transforms (default: static)

Returns:

- Gf.Vec3d: World-space position (x, y, z)

Example:
```pythonposition = get_world_position(cube_prim)```

get_world_positions_batch(prims, time=Usd.TimeCode.Default())
Extract world positions for multiple prims efficiently using XformCache.
Parameters:

prims (List[Usd.Prim]): List of USD prims to query
time (Usd.TimeCode): Time code for animated transforms

Returns:

List[Gf.Vec3d]: World-space positions corresponding to input prims

Performance: 5-10x faster than individual queries for scenes with shared transform hierarchies.
Example:
```
pythonpositions = get_world_positions_batch([prim1, prim2, prim3])
```

```get_world_transform_components(prim, time=Usd.TimeCode.Default())```
Extract full world-space transform decomposition (translation, rotation, scale).
Parameters:

- prim (Usd.Prim): The USD prim to decompose
- time (Usd.TimeCode): Time code for evaluation

Returns:

- Tuple[Gf.Vec3d, Gf.Rotation, Gf.Vec3d]: (translation, rotation, scale)

Example:
```pythontranslation, rotation, scale = get_world_transform_components(prim)```

**Testing**

Run All Tests
```bashpoetry run pytest test_get_world_position.py -v```
Run with Coverage Report
```bashpoetry run pytest test_get_world_position.py --cov=get_world_position --cov-report=term-missing```
Test Results
✅ 17/17 tests passing (100%)

Test Categories:
├─ Basic Functionality (4 tests)
├─ Hierarchy & Nesting (4 tests)
├─ Batch Queries (3 tests)
├─ Transform Components (1 test)
├─ Animated Transforms (2 tests)
├─ Performance Benchmarks (1 test)
└─ Traditional Comparison (2 tests)

**How It Works**
Transform Composition in USD
USD transforms are applied according to the xformOpOrder attribute:

```xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ", "xformOp:scale"]```

Operations are applied left-to-right (translate → rotate → scale).

XformCache Optimization
For batch queries, the API uses UsdGeom.XformCache which:
1. Caches intermediate transform computations
2. Reuses cached parent transforms for child prims
3. Provides 5-10x performance improvement for hierarchical scenes
