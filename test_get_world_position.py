"""
Test Suite for World Position Extraction API

This comprehensive test suite validates the simplified world position API
against various scenarios including edge cases, performance benchmarks,
and comparison with traditional approaches.

Run with: python -m pytest test_world_position.py -v
Or: python test_world_position.py (for standalone execution)
"""

import unittest
import time
from pxr import Usd, UsdGeom, Gf, Sdf


# Import the functions we're testing
# Adjust import path based on your module structure
try:
    from get_world_position import (
        get_world_position,
        get_world_positions_batch,
        get_world_transform_components
    )
except ImportError:
    # If running standalone, the functions should be in the same file
    # or we need to import from the artifact
    print("Note: Import from get_world_position module failed.")
    print("Define functions inline for testing or adjust import path.")


class TestWorldPositionBasic(unittest.TestCase):
    """Basic functionality tests for single prim position queries."""
    
    def setUp(self):
        """Create a fresh stage for each test."""
        self.stage = Usd.Stage.CreateInMemory()
        self.world = UsdGeom.Xform.Define(self.stage, Sdf.Path("/World"))
        self.stage.SetDefaultPrim(self.world.GetPrim())
    
    def test_simple_translation(self):
        """Test basic position extraction from a prim with translation."""
        cube = UsdGeom.Cube.Define(self.stage, Sdf.Path("/World/Cube"))
        expected_pos = Gf.Vec3d(10, 20, 30)
        cube.AddTranslateOp().Set(expected_pos)
        
        result = get_world_position(cube.GetPrim())
        
        self.assertAlmostEqual(result[0], expected_pos[0], places=5)
        self.assertAlmostEqual(result[1], expected_pos[1], places=5)
        self.assertAlmostEqual(result[2], expected_pos[2], places=5)
    
    def test_zero_position(self):
        """Test prim at origin."""
        cube = UsdGeom.Cube.Define(self.stage, Sdf.Path("/World/Cube"))
        # No translation op = position at origin
        
        result = get_world_position(cube.GetPrim())
        
        self.assertAlmostEqual(result[0], 0.0, places=5)
        self.assertAlmostEqual(result[1], 0.0, places=5)
        self.assertAlmostEqual(result[2], 0.0, places=5)
    
    def test_negative_coordinates(self):
        """Test prims with negative world positions."""
        cube = UsdGeom.Cube.Define(self.stage, Sdf.Path("/World/Cube"))
        expected_pos = Gf.Vec3d(-100, -50, -25)
        cube.AddTranslateOp().Set(expected_pos)
        
        result = get_world_position(cube.GetPrim())
        
        self.assertAlmostEqual(result[0], expected_pos[0], places=5)
        self.assertAlmostEqual(result[1], expected_pos[1], places=5)
        self.assertAlmostEqual(result[2], expected_pos[2], places=5)
    
    def test_non_transformable_prim(self):
        """Test that non-Xformable prims raise appropriate error."""
        # Create a non-transformable prim (e.g., a Scope without Xform)
        scope = self.stage.DefinePrim("/World/Scope", "Scope")
        
        with self.assertRaises(RuntimeError):
            get_world_position(scope)


