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
    "sphinx_ts",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output ------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"

# Theme options
html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "source_repository": "https://github.com/your-username/sphinx-ts/",
    "source_branch": "main",
    "source_directory": "docs/",
}
html_static_path = []

# -- TypeScript Sphinx Configuration ----------------------------------------

# Directories to scan for TypeScript files (relative to conf.py)
sphinx_ts_src_dirs = ["../examples"]

# Patterns for files to exclude from parsing
sphinx_ts_exclude_patterns = [
    "**/*.test.ts",
    "**/*.spec.ts",
    "**/node_modules/**",
    "**/*.d.ts",
]

# Whether to include private members in documentation
sphinx_ts_include_private = True

# Whether to include inherited members in class documentation
sphinx_ts_include_inherited = True

# Source linking configuration
sphinx_ts_show_source_links = True
sphinx_ts_source_base_url = "https://github.com/snus-kin/sphinx-ts"
sphinx_ts_source_branch = "master"

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

# -- Furo theme configuration ------------------------------------------

highlight_language = "typescript"

# -- Todo extension configuration ------------------------------------------

todo_include_todos = True

html_theme_options = {
    "light_css_variables": {
        "color-sidebar-background": "#f8f9fb",
        "color-brand-primary": "#20539E",
        "color-brand-content": "#20539E",
        "color-foreground-primary": "#4E585F",
        "color-background-primary": "#FEFEFE",
        "color-background-secondary": "#F7F7F7",
        "font-stack": (
            "'Nunito Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', "
            "Helvetica, Arial, sans-serif"
        ),
    },
    "dark_css_variables": {
        "color-brand-primary": "#B6CBE9",
        "color-brand-content": "#B6CBE9",
        "color-foreground-primary": "#D5D5D5",
        "color-background-primary": "#393939",
        "color-background-secondary": "#434343",
        "color-sidebar-background": "#1E1E1E",
        "font-stack": (
            "'Nunito Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', "
            "Helvetica, Arial, sans-serif"
        ),
    },
}
