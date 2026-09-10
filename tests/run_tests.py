import os
import sys
import unittest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "test-secret-key")


if __name__ == "__main__":
    print("\nRunning PCOSight automated tests...\n")
    suite = unittest.defaultTestLoader.discover(
        start_dir=os.path.dirname(__file__),
        pattern="test_*.py",
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)

    print("\nTest summary")
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures:  {len(result.failures)}")
    print(f"  Errors:    {len(result.errors)}")

    if result.wasSuccessful():
        print("  Result:    PASS")
        sys.exit(0)

    print("  Result:    FAIL")
    sys.exit(1)
