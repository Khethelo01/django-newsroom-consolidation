"""Initialise Django before autodoc imports application modules."""
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Documentation imports models but never queries a live database.
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ["DB_ENGINE"] = "sqlite"
os.environ.setdefault("DJANGO_SECRET_KEY", "documentation-build-only")
import django

django.setup()

project = "Newsroom Capstone"
author = "Khethelo Ntsele"
copyright = "2026, Khethelo Ntsele"
version = release = "1.0"
language = "en"
extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode", "sphinx.ext.napoleon"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "sphinx_rtd_theme"
html_static_path = []
templates_path = []
