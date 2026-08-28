from __future__ import annotations

import argparse
import csv
import html
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


DEFAULT_INPUT = Path("explorations/data/raw/data_v0.csv")
DEFAULT_OUTPUT = Path("explorations/data/interim/data_v0_with_abstracts.csv")
USER_AGENT = "noticias-fill-abstracts/0.1"
ARXIV_API = "https://export.arxiv.org/api/query?id_list={paper_id}"


class MetaDescriptionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "meta":
            return

        attr_map = {key.lower(): (value or "") for key, value in attrs}
        content = attr_map.get("content", "").strip()
        if not content:
            return

        for key in ("name", "property"):
            meta_name = attr_map.get(key, "").strip().lower()
            if meta_name:
                self.meta[meta_name] = content


def _http_get(url: str, *, timeout: float) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def _extract_arxiv_id(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    if "arxiv.org" not in parsed.netloc.lower():
        return None

    path = parsed.path.strip("/")
    if not path:
        return None

    if path.startswith("abs/"):
        return path.removeprefix("abs/").strip()
    if path.startswith("pdf/"):
        return path.removeprefix("pdf/").removesuffix(".pdf").strip()
    return None


def _fetch_arxiv_abstract(paper_id: str, *, timeout: float) -> str | None:
    feed = _http_get(ARXIV_API.format(paper_id=urllib.parse.quote(paper_id)), timeout=timeout)
    root = ET.fromstring(feed)
    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    summary = root.findtext(".//atom:entry/atom:summary", default="", namespaces=namespace)
    return _clean_abstract(summary)


def _extract_meta_abstract(html_text: str) -> str | None:
    parser = MetaDescriptionParser()
    parser.feed(html_text)

    candidates = [
        parser.meta.get("citation_abstract"),
        parser.meta.get("description"),
        parser.meta.get("og:description"),
        parser.meta.get("twitter:description"),
    ]
    for candidate in candidates:
        cleaned = _clean_abstract(candidate or "")
        if cleaned:
            return cleaned
    return None


def _clean_abstract(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^(abstract|summary)\s*[:\-]\s*", "", text, flags=re.IGNORECASE)
    return text.strip()


def _fetch_abstract(source_url: str, *, timeout: float) -> str | None:
    arxiv_id = _extract_arxiv_id(source_url)
    if arxiv_id:
        return _fetch_arxiv_abstract(arxiv_id, timeout=timeout)

    page = _http_get(source_url, timeout=timeout)
    return _extract_meta_abstract(page)


def fill_abstracts(
    input_path: Path,
    output_path: Path,
    *,
    timeout: float,
    delay_seconds: float,
) -> tuple[int, int, int]:
    with input_path.open("r", encoding="utf-8-sig", newline="") as infile:
        reader = csv.DictReader(infile)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames:
            raise ValueError(f"{input_path} does not contain a CSV header")
        if "abstract" not in fieldnames:
            raise ValueError(f"{input_path} is missing the 'abstract' column")
        if "source_url" not in fieldnames:
            raise ValueError(f"{input_path} is missing the 'source_url' column")

        rows = list(reader)

    updated = 0
    skipped = 0
    failed = 0

    for row in rows:
        current = (row.get("abstract") or "").strip()
        if current:
            skipped += 1
            continue

        source_url = (row.get("source_url") or "").strip()
        if not source_url:
            failed += 1
            continue

        try:
            abstract = _fetch_abstract(source_url, timeout=timeout)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ET.ParseError) as exc:
            failed += 1
            print(
                f"[warn] {row.get('paper_id', '<unknown>')}: could not fetch abstract from {source_url} ({exc})",
                file=sys.stderr,
            )
            continue

        if not abstract:
            failed += 1
            print(
                f"[warn] {row.get('paper_id', '<unknown>')}: no abstract metadata found at {source_url}",
                file=sys.stderr,
            )
            continue

        row["abstract"] = abstract
        updated += 1

        if delay_seconds > 0:
            time.sleep(delay_seconds)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return updated, skipped, failed


def main() -> int:
    parser = argparse.ArgumentParser(description="Fill empty abstract cells in a CSV of papers.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--delay", type=float, default=0.5)
    args = parser.parse_args()

    updated, skipped, failed = fill_abstracts(
        args.input,
        args.output,
        timeout=args.timeout,
        delay_seconds=args.delay,
    )
    print(
        f"Wrote {args.output} | updated={updated} skipped={skipped} failed={failed}",
        file=sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
