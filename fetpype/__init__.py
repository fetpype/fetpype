from . import pipelines  # noqa
from . import nodes  # noqa
from . import utils  # noqa
from .definitions import (  # noqa
    VALID_RECONSTRUCTION,
    VALID_SEGMENTATION,
    VALID_PREPRO_TAGS,
    VALID_RECON_TAGS,
    VALID_SEG_TAGS,
)

__version__ = "unknown"
try:
    from ._version import __version__  # noqa
except ImportError:
    # We're running in a tree that doesn't have a _version.py
    pass
