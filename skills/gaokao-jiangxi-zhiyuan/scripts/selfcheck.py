#!/usr/bin/env python3
"""江西志愿 skill 脚本自检。"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def write_csv(path: Path, rows: list[dict]):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_rank_buckets():
    rows = [
        {"投档单位id": "A-101", "院校名": "甲大学", "专业组代码": "101", "科类": "历史类", "批次": "本科批", "最低分": "520", "最低位次": "8500", "year": "2025", "source_url": "https://example.com/a"},
        {"投档单位id": "B-102", "院校名": "乙学院", "专业组代码": "102", "科类": "历史类", "批次": "本科批", "最低分": "500", "最低位次": "10050", "year": "2025", "source_url": "https://example.com/b"},
        {"投档单位id": "C-103", "院校名": "丙学院", "专业组代码": "103", "科类": "历史类", "批次": "本科批", "最低分": "480", "最低位次": "11800", "year": "2025", "source_url": "https://example.com/c"},
        {"投档单位id": "D-104", "院校名": "丁学院", "专业组代码": "104", "科类": "物理类", "批次": "本科批", "最低分": "480", "最低位次": "11800", "year": "2025", "source_url": "https://example.com/d"},
    ]
    with tempfile.TemporaryDirectory() as td:
        data = Path(td) / "min.csv"
        out = Path(td) / "out.json"
        write_csv(data, rows)
        subprocess.run([
            sys.executable,
            str(ROOT / "jiangxi_rank_buckets.py"),
            "--rank", "10000",
            "--min-ranks", str(data),
            "--category", "历史类",
            "--batch", "本科批",
            "--out", str(out),
        ], check=True)
        result = json.loads(out.read_text(encoding="utf-8"))
    assert result["考生位次"] == 10000
    assert len(result["冲"]) == 1
    assert len(result["稳"]) == 1
    assert len(result["保"]) == 1
    assert result["冲"][0]["院校名"] == "甲大学"


def test_tone_check():
    ok = subprocess.run([sys.executable, str(ROOT / "tone_check.py")], input="可考虑，需核验。", text=True, capture_output=True)
    assert ok.returncode == 0
    bad = subprocess.run([sys.executable, str(ROOT / "tone_check.py")], input="这个稳录，强烈建议。", text=True, capture_output=True)
    assert bad.returncode != 0


def test_source_audit():
    rows = [
        {"数据集名称": "江西公告", "source_url": "https://www.jxeea.cn/example.html"},
        {"数据集名称": "第三方线索", "source_url": "https://example.com/mirror.html"},
    ]
    with tempfile.TemporaryDirectory() as td:
        data = Path(td) / "sources.csv"
        out = Path(td) / "audit.json"
        write_csv(data, rows)
        subprocess.run([
            sys.executable,
            str(ROOT / "source_audit.py"),
            str(data),
            "--out",
            str(out),
        ], check=True)
        result = json.loads(out.read_text(encoding="utf-8"))
    assert result[0]["source_level"] == "A0"
    assert result[1]["source_level"] == "B"
    assert "verification_status" in result[0]


def main():
    test_rank_buckets()
    test_tone_check()
    test_source_audit()
    print("selfcheck OK")


if __name__ == "__main__":
    main()
