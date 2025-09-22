import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath("../../bib_dedupe"))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "BibDedupe"
copyright = f"{datetime.now().year}, Gerit Wagner"
author = "Gerit Wagner"
release = "0.6.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

extensions = ["sphinx.ext.autodoc", "sphinx_copybutton"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
# html_logo = "logo_small.png"
html_favicon = "favicon.ico"
html_css_files = [
    "css/custom.css",
]
html_title = "BibDedupe"
# html_logo = "figures/logo.png"
