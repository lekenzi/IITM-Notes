"""Compile every standalone .tex file under docs/ into a PDF next to it.

Uses Tectonic if installed (what CI uses), otherwise latexmk (MiKTeX / TeX Live).
Files without \\documentclass are treated as partials and skipped.
"""
import shutil
import subprocess
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"


def compile_cmd(tex):
    if shutil.which("tectonic"):
        return ["tectonic", tex.name]
    if shutil.which("latexmk"):
        return ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", tex.name]
    return None


def main():
    docs = [p for p in DOCS.rglob("*.tex")
            if "\\documentclass" in p.read_text(encoding="utf-8", errors="replace")]
    if not docs:
        print("No LaTeX documents found.")
        return 0
    if compile_cmd(docs[0]) is None:
        print("No LaTeX compiler found (install Tectonic or MiKTeX); skipping.")
        return 0

    failed = []
    for tex in docs:
        print(f"Compiling {tex.relative_to(DOCS)}")
        if subprocess.run(compile_cmd(tex), cwd=tex.parent).returncode != 0:
            failed.append(tex)
        elif shutil.which("latexmk") and not shutil.which("tectonic"):
            subprocess.run(["latexmk", "-c", tex.name], cwd=tex.parent)  # tidy aux files

    for tex in failed:
        print(f"FAILED: {tex.relative_to(DOCS)}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
