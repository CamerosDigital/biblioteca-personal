#!/usr/bin/env python3
"""Generate index.html for the personal library website."""

import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from html import escape
from urllib.parse import quote

CALIBRE_ROOT = Path("/Users/francescbox/Documents/2 AREES/Calibre")
PROJECT_DIR  = Path(__file__).parent
OUTPUT       = PROJECT_DIR / "index.html"
COVERS_DIR   = PROJECT_DIR / "covers"

def clean_title(folder_name):
    return re.sub(r'\s*\(\d+\)$', '', folder_name).strip()

def read_synopsis(opf_path):
    try:
        tree = ET.parse(opf_path)
        root = tree.getroot()
        ns = {'dc': 'http://purl.org/dc/elements/1.1/'}
        desc_el = root.find('.//dc:description', ns)
        if desc_el is None or not desc_el.text:
            return ''
        text = re.sub(r'<[^>]+>', ' ', desc_el.text)
        return re.sub(r'\s+', ' ', text).strip()
    except Exception:
        return ''

def anchor(author):
    return re.sub(r'[^a-z0-9]', '-', author.lower())

def rel_url(path: Path) -> str:
    """Return a URL-encoded relative path from PROJECT_DIR to path."""
    return '/'.join(quote(part) for part in path.relative_to(PROJECT_DIR).parts)

# Collect books grouped by author and copy covers
library = {}
copied = skipped = 0

for author_dir in sorted(CALIBRE_ROOT.iterdir(), key=lambda p: p.name.lower()):
    if not author_dir.is_dir() or author_dir.name.startswith('.'):
        continue
    books = []
    author_covers = COVERS_DIR / author_dir.name
    for i, book_dir in enumerate(sorted(author_dir.iterdir(), key=lambda p: p.name.lower())):
        if not book_dir.is_dir():
            continue
        cover = book_dir / "cover.jpg"
        if not cover.exists():
            continue
        dest = author_covers / f"{i}.jpg"
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cover, dest)
            copied += 1
        else:
            skipped += 1
        synopsis = read_synopsis(book_dir / 'metadata.opf')
        books.append({
            'title': clean_title(book_dir.name),
            'src': rel_url(dest),
            'synopsis': synopsis,
        })
    if books:
        library[author_dir.name] = books

print(f"Covers: {copied} copied, {skipped} already up to date")

total_books = sum(len(v) for v in library.values())
total_authors = len(library)

# Build A-Z index letters
letters = sorted({a[0].upper() for a in library})

# Generate author nav entries
nav_items = "\n".join(
    f'      <li><a href="#{anchor(a)}" data-author="{escape(a)}">{escape(a)} <span class="count">({len(library[a])})</span></a></li>'
    for a in library
)

# Generate letter tabs
letter_tabs = "\n".join(
    f'      <button class="letter-btn" data-letter="{l}">{l}</button>'
    for l in letters
)

# Generate main content sections
sections = []
for author, books in library.items():
    def card_html(b):
        synopsis_attr = f' data-synopsis="{escape(b["synopsis"])}"' if b.get('synopsis') else ''
        return (
            f'        <figure class="book-card"{synopsis_attr}>\n'
            f'          <img src="{escape(b["src"])}" alt="{escape(b["title"])}" loading="lazy">\n'
            f'          <figcaption>{escape(b["title"])}</figcaption>\n'
            f'        </figure>'
        )
    cards = "\n".join(card_html(b) for b in books)
    sections.append(
        f'    <section id="{anchor(author)}" data-author="{escape(author)}">\n'
        f'      <h2>{escape(author)} <span class="author-count">({len(books)})</span></h2>\n'
        f'      <div class="books-grid">\n{cards}\n      </div>\n'
        f'    </section>'
    )

