#!/usr/bin/env python3
"""Generate Jekyll publication pages from a BibTeX file.

Usage:
    python scripts/update_publications.py

This reads _data/publications.bib and writes markdown files into _publications/.
Update the BibTeX file and rerun the script whenever you want to refresh the site.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
BIB_PATH = ROOT / "_data" / "publications.bib"
OUTPUT_DIR = ROOT / "_publications"

try:
    from pybtex.database.input import bibtex
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "pybtex is required. Install it with: python -m pip install pybtex"
    ) from exc


def clean_text(value: str) -> str:
    return (
        value.replace("{", "")
        .replace("}", "")
        .replace("\\", "")
        .replace("\n", " ")
        .strip()
    )


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "publication"


def format_authors(entry) -> str:
    authors = entry.persons.get("author", [])
    if not authors:
        return "Anonymous"

    names = []
    for author in authors:
        first = " ".join(author.first_names).strip()
        last = " ".join(author.last_names).strip()
        if first and last:
            names.append(f"{first} {last}")
        elif last:
            names.append(last)

    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} & {names[1]}"
    return ", ".join(names[:-1]) + f", & {names[-1]}"


def parse_month(month: str) -> str:
    if not month:
        return "01"
    key = month.strip().lower()
    mapping = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05",
        "jun": "06", "jul": "07", "aug": "08", "sep": "09", "oct": "10",
        "nov": "11", "dec": "12"
    }
    if key in mapping:
        return mapping[key]
    if key.isdigit() and len(key) == 1:
        return f"0{key}"
    if key.isdigit() and len(key) == 2:
        return key
    return "01"


def make_citation(entry) -> str:
    authors = format_authors(entry)
    title = clean_text(entry.fields.get("title", "Untitled"))
    year = entry.fields.get("year", "1900")

    venue = (
        entry.fields.get("journal")
        or entry.fields.get("booktitle")
        or entry.fields.get("publisher")
        or entry.fields.get("venue")
        or ""
    )
    venue = clean_text(venue)

    if venue:
        return f'{authors} ({year}). "{title}." {venue}, {year}.'
    return f'{authors} ({year}). "{title}." {year}.'


def make_excerpt(entry) -> str:
    url = clean_text(entry.fields.get("url", ""))
    doi = clean_text(entry.fields.get("doi", ""))
    if url:
        return f"[Link]({url})"
    if doi:
        return f"[DOI](https://doi.org/{doi})"
    return ""


def render_file(entry, key: str) -> str:
    title = clean_text(entry.fields.get("title", "Untitled"))
    year = entry.fields.get("year", "1900")
    month = parse_month(entry.fields.get("month", ""))
    day = entry.fields.get("day", "01")
    if day.isdigit() and len(day) == 1:
        day = f"0{day}"

    date = f"{year}-{month}-{day}"
    venue = (
        entry.fields.get("journal")
        or entry.fields.get("booktitle")
        or entry.fields.get("publisher")
        or entry.fields.get("venue")
        or ""
    )
    venue = clean_text(venue)
    url = clean_text(entry.fields.get("url", ""))
    doi = clean_text(entry.fields.get("doi", ""))
    abstract = clean_text(entry.fields.get("abstract", ""))
    excerpt = make_excerpt(entry)
    slug = slugify(title)

    front_matter = [
        "---",
        f"title: \"{title}\"",
        "collection: publications",
        "category: manuscripts",
        f"permalink: /publication/{slug}",
        f"excerpt: '{excerpt}'" if excerpt else "excerpt: ''",
        f"date: {date}",
        f"venue: '{venue}'" if venue else "venue: ''",
        f"paperurl: '{url}'" if url else "paperurl: ''",
        f"doi: '{doi}'" if doi else "doi: ''",
        f"citation: >-",
        f"  {make_citation(entry)}",
        "---",
        "",
    ]

    body_lines = []
    if abstract:
        body_lines.append(abstract)
    if url:
        body_lines.append("")
        body_lines.append(f"[Read the paper]({url})")
    elif doi:
        body_lines.append("")
        body_lines.append(f"[DOI](https://doi.org/{doi})")

    return "\n".join(front_matter + body_lines) + "\n"


def main() -> None:
    if not BIB_PATH.exists():
        raise SystemExit(f"BibTeX file not found: {BIB_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for stale_file in OUTPUT_DIR.glob("*.md"):
        stale_file.unlink()

    parser = bibtex.Parser()
    bib_data = parser.parse_file(str(BIB_PATH))

    generated = 0
    for key in sorted(bib_data.entries):
        entry = bib_data.entries[key]
        rendered = render_file(entry, key)
        slug = slugify(clean_text(entry.fields.get("title", "Untitled")))
        filename = f"{entry.fields.get('year', '1900')}-{slug}.md"
        output_path = OUTPUT_DIR / filename
        output_path.write_text(rendered, encoding="utf-8")
        generated += 1

    print(f"Generated {generated} publication pages from {BIB_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
