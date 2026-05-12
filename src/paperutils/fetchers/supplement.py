"""PMC supplementary material enumeration via HTML scraping."""

from __future__ import annotations

import re
import urllib.parse
from typing import Any

from paperutils.http import FetchError, get_text
from paperutils.models import PaperMetadata

_SUPP_A_RE = re.compile(
    r"(?is)"
    r"<a\s[^>]*"
    r'data-ga-action\s*=\s*"click_feat_suppl"'
    r"[^>]*>"
    r"(.*?)"  # group 1: link text
    r"</a>"
    r"\s*"
    r'(?:<sup[^>]*>\s*\(\s*([^)]*?)\s*\)\s*</sup>)?',  # group 2: optional size/format
)

_HREF_RE = re.compile(r'''href\s*=\s*"([^"]+)"''', re.IGNORECASE)

_STRIP_TAGS_RE = re.compile(r"<[^>]+>")


def enumerate_supplement(meta: PaperMetadata, timeout: float) -> list[dict[str, Any]]:
    """Scrape the PMC article page for individual supplementary files.

    Returns a list of file dicts with keys ``name``, ``url``, ``size``, ``format``.
    """
    if not meta.pmcid:
        return []
    article_url = f"https://pmc.ncbi.nlm.nih.gov/articles/{meta.pmcid}/"
    try:
        html = get_text(article_url, timeout=timeout)
    except FetchError:
        return []
    return _extract_supplement_files(html, article_url)


def _extract_supplement_files(html: str, article_url: str) -> list[dict[str, Any]]:
    seen = set()
    result: list[dict[str, Any]] = []
    for match in _SUPP_A_RE.finditer(html):
        href = _extract_href(match.group(0))
        if not href or not href.startswith("/articles/instance/"):
            continue
        abs_url = urllib.parse.urljoin(article_url, href)
        if abs_url in seen:
            continue
        seen.add(abs_url)

        name = _url_filename(abs_url)
        link_text = _STRIP_TAGS_RE.sub("", match.group(1)).strip()
        size, fmt = _parse_size_format(match.group(2) or "")
        if not fmt:
            fmt = _format_from_extension(name)

        result.append({"name": name, "url": abs_url, "size": size, "format": fmt})
    return result


def _extract_href(tag: str) -> str | None:
    m = _HREF_RE.search(tag)
    return m.group(1) if m else None


def _url_filename(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.rstrip("/")
    name = path.rsplit("/", 1)[-1] if path else ""
    if not name:
        name = url.rstrip("/").rsplit("/", 1)[-1]
    return name


def _parse_size_format(sup_text: str) -> tuple[str | None, str]:
    text = sup_text.strip()
    if not text:
        return None, ""
    if "," in text:
        size_part, fmt_part = text.rsplit(",", 1)
        size_part = size_part.strip()
        fmt_part = fmt_part.strip()
    else:
        size_part = text.strip()
        fmt_part = ""
    if size_part and re.match(r"^[\d.]+(?:KB|MB|GB|B)?$", size_part):
        return size_part, fmt_part.lower()
    if not fmt_part:
        return None, text.strip().lower()
    return None, fmt_part.lower()


def _format_from_extension(filename: str) -> str:
    if "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    return ""
