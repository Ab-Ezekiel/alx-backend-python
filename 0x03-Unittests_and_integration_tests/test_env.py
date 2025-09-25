#!/usr/bin/env python3
"""Diagnostic test to expose grader environment for debugging."""

import sys
import os
import unittest
import subprocess

class TestEnv(unittest.TestCase):
    """Print environment info so autograder logs reveal differences."""

    def test_show_environment(self):
        """Print Python and filesystem info for debugging only."""
        print("=== PYTHON INFO ===")
        print("executable:", sys.executable)
        print("version:", sys.version.replace("\n", " "))
        print("platform:", sys.platform)
        print()
        print("=== SYS.PATH (first 10) ===")
        for p in sys.path[:10]:
            print(p)
        print()
        print("=== REPO ROOT LISTING (top-level) ===")
        for f in sorted(os.listdir(".")):
            print(f)
        print()
        print("=== tests folder listing ===")
        for f in sorted(os.listdir("0x03-Unittests_and_integration_tests")):
            print(f)
        print()
        try:
            print("=== pip freeze snippet (first 40 lines) ===")
            out = subprocess.check_output([sys.executable, "-m", "pip", "freeze"],
                                          stderr=subprocess.STDOUT,
                                          text=True)
            for i, line in enumerate(out.splitlines()):
                if i >= 40:
                    break
                print(line)
        except Exception as exc:
            print("pip freeze failed:", exc)

        # The test should always pass (we only want printed info)
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()
