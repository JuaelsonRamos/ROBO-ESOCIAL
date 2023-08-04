""" Sphinx configuration."""

from os.path import dirname, join, abspath
import sys

project_root: str = abspath(join(dirname(__file__), "..", "..", ".."))

sys.path.insert(0, project_root)

extensions = [
    "sphinx.ext.todo",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx.ext.graphviz",
    "sphinx.ext.napoleon",
    "autoapi.extension",
    "myst_parser"
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

autoapi_dirs = [
    join(project_root, "src"),
]

autoapi_ignore = [
    "build/**/*.py"
]

project = 'ROBO-ESOCIAL'
copyright = '2023, Juaelson'
author = 'Juaelson'
release = '0.0.0'

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

language = 'pt_BR'

html_theme = 'furo'
html_static_path = ['_static']

html_search_language = "pt"

numfig = True
autosummary_generate = True
