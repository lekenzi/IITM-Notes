"""Builds the site structure from folder/file names, so there's no nav to maintain.

    docs/maths-1/week-2/sets_and_functions.pdf
      -> tab "Maths 1" > section "Week 2" > page "Sets And Functions"

- Every PDF gets a generated page with an embedded viewer.
- A .tex file (with \\documentclass) is shown via its compiled PDF; if it hasn't been
  compiled (e.g. local preview without LaTeX), its source is shown instead.
- Separators (-, _, spaces) become spaces; lowercase words are capitalised,
  words with capitals are kept as-is (DBMS, OPPE, L1.2 stay untouched).
- Sorting is "natural" (week-2 before week-10), and the textbooks folder goes last.
- A Markdown page can override its title with front matter:  title: Foo
- On the home page, the marker <!-- SUBJECTS --> is replaced with subject cards.
"""
import html
import json
import posixpath
import re

from mkdocs.structure.files import File, Files
from mkdocs.structure.nav import Section

INDEX_NAMES = {"index", "readme"}
TEXTBOOKS_DIR = "textbooks"
SUBJECTS_MARKER = "<!-- SUBJECTS -->"
KNOWN_EXTS = {".md", ".pdf", ".tex"}

_doc_files = []


def prettify(name):
    stem, ext = posixpath.splitext(name)
    if ext.lower() in KNOWN_EXTS:
        name = stem
    words = [w for w in re.split(r"[\s_-]+", name.strip()) if w]
    return " ".join(w if any(c.isupper() for c in w) else w.capitalize() for w in words)


def _natural(text):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", text)]


def _sort_key(file):
    *dirs, filename = file.src_uri.split("/")
    stem = posixpath.splitext(filename)[0].lower()
    in_textbooks = bool(dirs) and dirs[0].lower() == TEXTBOOKS_DIR
    return (in_textbooks, [_natural(d) for d in dirs], stem not in INDEX_NAMES, _natural(filename))


def _ext(file):
    return posixpath.splitext(file.src_uri)[1].lower()


def _relative_url(page_file, target_file):
    # File.url values are already percent-encoded.
    base = page_file.url if page_file.url.endswith("/") else posixpath.dirname(page_file.url)
    return posixpath.relpath(target_file.url, base or ".")


def _new_page(files, config, source, suffix):
    stem = posixpath.splitext(source.src_uri)[0]
    src_uri = stem + ".md"
    if files.get_file_from_path(src_uri):  # a hand-written note already uses that name
        src_uri = f"{stem}-{suffix}.md"
    page = File.generated(config, src_uri, content="")
    files.append(page)
    return page


def _add_pdf_page(files, config, pdf):
    page = _new_page(files, config, pdf, "pdf")
    title = prettify(posixpath.basename(pdf.src_uri))
    url = _relative_url(page, pdf)

    buttons = [
        f'<a class="md-button md-button--primary" href="{url}" target="_blank">Open</a>',
        f'<a class="md-button" href="{url}" download>Download</a>',
    ]
    tex = files.get_file_from_path(posixpath.splitext(pdf.src_uri)[0] + ".tex")
    if tex:
        buttons.append(f'<a class="md-button" href="{_relative_url(page, tex)}" download>LaTeX source</a>')

    page.content_string = (
        f"---\ntitle: {json.dumps(title)}\nhide: [toc]\n---\n\n"
        f'<div class="pdf-actions">{" ".join(buttons)}</div>\n\n'
        f'<iframe class="pdf-viewer" src="{url}" title="{html.escape(title)}"></iframe>\n'
    )


def _add_uncompiled_tex_page(files, config, tex):
    if files.get_file_from_path(posixpath.splitext(tex.src_uri)[0] + ".pdf"):
        return  # the PDF page covers it
    with open(tex.abs_src_path, encoding="utf-8", errors="replace") as fh:
        source = fh.read()
    if "\\documentclass" not in source:
        return  # a partial pulled in via \input, not a document of its own

    page = _new_page(files, config, tex, "tex")
    title = prettify(posixpath.basename(tex.src_uri))
    page.content_string = (
        f"---\ntitle: {json.dumps(title)}\n---\n\n"
        "!!! note\n    This file hasn't been compiled yet — the PDF is built automatically on deploy.\n\n"
        f"~~~~latex\n{source}\n~~~~\n"
    )


def on_files(files, config):
    for f in list(files):
        if _ext(f) == ".pdf":
            _add_pdf_page(files, config, f)
        elif _ext(f) == ".tex":
            _add_uncompiled_tex_page(files, config, f)

    # MkDocs builds the auto-nav in file order, so sorting here orders the nav.
    global _doc_files
    ordered = sorted(files, key=_sort_key)
    _doc_files = [f for f in ordered if f.is_documentation_page()]
    return Files(ordered)


def _first_page(section):
    for child in section.children:
        if isinstance(child, Section):
            page = _first_page(child)
            if page:
                return page
        elif getattr(child, "file", None):
            return child
    return None


def _title_sections(items, depth):
    for item in items:
        if isinstance(item, Section):
            page = _first_page(item)
            if page:
                item.title = prettify(page.file.src_uri.split("/")[depth])
            _title_sections(item.children, depth + 1)


def on_nav(nav, config, files):
    _title_sections(nav.items, 0)
    return nav


def on_page_markdown(markdown, page, config, files):
    if "title" not in page.meta:
        parts = page.file.src_uri.split("/")
        stem = posixpath.splitext(parts[-1])[0]
        if stem.lower() in INDEX_NAMES:
            page.meta["title"] = prettify(parts[-2]) if len(parts) > 1 else "Home"
        else:
            page.meta["title"] = prettify(stem)

    if page.file.src_uri == "index.md" and SUBJECTS_MARKER in markdown:
        markdown = markdown.replace(SUBJECTS_MARKER, _subject_cards())
    return markdown


def _subject_cards():
    # subject -> group (week, or textbook subject) -> first page in it; files are pre-sorted
    subjects = {}
    for f in _doc_files:
        parts = f.src_uri.split("/")
        if len(parts) < 2:
            continue
        group = parts[1]
        subjects.setdefault(parts[0], {}).setdefault(group, f)

    if not subjects:
        return "_No notes yet — add a subject folder under `docs/`._"

    cards = []
    for subject, groups in subjects.items():
        links = [f"[{prettify(group)}]({f.url})" for group, f in groups.items()]
        cards.append(f"-   **{prettify(subject)}**\n\n    ---\n\n    " + " · ".join(links))
    return '<div class="grid cards" markdown>\n\n' + "\n\n".join(cards) + "\n\n</div>"
