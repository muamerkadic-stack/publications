#!/usr/bin/env python3
"""
Fetch a Google Scholar profile with the free `scholarly` library and build index.html.

Environment variables:
  SCHOLAR_ID    - the "user=" value from your Google Scholar profile URL
  FILL_DETAILS  - "1" to also fetch the full author list of every paper
                  (slower, and more likely to be blocked by Google). Default "0".

If Google blocks the direct request, the script retries through free proxies.
If everything fails, the existing index.html is left untouched.
"""
import html
import os
import sys
import time
import warnings
from collections import OrderedDict
from datetime import datetime, timezone

warnings.filterwarnings("ignore")
from scholarly import scholarly, ProxyGenerator  # noqa: E402

OUTPUT = "index.html"


def fetch(scholar_id, fill_details):
    author = scholarly.search_author_id(scholar_id)
    author = scholarly.fill(author, sections=["basics", "indices", "publications"])
    pubs = author.get("publications", [])
    if fill_details:
        filled = []
        for p in pubs:
            try:
                filled.append(scholarly.fill(p))
                time.sleep(2)
            except Exception as exc:  # keep the short version if one paper fails
                print(f"  could not fill '{p['bib'].get('title')}': {exc}")
                filled.append(p)
        pubs = filled
    return author, pubs


def fetch_with_retries(scholar_id, fill_details):
    attempts = [("direct", None)] + [("free proxy", "free")] * 3
    for i, (label, mode) in enumerate(attempts, 1):
        try:
            if mode == "free":
                pg = ProxyGenerator()
                pg.FreeProxies()
                scholarly.use_proxy(pg)
            print(f"Attempt {i} ({label})…")
            author, pubs = fetch(scholar_id, fill_details)
            if pubs:
                return author, pubs
            print("  no publications returned")
        except Exception as exc:
            print(f"  failed: {exc}")
        time.sleep(5)
    return None, []


def render(author, pubs, scholar_id):
    e = html.escape
    groups = OrderedDict()
    for p in sorted(pubs, key=lambda p: str(p["bib"].get("pub_year") or "0"), reverse=True):
        groups.setdefault(str(p["bib"].get("pub_year") or "Undated"), []).append(p)

    sections = []
    for year, items in groups.items():
        lis = []
        for p in items:
            bib = p.get("bib", {})
            title = e(bib.get("title", "Untitled"))
            pub_id = p.get("author_pub_id")
            link = p.get("pub_url") or (
                f"https://scholar.google.com/citations?view_op=view_citation&citation_for_view={pub_id}"
                if pub_id else None
            )
            title_html = f'<a href="{e(link)}">{title}</a>' if link else title
            authors = bib.get("author", "")
            authors_html = f'<div class="authors">{e(authors.replace(" and ", ", "))}</div>' if authors else ""
            venue = bib.get("citation") or bib.get("journal") or bib.get("conference") or bib.get("venue") or ""
            cites = p.get("num_citations")
            cites_html = f'<span class="cites">Cited by {cites}</span>' if cites else ""
            lis.append(
                f'<li><div class="title">{title_html}</div>{authors_html}'
                f'<div class="venue">{e(venue)} {cites_html}</div></li>'
            )
        sections.append(f'<h2>{e(year)}</h2><ul>{"".join(lis)}</ul>')

    parts = [f"{len(pubs)} publications"]
    if author.get("citedby") is not None:
        parts.append(f"{author['citedby']} citations")
    if author.get("hindex") is not None:
        parts.append(f"h-index {author['hindex']}")
    if author.get("i10index") is not None:
        parts.append(f"i10-index {author['i10index']}")
    stats = " · ".join(parts)
    updated = datetime.now(timezone.utc).strftime("%d %B %Y")
    profile = f"https://scholar.google.com/citations?user={scholar_id}"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Publications – {e(author.get("name", ""))}</title>
<base target="_blank">
<style>
  body {{ font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif; color: #222;
         max-width: 900px; margin: 0 auto; padding: 16px; line-height: 1.45; background: #fff; }}
  .stats {{ color: #555; font-size: 0.95em; margin-bottom: 8px; }}
  #filter {{ width: 100%; padding: 8px 10px; font-size: 1em; border: 1px solid #ccc;
            border-radius: 6px; box-sizing: border-box; margin: 8px 0 4px; }}
  h2 {{ font-size: 1.15em; border-bottom: 2px solid #e5e5e5; padding-bottom: 4px; margin-top: 28px; }}
  ul {{ list-style: none; padding: 0; margin: 0; }}
  li {{ padding: 10px 0; border-bottom: 1px solid #f0f0f0; }}
  .title {{ font-weight: 600; }}
  .title a {{ color: #1a5fb4; text-decoration: none; }}
  .title a:hover {{ text-decoration: underline; }}
  .authors {{ color: #444; font-size: 0.93em; }}
  .venue {{ color: #777; font-size: 0.9em; font-style: italic; }}
  .cites {{ font-style: normal; background: #eef3fb; color: #1a5fb4; border-radius: 4px;
           padding: 1px 6px; margin-left: 6px; font-size: 0.85em; }}
  footer {{ color: #999; font-size: 0.8em; margin-top: 24px; }}
  footer a {{ color: #999; }}
</style>
</head>
<body>
<div class="stats">{e(stats)}</div>
<input id="filter" type="search" placeholder="Search publications…" aria-label="Search publications">
{"".join(sections)}
<footer>Source: <a href="{e(profile)}">Google Scholar</a> · last updated {updated}</footer>
<script>
  document.getElementById("filter").addEventListener("input", function () {{
    var q = this.value.toLowerCase();
    document.querySelectorAll("ul").forEach(function (ul) {{
      var shown = 0;
      ul.querySelectorAll("li").forEach(function (li) {{
        var ok = li.textContent.toLowerCase().indexOf(q) !== -1;
        li.style.display = ok ? "" : "none";
        if (ok) shown++;
      }});
      ul.previousElementSibling.style.display = shown ? "" : "none";
    }});
  }});
</script>
</body>
</html>
"""


def main():
    scholar_id = os.environ.get("SCHOLAR_ID")
    if not scholar_id:
        sys.exit("Set the SCHOLAR_ID environment variable.")
    fill_details = os.environ.get("FILL_DETAILS", "0") == "1"

    author, pubs = fetch_with_retries(scholar_id, fill_details)
    if not pubs:
        # Never overwrite a good page with an empty one
        sys.exit("Google Scholar could not be reached – keeping the existing page. "
                 "It will try again at the next scheduled run.")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(render(author, pubs, scholar_id))
    print(f"Wrote {OUTPUT} with {len(pubs)} publications.")


if __name__ == "__main__":
    main()
