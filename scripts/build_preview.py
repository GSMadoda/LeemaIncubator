"""Render the Hub's pages to static HTML for the public preview.

The Hub is a Django application: it needs Python, a database and a signed-in
user, none of which GitHub Pages provides. This renders the real views through
Django's test client against a throwaway database of demo data, and writes the
output as flat files that any static host can serve.

What comes out is the Hub's own templates and stylesheet, with working links
between pages. It is a photograph, not the application: nothing submits,
nothing saves, and the figures are the fictional demo cohort.

    python scripts/build_preview.py [--base /LeemaIncubator/preview] [--out preview]
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

BANNER = """<div style="background:#E8B820;color:#1a1a1a;font:600 15px/1.5 Barlow,system-ui,sans-serif;\
padding:12px 20px;text-align:center">
<strong>Static preview.</strong> These are the Incubation Hub's real pages, rendered from fictional demo data
so the interface can be read without installing it. Nothing here saves, submits or signs in &mdash; the working
application needs a server, a database and an account.
<br><a href="{base}/site/" style="color:#1a1a1a">The Leema Township Incubator website &rarr;</a>
</div>"""


def rewrite(html: str, base: str, depth: int) -> str:
    """Point absolute Django URLs at the static tree, and neutralise what cannot work."""
    # /static/... and every app URL become <base>-prefixed paths.
    html = re.sub(r'(href|src)="/(?!/)', rf'\1="{base}/', html)
    html = html.replace(f'{base}/static/', f'{base}/static/')
    # The admin and the CSV export are not part of a static build.
    html = re.sub(
        r'<a href="[^"]*/admin/[^"]*"[^>]*>(.*?)</a>',
        r'<span title="Not available in the static preview" style="opacity:.45">\1</span>',
        html,
    )
    # Forms cannot post anywhere; make that visible rather than silently broken.
    html = re.sub(r'<form([^>]*)method="post"([^>]*)>', r'<form\1onsubmit="return false"\2>', html, flags=re.I)
    return html.replace("</body>", "</body>")


def write(out: Path, url_path: str, html: str) -> Path:
    target = out / url_path.strip("/") / "index.html" if url_path.strip("/") else out / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
    return target


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="/LeemaIncubator/preview",
                    help="URL prefix the preview is served under, no trailing slash")
    ap.add_argument("--out", default="preview", help="output directory, relative to the repository root")
    args = ap.parse_args()

    base = args.base.rstrip("/")
    out = BASE_DIR / args.out

    tmp = Path(tempfile.mkdtemp(prefix="hub-preview-"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hub.settings")
    os.environ["DJANGO_DEBUG"] = "1"
    os.environ["HUB_DB_PATH"] = str(tmp / "preview.sqlite3")
    os.environ["DJANGO_ALLOWED_HOSTS"] = "testserver"  # the test client's own host
    sys.path.insert(0, str(BASE_DIR))

    import django
    django.setup()
    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.test import Client

    call_command("migrate", verbosity=0)
    call_command("seed_demo", verbosity=0)

    from incubator.models import Enterprise

    User = get_user_model()
    User.objects.create_superuser("preview", "preview@example.invalid", "preview-only-not-a-real-password")
    client = Client()
    client.login(username="preview", password="preview-only-not-a-real-password")

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    paths = ["/", "/enterprises/", "/reports/", "/apply/", "/apply/received/"]
    paths += [f"/enterprises/{pk}/" for pk in Enterprise.objects.values_list("pk", flat=True)]

    written = 0
    for path in paths:
        response = client.get(path)
        if response.status_code != 200:
            print(f"  SKIP {path} -> HTTP {response.status_code}")
            continue
        html = response.content.decode("utf-8")
        html = rewrite(html, base, path.count("/") - 1)
        html = html.replace("<body>", "<body>\n" + BANNER.format(base=base), 1)
        target = write(out, path, html)
        written += 1
        print(f"  {path:32} -> {target.relative_to(BASE_DIR)}")

    # The stylesheet the templates ask for, at the path they ask for it.
    css_src = BASE_DIR / "static" / "hub" / "hub.css"
    css_dst = out / "static" / "hub" / "hub.css"
    css_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(css_src, css_dst)

    # The quarterly export, as the real thing produces it.
    csv = client.get("/reports/export.csv")
    if csv.status_code == 200:
        (out / "reports").mkdir(parents=True, exist_ok=True)
        (out / "reports" / "export.csv").write_bytes(csv.content)
        print(f"  /reports/export.csv              -> {(out / 'reports' / 'export.csv').relative_to(BASE_DIR)}")

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{written} pages written to {out.relative_to(BASE_DIR)}/ for base {base}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
