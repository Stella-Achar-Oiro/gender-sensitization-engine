#!/usr/bin/env python3
"""
Fix blank screen when opening Label: use a minimal label config
(no conditional visibility, no inline styles) so the UI loads.

Usage (from repo root):
  LABEL_STUDIO_BASE_DATA_DIR=.label_studio_data DJANGO_DB=sqlite \
    .ls_venv/bin/python scripts/fix_label_studio_blank_screen.py
"""
import os
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("LABEL_STUDIO_BASE_DATA_DIR", os.path.join(repo_root, ".label_studio_data"))
os.environ.setdefault("DJANGO_DB", "sqlite")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "label_studio.core.settings.label_studio")

venv_site = os.path.join(repo_root, ".ls_venv", "lib", "python3.11", "site-packages")
ls_pkg = os.path.join(venv_site, "label_studio")
for p in (ls_pkg, venv_site):
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

import django
django.setup()

from projects.models import Project

MINIMAL_CONFIG_PATH = os.path.join(repo_root, "scripts", "label_studio_config_minimal.xml")


def main():
    project = Project.objects.filter(title__icontains="JuaKazi").first()
    if not project:
        print("No JuaKazi project found.")
        sys.exit(1)
    if not os.path.isfile(MINIMAL_CONFIG_PATH):
        print(f"Minimal config not found: {MINIMAL_CONFIG_PATH}")
        sys.exit(1)
    with open(MINIMAL_CONFIG_PATH, encoding="utf-8") as f:
        config = f.read()
    project.label_config = config
    project.parsed_label_config = None  # force re-parse
    project.save()
    print("Updated project to minimal label config. Refresh the page and click Label again.")


if __name__ == "__main__":
    main()
