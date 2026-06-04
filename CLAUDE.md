# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A static personal library website generated from a local Calibre ebook library. The site displays book covers organized by author, with search, A-Z filtering, and sidebar navigation.

## How to apply any change

**Never edit `index.html` directly.** All changes go into `generate.py`, then regenerate:

```bash
python3 generate.py
```

This reads the Calibre library, copies missing covers, and writes `index.html` from scratch.

## Key paths

| Path | Purpose |
|---|---|
| `generate.py` | Single source of truth — reads Calibre, writes `index.html` |
| `index.html` | Generated output (do not edit manually) |
| `covers/` | Cover images copied from Calibre (`{AuthorFolder}/{index}.jpg`) |
| `/Users/francescbox/Documents/2 AREES/Calibre` | Calibre library root (`{Author}/{Book Title (id)}/`) |

## Calibre library structure

```
Calibre/
  {Author Name}/
    {Book Title (calibre_id)}/
      cover.jpg
      metadata.opf   ← contains <dc:title>, <dc:description>, <dc:creator>, etc.
      *.epub
```

`metadata.opf` is standard OPF/XML. The synopsis is in `<dc:description>` and may contain HTML tags that need stripping.

## generate.py architecture

1. **Collect books**: iterates Calibre authors/books, copies missing covers to `covers/`, builds `library` dict: `{author_name: [{title, src, synopsis}]}`
2. **Build HTML**: f-string template with inlined CSS, static HTML sections, and a `<script>` block — all in one file output

### Key functions
- `clean_title(folder_name)` — strips the trailing ` (id)` from Calibre folder names
- `anchor(author)` — slugifies author name for HTML `id` attributes
- `rel_url(path)` — URL-encodes the relative path to a cover image
- `read_synopsis(opf_path)` — parses OPF XML, strips HTML tags from `<dc:description>`

## CSS/JS patterns in the template

- Variables in the f-string template use `{{` / `}}` to escape Python's f-string braces
- CSS custom properties defined in `:root` — `--bg`, `--surface`, `--accent`, `--sidebar-w`, `--topbar-h`
- Book cards: `<figure class="book-card">` with an absolutely-positioned `<figcaption>` overlay and an optional `<div class="book-synopsis">` below the image
- JS adds `.has-synopsis` class at runtime to cards that have a synopsis div, enabling `cursor: pointer`
- Active author highlighting uses `IntersectionObserver` on `<section data-author="...">` elements
