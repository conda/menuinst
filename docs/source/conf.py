# Copyright (C) 2022 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import json
from pathlib import Path

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = html_title = "menuinst"
copyright = "2022, menuinst contributors"
author = "menuinst contributors"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.graphviz",
    "sphinx.ext.ifconfig",
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.viewcode",
    "sphinxcontrib.mermaid",
    "sphinx_sitemap",
    "sphinx_design",
    "sphinx_copybutton",
    "sphinx_tabs.tabs",
    "sphinxcontrib.autodoc_pydantic",
]

myst_heading_anchors = 3
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]
myst_linkify_fuzzy_links = False
default_config_payload = json.dumps(
    json.loads(
        (Path(__file__).parents[2] / "menuinst" / "data" / "menuinst.default.json").read_text()
    ),
    indent=2,
)
myst_substitutions = {
    "default_schema_json": f"```json\n{default_config_payload}\n```",
}

autodoc_pydantic_field_swap_name_and_alias = True
autodoc_pydantic_model_signature_prefix = "model"
autodoc_pydantic_model_show_json = False
autodoc_pydantic_model_show_config_member = False
autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_model_show_validator_summary = False
autodoc_pydantic_model_show_field_summary = False
autodoc_pydantic_model_member_order = "bysource"

nitpicky = True
nitpick_ignore = [
    ("py:class", "types.ConstrainedListValue"),
    ("py:class", "menuinst._schema.ConstrainedStrValue"),
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]

html_css_files = [
    "css/custom.css",
]

# Serving the robots.txt since we want to point to the sitemap.xml file
html_extra_path = ["robots.txt"]

html_theme_options = {
    "github_url": "https://github.com/conda/menuinst",
    "collapse_navigation": True,
    "navigation_depth": 1,
    "use_edit_page_button": True,
    "show_toc_level": 1,
    "navbar_align": "left",
    "header_links_before_dropdown": 1,
    # "announcement": "<p>This is the documentation for menuinst!</p>",
}

html_context = {
    "github_user": "conda",
    "github_repo": "menuinst",
    "github_version": "main",
    "doc_path": "docs",
}

# We don't have a locale set, so we can safely ignore that for the sitemaps.
sitemap_locales = [None]
# We're hard-coding stable here since that's what we want Google to point to.
sitemap_url_scheme = "{link}"