class TestWorldPositionHierarchy(unittest.TestCase):
    """Test world position computation with nested transforms."""
    
    def setUp(self):
        """Create a stage with transform hierarchy."""
        self.stage = Usd.Stage.CreateInMemory()
        self.world = UsdGeom.Xform.Define(self.stage, Sdf.Path("/World"))
        self.stage.SetDefaultPrim(self.world.GetPrim())
    
    def test_parent_child_translation(self):
        """Test accumulation of parent and child translations."""
        # Parent at (100, 0, 0)
        parent = UsdGeom.Xform.Define(self.stage, Sdf.Path("/World/Parent"))
        parent.AddTranslateOp().Set(Gf.Vec3d(100, 0, 0))
        
        # Child at local (0, 50, 0), should be world (100, 50, 0)
        child = UsdGeom.Cube.Define(self.stage, Sdf.Path("/World/Parent/Child"))
        child.AddTranslateOp().Set(Gf.Vec3d(0, 50, 0))
        
        result = get_world_position(child.GetPrim())
        
        self.assertAlmostEqual(result[0], 100, places=5)
        self.assertAlmostEqual(result[1], 50, places=5)
        self.assertAlmostEqual(result[2], 0, places=5)
    
    def test_multi_level_hierarchy(self):
        """Test deep hierarchy with multiple transform levels."""
        # Level 1: (10, 0, 0)
        level1 = UsdGeom.Xform.Define(self.stage, Sdf.Path("/World/Level1"))
        level1.AddTranslateOp().Set(Gf.Vec3d(10, 0, 0))
        
        # Level 2: (0, 20, 0)
        level2 = UsdGeom.Xform.Define(self.stage, Sdf.Path("/World/Level1/Level2"))
        level2.AddTranslateOp().Set(Gf.Vec3d(0, 20, 0))
        
        # Level 3: (0, 0, 30)
        level3 = UsdGeom.Xform.Define(self.stage, Sdf.Path("/World/Level1/Level2/Level3"))
        level3.AddTranslateOp().Set(Gf.Vec3d(0, 0, 30))
        
        # Child: (1, 2, 3), world should be (11, 22, 33)
        child = UsdGeom.Cube.Define(self.stage, Sdf.Path("/World/Level1/Level2/Level3/Child"))
        child.AddTranslateOp().Set(Gf.Vec3d(1, 2, 3))
        
        result = get_world_position(child.GetPrim())
        
        self.assertAlmostEqual(result[0], 11, places=5)
        self.assertAlmostEqual(result[1], 22, places=5)
        self.assertAlmostEqual(result[2], 33, places=5)
    
    def test_rotation_affects_child_position(self):
        """Test that parent rotation affects child world position."""
        # Parent rotated 90 degrees around Z axis
        parent = UsdGeom.Xform.Define(self.stage, Sdf.Path("/World/Parent"))
        parent.AddRotateZOp().Set(90)
        
        # Child at local (10, 0, 0)
        # After 90° Z rotation, should be at world (0, 10, 0)
        child = UsdGeom.Cube.Define(self.stage, Sdf.Path("/World/Parent/Child"))
        child.AddTranslateOp().Set(Gf.Vec3d(10, 0, 0))
        
        result = get_world_position(child.GetPrim())
        
        # Allow some numerical tolerance for rotation
        self.assertAlmostEqual(result[0], 0, places=3)
        self.assertAlmostEqual(result[1], 10, places=3)
        self.assertAlmostEqual(result[2], 0, places=3)

    def test_scale_affects_child_position(self):
        """Test that parent scale affects child's world position."""
        # Parent with translate then scale
        parent = UsdGeom.Xform.Define(self.stage, Sdf.Path("/World/Parent"))
        parent.AddTranslateOp().Set(Gf.Vec3d(10, 0, 0))
        parent.AddScaleOp().Set(Gf.Vec3d(2, 2, 2))
        
        # Child translation
        child = UsdGeom.Cube.Define(self.stage, Sdf.Path("/World/Parent/Child"))
        child.AddTranslateOp().Set(Gf.Vec3d(5, 0, 0))
        
        result = get_world_position(child.GetPrim())
        
        # USD Transform Composition:
        # Parent: Translate(10,0,0) then Scale(2,2,2) → parent at (10,0,0) with scale 2
        # Child: Local offset (5,0,0) → scaled by parent's scale → (10,0,0) offset
        # Child world position: (10,0,0) + (10,0,0) = (20,0,0)
        self.assertAlmostEqual(result[0], 20, places=3)
        self.assertAlmostEqual(result[1], 0, places=3)
        self.assertAlmostEqual(result[2], 0, places=3)


class TestWorldPositionBatch(unittest.TestCase):
    """Test batch position queries with XformCache."""
    
    def setUp(self):
        """Create stage with multiple prims."""
        self.stage = Usd.Stage.CreateInMemory()
        self.world = UsdGeom.Xform.Define(self.stage, Sdf.Path("/World"))
        self.stage.SetDefaultPrim(self.world.GetPrim())
    
    def test_batch_query_accuracy(self):
        """Test that batch query produces same results as individual queries."""
        prims = []
        expected_positions = []
        
        # Create 10 cubes at different positions
        for i in range(10):
            cube = UsdGeom.Cube.Define(self.stage, Sdf.Path(f"/World/Cube{i}"))
            pos = Gf.Vec3d(i * 10, i * 5, i * 2)
            cube.AddTranslateOp().Set(pos)
            prims.append(cube.GetPrim())
            expected_positions.append(pos)
        
        # Batch query
        batch_results = get_world_positions_batch(prims)
        
        # Individual queries
        individual_results = [get_world_position(p) for p in prims]
        
        # Compare batch vs individual
        for batch, individual, expected in zip(batch_results, individual_results, expected_positions):
            self.assertAlmostEqual(batch[0], individual[0], places=5)
            self.assertAlmostEqual(batch[1], individual[1], places=5)
            self.assertAlmostEqual(batch[2], individual[2], places=5)
            
            self.assertAlmostEqual(batch[0], expected[0], places=5)
            self.assertAlmostEqual(batch[1], expected[1], places=5)
            self.assertAlmostEqual(batch[2], expected[2], places=5)
    
    def test_batch_with_shared_parents(self):
        """Test batch query efficiency with shared parent transforms."""
        # Create parent
        parent = UsdGeom.Xform.Define(self.stage, Sdf.Path("/World/Parent"))
        parent.AddTranslateOp().Set(Gf.Vec3d(100, 0, 0))
        
        # Create 20 children under same parent
        prims = []
        for i in range(20):
            cube = UsdGeom.Cube.Define(self.stage, Sdf.Path(f"/World/Parent/Cube{i}"))
            cube.AddTranslateOp().Set(Gf.Vec3d(i, 0, 0))
            prims.append(cube.GetPrim())
        
        # Batch query should cache parent transform
        results = get_world_positions_batch(prims)
        
        # Verify all have parent offset applied
        for i, pos in enumerate(results):
            self.assertAlmostEqual(pos[0], 100 + i, places=5)
    
    def test_empty_batch(self):
        """Test batch query with empty list."""
        results = get_world_positions_batch([])
        self.assertEqual(len(results), 0)


