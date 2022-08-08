"""Logging setup.

Import the package::

   import lamin_logger

This is the complete API reference:

.. autosummary::
   :toctree: .

   colors
"""

__version__ = "0.1.3"

from ._core import colors, logger  # noqa
from . import _configure_external  # noqa
