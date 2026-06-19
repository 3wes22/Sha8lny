"""
Test-suite environment guards.

OMP_NUM_THREADS=1 prevents a segfault-at-exit on macOS when lightgbm's
OpenMP runtime collides with other native libs loaded by the suite
(observed on system Python 3.13: all tests pass, interpreter dies at
shutdown with exit 139). Must be set before lightgbm is imported, which
is why it lives in conftest rather than individual test modules.
Proper fix is running the suite inside the project venv (see
IMPLEMENTATION_PLAN.md Task 1.3).
"""

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