class TestWorldTransformComponents(unittest.TestCase):
    """Test full transform decomposition function."""
    
    def setUp(self):
        """Create a fresh stage."""
        self.stage = Usd.Stage.CreateInMemory()
        self.world = UsdGeom.Xform.Define(self.stage, Sdf.Path("/World"))
        self.stage.SetDefaultPrim(self.world.GetPrim())
    
    def test_transform_decomposition(self):
        """Test extraction of translation, rotation, and scale."""
        cube = UsdGeom.Cube.Define(self.stage, Sdf.Path("/World/Cube"))
        
        # Add transforms
        cube.AddTranslateOp().Set(Gf.Vec3d(10, 20, 30))
        cube.AddRotateXYZOp().Set(Gf.Vec3f(0, 45, 0))
        cube.AddScaleOp().Set(Gf.Vec3d(2, 3, 4))
        
        translation, rotation, scale = get_world_transform_components(cube.GetPrim())
        
        # Check translation
        self.assertAlmostEqual(translation[0], 10, places=5)
        self.assertAlmostEqual(translation[1], 20, places=5)
        self.assertAlmostEqual(translation[2], 30, places=5)
        
        # Check scale
        self.assertAlmostEqual(scale[0], 2, places=2)
        self.assertAlmostEqual(scale[1], 3, places=2)
        self.assertAlmostEqual(scale[2], 4, places=2)


class TestAnimatedTransforms(unittest.TestCase):
    """Test position queries at different time codes."""
    
    def setUp(self):
        """Create stage with animated transform."""
        self.stage = Usd.Stage.CreateInMemory()
        self.world = UsdGeom.Xform.Define(self.stage, Sdf.Path("/World"))
        self.stage.SetDefaultPrim(self.world.GetPrim())
    
    def test_position_at_different_times(self):
        """Test animated translation."""
        cube = UsdGeom.Cube.Define(self.stage, Sdf.Path("/World/Cube"))
        translate_op = cube.AddTranslateOp()
        
        # Animate: linear motion from (0,0,0) to (100,0,0) over 100 frames
        translate_op.Set(Gf.Vec3d(0, 0, 0), 0)
        translate_op.Set(Gf.Vec3d(50, 0, 0), 50)
        translate_op.Set(Gf.Vec3d(100, 0, 0), 100)
        
        # Query at different times
        pos_t0 = get_world_position(cube.GetPrim(), Usd.TimeCode(0))
        pos_t50 = get_world_position(cube.GetPrim(), Usd.TimeCode(50))
        pos_t100 = get_world_position(cube.GetPrim(), Usd.TimeCode(100))
        
        self.assertAlmostEqual(pos_t0[0], 0, places=5)
        self.assertAlmostEqual(pos_t50[0], 50, places=5)
        self.assertAlmostEqual(pos_t100[0], 100, places=5)
    
    def test_default_time_vs_specific_time(self):
        """Test difference between default and specific time codes."""
        cube = UsdGeom.Cube.Define(self.stage, Sdf.Path("/World/Cube"))
        translate_op = cube.AddTranslateOp()
        
        # Set default value
        translate_op.Set(Gf.Vec3d(10, 0, 0))
        
        # Set time-varying value
        translate_op.Set(Gf.Vec3d(50, 0, 0), 100)
        
        pos_default = get_world_position(cube.GetPrim())  # Uses default
        pos_t100 = get_world_position(cube.GetPrim(), Usd.TimeCode(100))
        
        self.assertAlmostEqual(pos_default[0], 10, places=5)
        self.assertAlmostEqual(pos_t100[0], 50, places=5)


