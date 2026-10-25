#!/usr/bin/env python3
"""Score discovered job URLs and write a review queue. No application submission."""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import yaml


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def extract_urls(markdown: str) -> list[str]:
    urls = re.findall(r"https?://[^\s)\]>\"']+", markdown)
    seen = set()
    out = []
    for url in urls:
        url = url.rstrip(".,;")
        if url not in seen and urlparse(url).scheme == "https":
            seen.add(url)
            out.append(url)
    return out


def fetch_text(url: str, timeout: int = 15) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Only HTTPS job URLs are accepted")
    req = Request(url, headers={"User-Agent": "smart-job-search-apply/0.1"})
    with urlopen(req, timeout=timeout) as response:
        raw = response.read(1_500_000).decode("utf-8", errors="replace")
    parser = TextExtractor()
    parser.feed(raw)
    return re.sub(r"\s+", " ", html.unescape(" ".join(parser.parts))).strip()


def score(text: str, cfg: dict) -> tuple[int, list[str], str]:
    lower = text.lower()
    title_hits = [t for t in cfg.get("target_titles", []) if t.lower() in lower]
    skill_hits = [s for s in cfg.get("skills", []) if s.lower() in lower]
    exclusions = [x for x in cfg.get("exclude_terms", []) if x.lower() in lower]
    title_points = min(30, round(30 * len(title_hits) / max(1, min(3, len(cfg.get("target_titles", []))))))
    skill_points = min(70, round(70 * len(skill_hits) / max(1, min(10, len(cfg.get("skills", []))))))
    value = 0 if exclusions else min(100, title_points + skill_points)
    return value, skill_hits, ", ".join(title_hits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/pipeline.md")
    ap.add_argument("--config", default="config/pipeline.yml")
    ap.add_argument("--out", default="output")
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    source = Path(args.input)
    urls = extract_urls(source.read_text(encoding="utf-8")) if source.exists() else []
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for url in urls:
        row = {"url": url, "relevance_score": 0, "matched_skills": "", "matched_titles": "", "status": "rejected", "error": ""}
        try:
            text = fetch_text(url)
            if len(text) < int(cfg.get("min_description_chars", 300)):
                raise ValueError("Job description too short to score safely")
            value, skills, titles = score(text, cfg)
            row.update(relevance_score=value, matched_skills="; ".join(skills), matched_titles=titles,
                       status="qualified" if value >= int(cfg.get("min_relevance_score", 70)) else "below_threshold")
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"[:240]
        rows.append(row)
        time.sleep(0.5)
    fields = ["url", "relevance_score", "matched_skills", "matched_titles", "status", "error"]
    with (out_dir / "job_queue.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    qualified = [r for r in rows if r["status"] == "qualified"]
    (out_dir / "qualified_jobs.json").write_text(json.dumps(qualified, indent=2), encoding="utf-8")
    print(f"Scanned {len(urls)} URLs; {len(qualified)} reached relevance threshold.")
    print("Scores indicate role relevance only, not ATS probability.")


if __name__ == "__main__":
    main()
