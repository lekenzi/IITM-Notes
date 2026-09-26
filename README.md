# IITM Notes

Notes for the IIT Madras BS Degree, published with GitHub Pages (MkDocs Material).
Everything is driven by folder and file names — there is no navigation file to edit.

## Adding notes

```
docs/
├── index.md                     home page (subject cards are generated)
├── maths-1/                     -> tab "Maths 1"
│   ├── week-1/                  -> section "Week 1"
│   │   ├── lecture-notes.pdf    -> page "Lecture Notes" (embedded PDF viewer)
│   │   ├── sets_and_functions.md
│   │   └── graphs.tex           -> compiled to PDF on deploy (TikZ works)
│   └── week-2/
└── textbooks/                   -> tab "Textbooks" (always last)
    └── maths-1/
        └── some-book.pdf
```

- **Names become titles**: `-`, `_` and spaces become spaces and lowercase words get
  capitalised; words that already have capitals stay as they are (`DBMS`, `L1.2`).
- **Ordering is numeric**: `week-2` comes before `week-10`.
- **PDFs**: every PDF gets its own page with a viewer plus Open/Download buttons.
- **LaTeX**: any `.tex` file with `\documentclass` is compiled to a PDF next to it
  (files without it are treated as `\input` partials). The `.tex` source is offered as a download.
- **Markdown**: supports `$maths$`, `$$display maths$$`, and ` ```mermaid ` diagrams.
  To use a different title, add front matter: `title: My Title`.

## One-time GitHub setup

1. Push this folder to a GitHub repo on the `main` branch.
2. Repo **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Every push to `main` rebuilds the site at `https://<username>.github.io/<repo>/`.

## Local preview (optional)

```sh
pip install -r requirements.txt
python scripts/build_tex.py   # needs Tectonic or MiKTeX; skipped if neither is installed
mkdocs serve                  # http://127.0.0.1:8000
```

## Limits to keep in mind

- GitHub rejects files over **100 MB**; the published site should stay under about **1 GB**.
  Large textbooks can hit both limits.