class TestPerformanceBenchmark(unittest.TestCase):
    """Performance comparison tests."""
    
    def setUp(self):
        """Create a large scene for performance testing."""
        self.stage = Usd.Stage.CreateInMemory()
        self.world = UsdGeom.Xform.Define(self.stage, Sdf.Path("/World"))
        self.stage.SetDefaultPrim(self.world.GetPrim())
        
        # Create hierarchy with many prims
        self.prims = []
        for i in range(100):
            cube = UsdGeom.Cube.Define(self.stage, Sdf.Path(f"/World/Cube{i}"))
            cube.AddTranslateOp().Set(Gf.Vec3d(i, i, i))
            self.prims.append(cube.GetPrim())
    
    def test_batch_vs_individual_performance(self):
        """Compare performance of batch vs individual queries."""
        # Individual queries
        start_individual = time.time()
        individual_results = [get_world_position(p) for p in self.prims]
        time_individual = time.time() - start_individual
        
        # Batch query
        start_batch = time.time()
        batch_results = get_world_positions_batch(self.prims)
        time_batch = time.time() - start_batch
        
        print(f"\n--- Performance Comparison (100 prims) ---")
        print(f"Individual queries: {time_individual*1000:.2f}ms")
        print(f"Batch query: {time_batch*1000:.2f}ms")
        print(f"Speedup: {time_individual/time_batch:.2f}x")
        
        # Batch should be faster (or at least not slower)
        # This is a soft assertion since timing can vary
        if time_batch < time_individual:
            print("✓ Batch query is faster!")
        
        # Verify results match
        for ind, batch in zip(individual_results, batch_results):
            self.assertAlmostEqual(ind[0], batch[0], places=5)


class TestComparisonWithTraditional(unittest.TestCase):
    """Verify our simplified API matches traditional approach."""
    
    def setUp(self):
        """Create test stage."""
        self.stage = Usd.Stage.CreateInMemory()
        self.world = UsdGeom.Xform.Define(self.stage, Sdf.Path("/World"))
        self.stage.SetDefaultPrim(self.world.GetPrim())
    
    def traditional_get_position(self, prim, time=Usd.TimeCode.Default()):
        """Traditional 3-step approach."""
        xformable = UsdGeom.Xformable(prim)
        world_transform = xformable.ComputeLocalToWorldTransform(time)
        return world_transform.ExtractTranslation()
    
    def test_matches_traditional_simple(self):
        """Test simplified API matches traditional approach."""
        cube = UsdGeom.Cube.Define(self.stage, Sdf.Path("/World/Cube"))
        cube.AddTranslateOp().Set(Gf.Vec3d(42, 84, 126))
        
        traditional = self.traditional_get_position(cube.GetPrim())
        simplified = get_world_position(cube.GetPrim())
        
        self.assertAlmostEqual(traditional[0], simplified[0], places=5)
        self.assertAlmostEqual(traditional[1], simplified[1], places=5)
        self.assertAlmostEqual(traditional[2], simplified[2], places=5)
    
    def test_matches_traditional_complex(self):
        """Test with complex hierarchy."""
        # Create complex hierarchy
        parent = UsdGeom.Xform.Define(self.stage, Sdf.Path("/World/Parent"))
        parent.AddTranslateOp().Set(Gf.Vec3d(100, 0, 0))
        parent.AddRotateZOp().Set(45)
        parent.AddScaleOp().Set(Gf.Vec3d(2, 2, 2))
        
        child = UsdGeom.Cube.Define(self.stage, Sdf.Path("/World/Parent/Child"))
        child.AddTranslateOp().Set(Gf.Vec3d(10, 10, 0))
        
        traditional = self.traditional_get_position(child.GetPrim())
        simplified = get_world_position(child.GetPrim())
        
        self.assertAlmostEqual(traditional[0], simplified[0], places=3)
        self.assertAlmostEqual(traditional[1], simplified[1], places=3)
        self.assertAlmostEqual(traditional[2], simplified[2], places=3)


def run_all_tests():
    """Run all tests with verbose output."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestWorldPositionBasic))
    suite.addTests(loader.loadTestsFromTestCase(TestWorldPositionHierarchy))
    suite.addTests(loader.loadTestsFromTestCase(TestWorldPositionBatch))
    suite.addTests(loader.loadTestsFromTestCase(TestWorldTransformComponents))
    suite.addTests(loader.loadTestsFromTestCase(TestAnimatedTransforms))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceBenchmark))
    suite.addTests(loader.loadTestsFromTestCase(TestComparisonWithTraditional))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(run_all_tests())