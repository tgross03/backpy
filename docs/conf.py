# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import backpy
import backpy.version
from backpy import TOMLConfiguration, VariableLibrary

import sys
from pathlib import Path

from datetime import datetime

pyproject = TOMLConfiguration(
    Path(backpy.__file__).parent.parent / "pyproject.toml"
)
authors = pyproject["project.authors"]
authors = ",".join([author["name"] for author in authors])
year = datetime.now().year

version = backpy.version.version

project = "backpy"
copyright = f"© {year}, {authors}"
author = authors
version = version
release = version

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

sys.path.append(str(Path('_extensions').resolve()))

extensions = ["sphinx_iconify", "sphinx_design", "sphinx_copybutton", "sphinx_togglebutton", "sphinx_click", "no_ansi"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTMLoutput -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "shibuya"
html_static_path = ["_static"]

html_theme_options = {
    "light_logo": "_static/backpy_header_light.png",
    "dark_logo": "_static/backpy_header_dark.png",
    "github_url": "https://github.com/tgross03/backpy",
    "accent_color": "blue",
    "nav_links": [
        {
            "title": "User Guide",
            "url": "writing",
            "children": [
                {
                    "title": "Quickstart",
                    "url": "user-guide/quickstart",
                },
                {
                    "title": "Installation",
                    "url": "user-guide/installation",
                },
                {
                    "title": "About",
                    "url": "user-guide/about",
                },
            ]
        },
    ]
}