main_content = "\n".join(sections)

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Biblioteca Personal</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg: #0f0f0f;
      --surface: #1a1a1a;
      --surface2: #242424;
      --border: #2e2e2e;
      --text: #e8e8e8;
      --text-muted: #888;
      --accent: #c8a96e;
      --accent-dim: #9a7a48;
      --sidebar-w: 260px;
      --topbar-h: 56px;
    }}

    html {{ scroll-behavior: smooth; }}

    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 14px;
      line-height: 1.5;
    }}

    /* ── Top bar ── */
    #topbar {{
      position: fixed;
      top: 0; left: 0; right: 0;
      height: var(--topbar-h);
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 0 16px;
      z-index: 200;
    }}

    #menu-toggle {{
      display: none;
      background: none;
      border: none;
      color: var(--text);
      font-size: 22px;
      cursor: pointer;
      padding: 4px 8px;
    }}

    #topbar h1 {{
      font-size: 16px;
      font-weight: 600;
      color: var(--accent);
      white-space: nowrap;
      flex-shrink: 0;
    }}

    #search {{
      flex: 1;
      max-width: 400px;
      padding: 7px 12px;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--surface2);
      color: var(--text);
      font-size: 14px;
      outline: none;
      transition: border-color .2s;
    }}
    #search:focus {{ border-color: var(--accent); }}
    #search::placeholder {{ color: var(--text-muted); }}

    #stats {{
      margin-left: auto;
      color: var(--text-muted);
      font-size: 12px;
      white-space: nowrap;
    }}

    /* ── Layout ── */
    #layout {{
      display: flex;
      padding-top: var(--topbar-h);
      min-height: 100vh;
    }}

    /* ── Sidebar ── */
    #sidebar {{
      width: var(--sidebar-w);
      flex-shrink: 0;
      position: fixed;
      top: var(--topbar-h);
      bottom: 0;
      left: 0;
      background: var(--surface);
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      z-index: 100;
      overflow: hidden;
    }}

    #letter-nav {{
      display: flex;
      flex-wrap: wrap;
      gap: 2px;
      padding: 10px;
      border-bottom: 1px solid var(--border);
    }}

    .letter-btn {{
      background: none;
      border: 1px solid var(--border);
      color: var(--text-muted);
      border-radius: 4px;
      padding: 2px 6px;
      font-size: 11px;
      cursor: pointer;
      transition: all .15s;
    }}
    .letter-btn:hover, .letter-btn.active {{
      background: var(--accent);
      border-color: var(--accent);
      color: #000;
    }}

    #author-list {{
      flex: 1;
      overflow-y: auto;
      padding: 8px 0;
    }}
    #author-list::-webkit-scrollbar {{ width: 4px; }}
    #author-list::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 2px; }}

    #author-list ul {{ list-style: none; }}

    #author-list a {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 6px 14px;
      color: var(--text-muted);
      text-decoration: none;
      font-size: 12px;
      transition: all .15s;
      border-left: 2px solid transparent;
    }}
    #author-list a:hover {{
      color: var(--text);
      background: var(--surface2);
      border-left-color: var(--accent);
    }}
    #author-list a.active {{
      color: var(--accent);
      background: var(--surface2);
      border-left-color: var(--accent);
    }}
    .count {{ color: var(--accent-dim); font-size: 11px; }}

    /* ── Main ── */
    #main {{
      margin-left: var(--sidebar-w);
      flex: 1;
      padding: 24px 20px 48px;
      min-width: 0;
    }}

    section {{
      margin-bottom: 40px;
    }}
    section.hidden {{ display: none; }}
    figure.hidden {{ display: none; }}

    h2 {{
      font-size: 15px;
      font-weight: 600;
      color: var(--accent);
      padding: 8px 0 12px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 14px;
      position: sticky;
      top: var(--topbar-h);
      background: var(--bg);
      z-index: 10;
    }}
    .author-count {{ color: var(--accent-dim); font-weight: 400; font-size: 13px; }}

    /* ── Book grid ── */
    .books-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
      gap: 12px;
    }}

    .book-card {{
      position: relative;
      cursor: default;
    }}

    .book-card.has-synopsis {{
      cursor: pointer;
    }}

    /* ── Synopsis modal ── */
    #synopsis-modal {{
      display: none;
      position: fixed;
      inset: 0;
      z-index: 300;
      background: rgba(0,0,0,.55);
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}
    #synopsis-modal.open {{ display: flex; }}
    #synopsis-box {{
      background: #fff;
      color: #111;
      border-radius: 12px;
      padding: 22px 20px 20px;
      max-width: 400px;
      width: 100%;
      position: relative;
      font-size: 15px;
      line-height: 1.65;
      box-shadow: 0 12px 48px rgba(0,0,0,.4);
    }}
    #synopsis-title {{
      font-weight: 700;
      font-size: 15px;
      margin-bottom: 10px;
      padding-right: 28px;
      color: #111;
    }}
    #synopsis-text {{
      color: #333;
      font-size: 14px;
      line-height: 1.6;
    }}
    #synopsis-close {{
      position: absolute;
      top: 12px; right: 14px;
      background: none;
      border: none;
      font-size: 20px;
      cursor: pointer;
      color: #555;
      line-height: 1;
      padding: 2px 4px;
    }}
    #synopsis-close:hover {{ color: #000; }}

    .book-card img {{
      width: 100%;
      aspect-ratio: 2/3;
      object-fit: cover;
      border-radius: 4px;
      display: block;
      background: var(--surface2);
      transition: transform .2s, box-shadow .2s;
    }}
    .book-card:hover img {{
      transform: translateY(-3px) scale(1.02);
      box-shadow: 0 8px 24px rgba(0,0,0,.6);
    }}

    figcaption {{
      position: absolute;
      bottom: 0; left: 0; right: 0;
      background: linear-gradient(transparent, rgba(0,0,0,.88) 40%);
      color: #fff;
      font-size: 10px;
      line-height: 1.3;
      padding: 20px 6px 6px;
      border-radius: 0 0 4px 4px;
      opacity: 0;
      transition: opacity .2s;
      pointer-events: none;
    }}
    .book-card:hover figcaption {{ opacity: 1; }}

    /* ── No results ── */
    #no-results {{
      display: none;
      text-align: center;
      padding: 80px 20px;
      color: var(--text-muted);
      font-size: 16px;
    }}

    /* ── Responsive ── */
    @media (max-width: 900px) {{
      .books-grid {{ grid-template-columns: repeat(auto-fill, minmax(90px, 1fr)); gap: 10px; }}
    }}

    @media (max-width: 640px) {{
      #menu-toggle {{ display: block; }}
      #sidebar {{
        left: calc(-1 * var(--sidebar-w));
        transition: left .25s ease;
        box-shadow: none;
      }}
      #sidebar.open {{
        left: 0;
        box-shadow: 4px 0 24px rgba(0,0,0,.5);
      }}
      #main {{ margin-left: 0; padding: 16px 12px 40px; }}
      .books-grid {{ grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 8px; }}
      #stats {{ display: none; }}
    }}
  </style>
