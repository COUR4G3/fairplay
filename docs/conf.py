# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
# -- Path setup --------------------------------------------------------------
# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import importlib
import inspect
import os

from setuptools_scm import get_version

# -- Project information -----------------------------------------------------

project = "FairPlay"
copyright = "2023, FairPlay"
author = "FairPlay"

# The full version, including alpha/beta/rc tags
release = get_version("../")


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.linkcode",
    "sphinx_issues",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for autodoc ----------------------------------------------------

# Automatically extract typehints when specified and place them in
# descriptions of the relevant function/method.
autodoc_typehints = "description"


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_title = f"{project} documentation ({release})"
html_logo = "_static/logo.jpg"
html_theme = "furo"
html_theme_options = {
    "footer_icons": [
        {
            "name": "Donate",
            "url": "https://ko-fi.com/cour4g3",
            "html": '<img src="/_static/ko-fi.svg" alt="Ko-fi">',
            "class": "",
        },
        {
            "name": "GitHub",
            "url": "https://github.com/fairplay/fairplay",
            "html": '<img src="/_static/github.svg" alt="GitHub">',
            "class": "",
        },
    ],
    "sidebar_hide_name": True,
    "source_repository": "https://github.com/fairplay/fairplay",
    "source_branch": "master",
    "source_directory": "docs/",
}

# Load custom stylesheets to support Algolia search.
html_css_files = [
    "algolia.css",
    "https://cdn.jsdelivr.net/npm/docsearch.js@2/dist/cdn/docsearch.min.css",
]

# Load custom javascript to support Algolia search. Note that the sequence
# defined below (external first) is intentional!
html_js_files = [
    (
        "https://cdn.jsdelivr.net/npm/docsearch.js@2/dist/cdn/"
        "docsearch.min.js",
        {"defer": "defer"},
    ),
    ("algolia.js", {"defer": "defer"}),
]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
}

issues_github_path = "COUR4G3/lumberjack"


def linkcode_resolve(domain, info):
    if domain != "py":
        return None
    if not info["module"]:
        return None

    mod = importlib.import_module(info["module"])
    if "." in info["fullname"]:
        objname, attrname = info["fullname"].split(".")
        obj = getattr(mod, objname)
        try:
            # object is a method of a class
            obj = getattr(obj, attrname)
        except AttributeError:
            # object is an attribute of a class
            return None
    else:
        obj = getattr(mod, info["fullname"])

    try:
        file = inspect.getsourcefile(obj)
        lines = inspect.getsourcelines(obj)
    except TypeError:
        # e.g. object is a typing.Union
        return None
    file = os.path.relpath(file, os.path.abspath(".."))
    start, end = lines[1], lines[1] + len(lines[0]) - 1

    return f"https://github.com/fairplay/fairplay/blob/master/{file}#L{start}-L{end}"
