#!/usr/bin/env python3
"""
Create or fix Label Studio annotator accounts (ann1, ann2) with passwords.
The API creates users but does not set a password, so they cannot log in.
Run this after setup_label_studio.sh (or when ann1/ann2 logins fail).

Usage (from repo root):
  LABEL_STUDIO_BASE_DATA_DIR=.label_studio_data DJANGO_DB=sqlite \
    .ls_venv/bin/python scripts/set_label_studio_passwords.py
"""
import os
import sys

# Label Studio needs these before Django loads
os.environ.setdefault("LABEL_STUDIO_BASE_DATA_DIR", ".label_studio_data")
os.environ.setdefault("DJANGO_DB", "sqlite")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "label_studio.core.settings.label_studio")

# Settings use "from core.settings.base" — need label_studio package dir on path
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

ANNOTATORS = [
    ("ann1@juakazi.ai", "annotator1pass", "ann1"),
    ("ann2@juakazi.ai", "annotator2pass", "ann2"),
]


def main():
    org = Organization.objects.first()
    if not org:
        print("No organization found. Run setup_label_studio.sh first.", file=sys.stderr)
        sys.exit(1)
    project = Project.objects.first()

    for email, password, username in ANNOTATORS:
        uname = username or email.split("@")[0]
        try:
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
            created = False
        except User.DoesNotExist:
            user = User.objects.create_user(
                email=email, password=password, username=uname,
                first_name="Annotator", last_name=uname,
            )
            created = True
        org.add_user(user)
        user.active_organization = org
        user.save(update_fields=["active_organization"])
        if project:
            project.add_collaborator(user)
        print(f"{'Created' if created else 'Updated'} {email} (password set)")
    print("Done. Annotators can log in at http://localhost:8080")


if __name__ == "__main__":
    main()
