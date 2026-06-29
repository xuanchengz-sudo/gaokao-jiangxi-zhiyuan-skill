#!/usr/bin/env python3
"""Audit source URLs for Jiangxi gaokao data collection.

Input can be CSV or JSON. The script looks for a URL in `url`, `source_url`,
`official_url`, or `retrieved_url`, classifies the domain, and optionally probes
HTTP accessibility with the standard library.
"""

from __future__ import annotations

import argparse
import csv
import json
import ssl
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


A0_DOMAINS = {
    "jxeea.cn": "江西省教育考试院",
    "www.jxeea.cn": "江西省教育考试院",
    "jxgk.jxeea.cn": "江西省普通高考综合管理平台",
    "jyt.jiangxi.gov.cn": "江西省教育厅",
    "gaokao.chsi.com.cn": "教育部阳光高考",
    "www.moe.gov.cn": "教育部",
}


def load_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [dict(x) for x in data]
        if isinstance(data, dict):
            for key in ("rows", "sources", "items"):
                if isinstance(data.get(key), list):
                    return [dict(x) for x in data[key]]
        raise ValueError("JSON input must be a list or contain rows/sources/items")
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def extract_url(row: dict[str, Any]) -> str:
    for key in ("url", "source_url", "official_url", "retrieved_url", "链接"):
        value = str(row.get(key, "") or "").strip()
        if value.startswith(("http://", "https://")):
            return value
    return ""


def classify(url: str, extra_official_domains: set[str]) -> tuple[str, str]:
    host = urlparse(url).netloc.lower().split(":")[0]
    if host in A0_DOMAINS:
        return "A0", A0_DOMAINS[host]
    if host in extra_official_domains:
        return "A1", "用户指定官方/院校域名"
    if host.endswith(".edu.cn"):
        return "A1", "疑似院校官方域名，需从院校官网或阳光高考反查"
    if host.endswith(".gov.cn"):
        return "A0", "政府官网域名，需核对页面归属和内容"
    if host:
        return "B", "非官方或聚合来源，需回溯官方原始来源"
    return "C", "无有效 URL"


def probe(url: str, timeout: int) -> dict[str, Any]:
    if not url:
        return {"http_status": "", "final_url": "", "content_type": "", "probe_error": "missing_url"}
    context = ssl.create_default_context()
    headers = {"User-Agent": "Mozilla/5.0 source-audit"}
    for method in ("HEAD", "GET"):
        request = Request(url, headers=headers, method=method)
        try:
            with urlopen(request, timeout=timeout, context=context) as response:
                return {
                    "http_status": response.getcode(),
                    "final_url": response.geturl(),
                    "content_type": response.headers.get("content-type", ""),
                    "probe_error": "",
                }
        except HTTPError as exc:
            if method == "HEAD" and exc.code in {403, 405}:
                continue
            return {
                "http_status": exc.code,
                "final_url": url,
                "content_type": exc.headers.get("content-type", "") if exc.headers else "",
                "probe_error": str(exc),
            }
        except URLError as exc:
            if method == "HEAD":
                continue
            return {"http_status": "", "final_url": url, "content_type": "", "probe_error": str(exc.reason)}
        except Exception as exc:  # pragma: no cover - environment dependent
            if method == "HEAD":
                continue
            return {"http_status": "", "final_url": url, "content_type": "", "probe_error": str(exc)}
    return {"http_status": "", "final_url": url, "content_type": "", "probe_error": "probe_failed"}


def audit(rows: list[dict[str, Any]], probe_urls: bool, timeout: int, extra_official_domains: set[str]) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    output: list[dict[str, Any]] = []
    for row in rows:
        url = extract_url(row)
        level, label = classify(url, extra_official_domains)
        result = {
            **row,
            "audited_url": url,
            "source_level": row.get("source_level") or level,
            "source_label": label,
            "verification_status": row.get("verification_status") or ("已官方域名初核" if level in {"A0", "A1"} else "待回溯官方来源"),
            "last_verified_at": now,
        }
        if probe_urls:
            result.update(probe(url, timeout))
        output.append(result)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit gaokao source URLs")
    parser.add_argument("input", help="CSV or JSON file containing URLs")
    parser.add_argument("--out", help="Output JSON path; defaults to stdout")
    parser.add_argument("--probe", action="store_true", help="Probe HTTP status and final URL")
    parser.add_argument("--timeout", type=int, default=12, help="HTTP timeout seconds")
    parser.add_argument("--official-domain", action="append", default=[], help="Additional official domain, e.g. zs.example.edu.cn")
    args = parser.parse_args()

    rows = load_rows(Path(args.input))
    extra = {d.lower().strip() for d in args.official_domain if d.strip()}
    result = audit(rows, args.probe, args.timeout, extra)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
