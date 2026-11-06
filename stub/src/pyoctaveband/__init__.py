#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Transition shim: PyOctaveBand has been renamed to phonometry.

Re-exports the complete phonometry API under the legacy ``pyoctaveband``
name so existing code keeps working. New code should ``import phonometry``.
"""

import warnings

from phonometry import *

# Each name the shim takes by name is re-exported as itself, the form a type
# checker reads as a re-export of a typed package: pyright refused a plain
# `from phonometry import __version__` as a private import.
from phonometry import __all__ as __all__
from phonometry import __version__ as __version__

# FutureWarning (not DeprecationWarning): visible by default, so users of
# the old name actually see the migration notice.
warnings.warn(
    "PyOctaveBand has been renamed to 'phonometry'. This package installs the "
    "3.x line, where 'import phonometry' replaces 'import pyoctaveband' and "
    "nothing else changes. From 4.0 on, names live in the module of their "
    "domain: https://docs.jmrp.io/phonometry/start/upgrading/",
    FutureWarning,
    stacklevel=2,
)