</head>
<body>

<div id="topbar">
  <button id="menu-toggle" aria-label="Menú">&#9776;</button>
  <h1>&#128218; Biblioteca</h1>
  <input id="search" type="search" placeholder="Buscar libro o autor…" autocomplete="off">
  <div id="stats">{total_books} libros · {total_authors} autores</div>
</div>

<div id="layout">
  <aside id="sidebar">
    <div id="letter-nav">
{letter_tabs}
    </div>
    <nav id="author-list">
      <ul>
{nav_items}
      </ul>
    </nav>
  </aside>

  <main id="main">
{main_content}
    <div id="no-results">No se encontraron resultados.</div>
  </main>
</div>

<div id="synopsis-modal">
  <div id="synopsis-box">
    <button id="synopsis-close">&#10005;</button>
    <div id="synopsis-title"></div>
    <p id="synopsis-text"></p>
  </div>
</div>

<script>
  const search = document.getElementById('search');
  const sections = [...document.querySelectorAll('section[data-author]')];
  const navLinks = [...document.querySelectorAll('#author-list a')];
  const letterBtns = [...document.querySelectorAll('.letter-btn')];
  const noResults = document.getElementById('no-results');
  const sidebar = document.getElementById('sidebar');
  const menuToggle = document.getElementById('menu-toggle');
  let currentLetter = null;

  // Menu toggle (mobile)
  menuToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  document.addEventListener('click', e => {{
    if (!sidebar.contains(e.target) && e.target !== menuToggle) {{
      sidebar.classList.remove('open');
    }}
  }});

  // Close sidebar on nav link click (mobile)
  navLinks.forEach(a => a.addEventListener('click', () => {{
    sidebar.classList.remove('open');
  }}));

  // Search
  search.addEventListener('input', () => {{
    const q = search.value.trim().toLowerCase();
    currentLetter = null;
    letterBtns.forEach(b => b.classList.remove('active'));
    filterSections(q, null);
  }});

  // Letter filter
  letterBtns.forEach(btn => {{
    btn.addEventListener('click', () => {{
      const l = btn.dataset.letter;
      if (currentLetter === l) {{
        currentLetter = null;
        btn.classList.remove('active');
        search.value = '';
        filterSections('', null);
      }} else {{
        currentLetter = l;
        letterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        search.value = '';
        filterSections('', l);
      }}
    }});
  }});

  function filterSections(q, letter) {{
    let visible = 0;
    sections.forEach(sec => {{
      const author = sec.dataset.author.toLowerCase();
      const matchesLetter = !letter || sec.dataset.author[0].toUpperCase() === letter;
      let sectionVisible = false;
      sec.querySelectorAll('figure.book-card').forEach(card => {{
        const title = (card.querySelector('figcaption')?.textContent || '').toLowerCase();
        const matchesQuery = !q || author.includes(q) || title.includes(q);
        const show = matchesLetter && matchesQuery;
        card.classList.toggle('hidden', !show);
        if (show) sectionVisible = true;
      }});
      sec.classList.toggle('hidden', !sectionVisible);
      if (sectionVisible) visible++;
    }});
    noResults.style.display = visible === 0 ? 'block' : 'none';

    // Sync nav
    navLinks.forEach(a => {{
      const sec = document.getElementById(a.getAttribute('href').slice(1));
      a.parentElement.style.display = sec && !sec.classList.contains('hidden') ? '' : 'none';
    }});
  }}

  // Highlight active author in sidebar on scroll
  const observer = new IntersectionObserver(entries => {{
    entries.forEach(entry => {{
      if (entry.isIntersecting) {{
        const id = entry.target.id;
        navLinks.forEach(a => {{
          a.classList.toggle('active', a.getAttribute('href') === '#' + id);
        }});
        // Scroll the active link into view in sidebar
        const active = document.querySelector('#author-list a.active');
        if (active) active.scrollIntoView({{ block: 'nearest' }});
      }}
    }});
  }}, {{ rootMargin: '-20% 0px -70% 0px', threshold: 0 }});

  sections.forEach(s => observer.observe(s));

  // Synopsis modal
  const synopsisModal = document.getElementById('synopsis-modal');
  const synopsisTitle = document.getElementById('synopsis-title');
  const synopsisText  = document.getElementById('synopsis-text');

  function closeModal() {{ synopsisModal.classList.remove('open'); }}
  document.getElementById('synopsis-close').addEventListener('click', closeModal);
  synopsisModal.addEventListener('click', e => {{ if (e.target === synopsisModal) closeModal(); }});
  document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeModal(); }});

  document.querySelectorAll('.book-card[data-synopsis]').forEach(card => {{
    card.classList.add('has-synopsis');
    card.addEventListener('click', () => {{
      synopsisTitle.textContent = card.querySelector('img').alt;
      synopsisText.textContent  = card.dataset.synopsis;
      synopsisModal.classList.add('open');
    }});
  }});
</script>
</body>
</html>
"""

OUTPUT.write_text(html, encoding='utf-8')
print(f"Generated {OUTPUT}")
print(f"  {total_authors} authors, {total_books} books")
