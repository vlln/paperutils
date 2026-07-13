"""Set up sys.path so tests can import the paperutils package.

The source lives under skills/paperutils/scripts/src/. Tests can be run with:

    PYTHONPATH=skills/paperutils/scripts/src python -m pytest

Or set PAPERUTILS_SRC to point directly at the package directory.
"""

import os
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
_SRC = os.environ.get("PAPERUTILS_SRC")
if _SRC:
    sys.path.insert(0, _SRC)
else:
    _DEFAULT = str(_HERE.parent / "skills" / "paperutils" / "scripts" / "src")
    sys.path.insert(0, _DEFAULT)

# Verify the package is importable
import paperutils  # noqa: E402, F401