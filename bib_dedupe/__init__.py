"""Top-level package for bib-dedupe."""

__author__ = """Gerit Wagner"""
__email__ = "gerit.wagner@uni-bamberg.de"

# Instead of adding elements to __all__,
# prefixing methods/variables with "__" is preferred.
# Imports like "from x import *" are discouraged.

from bib_dedupe.util import VerbosePrint

verbosity_level = 1  # Set your desired verbosity level here
verbose_print = VerbosePrint(verbosity_level)
