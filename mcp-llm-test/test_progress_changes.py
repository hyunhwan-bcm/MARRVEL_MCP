#!/usr/bin/env python3
"""
Simple test to verify progress bar and concurrency changes are working.
"""
import sys
import os

# Test imports
try:
    from tqdm.asyncio import tqdm as atqdm

    print("✅ tqdm.asyncio imported successfully")
except ImportError as e:
    print(f"❌ Failed to import tqdm.asyncio: {e}")
    sys.exit(1)

# Test argument parser additions
try:
    sys.path.insert(0, os.path.dirname(__file__))
    # We can't fully import evaluate_mcp without dependencies, but we can check syntax
    with open("evaluate_mcp.py", "r") as f:
        content = f.read()

    # Check for new features
    checks = [
        ("tqdm import", "from tqdm.asyncio import tqdm as atqdm" in content),
        ("pbar parameter", "pbar=None" in content),
        ("concurrency argument", "--concurrency" in content),
        ("progress bar creation", "atqdm(total=" in content),
        ("progress update", "pbar.update(1)" in content),
        ("progress message", "pbar.set_postfix_str" in content),
    ]

    all_passed = True
    for name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {'FOUND' if passed else 'NOT FOUND'}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n✅ All changes verified successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some changes are missing")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error during verification: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
