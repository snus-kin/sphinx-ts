"""Configuration file for the Sphinx documentation builder.

For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "TypeScript Sphinx Extension"
copyright_text = "2024, TypeScript Sphinx Contributors"
author = "TypeScript Sphinx Contributors"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "ts_sphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output ------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = []

# -- TypeScript Sphinx Configuration ----------------------------------------

# Directories to scan for TypeScript files (relative to conf.py)
ts_sphinx_src_dirs = ["../examples"]

# Patterns for files to exclude from parsing
ts_sphinx_exclude_patterns = [
    "**/*.test.ts",
    "**/*.spec.ts",
    "**/node_modules/**",
    "**/*.d.ts",
]

# Whether to include private members in documentation
ts_sphinx_include_private = False

# Whether to include inherited members in class documentation
ts_sphinx_include_inherited = True

# -- Intersphinx Configuration ----------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
}

# -- Napoleon Configuration -------------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# -- Additional HTML theme options ------------------------------------------

html_theme_options = {
    "source_repository": "https://github.com/your-username/ts-sphinx/",
    "source_branch": "main",
    "source_directory": "docs/",
    "sidebar_hide_name": True,
    "navigation_with_keys": True,
    "top_of_page_button": "edit",
}

highlight_language = "typescript"
