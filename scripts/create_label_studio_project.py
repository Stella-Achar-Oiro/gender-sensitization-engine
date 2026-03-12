#!/usr/bin/env python3
"""
Create the JuaKazi Label Studio project, import kappa tasks, and add members.
Run when you don't see any project after logging in (API create may have failed).

Usage (from repo root):
  LABEL_STUDIO_BASE_DATA_DIR=.label_studio_data DJANGO_DB=sqlite \
    .ls_venv/bin/python scripts/create_label_studio_project.py
"""
import os
import sys
import csv

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

from users.models import User
from organizations.models import Organization
from projects.models import Project
from tasks.models import Task

KAPPA_CSV = os.path.join(repo_root, "data", "annotation_export", "batch_for_annotator_B_kappa_overlap.csv")
# Use minimal config to avoid blank screen (full config uses visibleWhen/styles that can crash UI)
XML_CONFIG = os.path.join(repo_root, "scripts", "label_studio_config_minimal.xml")
if not os.path.isfile(XML_CONFIG):
    XML_CONFIG = os.path.join(repo_root, "scripts", "label_studio_config.xml")


def main():
    org = Organization.objects.first()
    if not org:
        print("No organization. Run setup_label_studio.sh first.", file=sys.stderr)
        sys.exit(1)
    admin = User.objects.filter(email="admin@juakazi.ai").first()
    if not admin:
        print("Admin user not found.", file=sys.stderr)
        sys.exit(1)

    # Avoid duplicate project
    existing = Project.objects.filter(title__icontains="JuaKazi").first()
    if existing:
        print(f"Project already exists: {existing.title} (id={existing.id})")
        print("Add yourself: log in as admin, open project → Settings → Members, add ann1/ann2")
        return

    with open(XML_CONFIG, encoding="utf-8") as f:
        label_config = f.read()

    project = Project.objects.create(
        title="JuaKazi — Swahili Kappa Overlap",
        description="Inter-annotator agreement set. Both annotators review every row independently.",
        label_config=label_config,
        organization=org,
        created_by=admin,
        maximum_annotations=2,
        overlap_cohort_percentage=100,
    )
    project.add_collaborator(admin)
    for email in ("ann1@juakazi.ai", "ann2@juakazi.ai"):
        try:
            u = User.objects.get(email=email)
            project.add_collaborator(u)
        except User.DoesNotExist:
            pass

    if not os.path.isfile(KAPPA_CSV):
        print(f"Kappa CSV not found: {KAPPA_CSV}", file=sys.stderr)
        print("Project created with 0 tasks. Import CSV from Label Studio UI or create the file.")
        return

    tasks = []
    with open(KAPPA_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tasks.append(
                Task(
                    project=project,
                    data={"id": row.get("id", ""), "text": row.get("text", "")},
                    overlap=2,
                )
        )
    # Bulk create in chunks to avoid huge INSERT
    chunk = 500
    for i in range(0, len(tasks), chunk):
        Task.objects.bulk_create(tasks[i : i + chunk])
    print(f"Created project id={project.id}, imported {len(tasks)} tasks.")
    print("Restart Label Studio or refresh the page — you should see the project.")


if __name__ == "__main__":
    main()
