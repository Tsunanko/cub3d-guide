"""Auto-insert breadcrumb navigation at the top of every non-home page.

Renders a line like:
    [🏠 ホーム](../index.md) › [cpp00](index.md) › **ex00 Megaphone**

This gives readers a consistent way to (a) see where they are in the
hierarchy and (b) jump back to the top from any page.
"""

import os.path


def _rel_md(target_src, page_src):
    """Return target's path relative to the page's directory."""
    page_dir = os.path.dirname(page_src) or "."
    return os.path.relpath(target_src, page_dir)


def on_page_markdown(markdown, page, config, files):
    if page.is_homepage:
        return markdown

    if not hasattr(page, "file") or not page.file:
        return markdown

    page_src = page.file.src_path

    home_path = _rel_md("index.md", page_src)
    crumbs = [f"[🏠 ホーム]({home_path})"]

    ancestors = []
    parent = page.parent
    while parent:
        ancestors.append(parent)
        parent = parent.parent
    ancestors.reverse()

    for ancestor in ancestors:
        title = (ancestor.title or "").strip()
        rel = None
        if hasattr(ancestor, "file") and ancestor.file:
            rel = _rel_md(ancestor.file.src_path, page_src)
        elif hasattr(ancestor, "children"):
            for child in ancestor.children:
                if (
                    hasattr(child, "file")
                    and child.file
                    and child.file.src_path.endswith("index.md")
                ):
                    rel = _rel_md(child.file.src_path, page_src)
                    break
        if rel:
            crumbs.append(f"[{title}]({rel})")
        else:
            crumbs.append(title)

    crumbs.append(f"**{page.title}**")

    breadcrumb = " › ".join(crumbs)
    return f"{breadcrumb}\n\n{markdown}"
