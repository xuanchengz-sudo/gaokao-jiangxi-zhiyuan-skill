#!/usr/bin/env python3
"""检查高考志愿回答中的高风险表达。"""

from __future__ import annotations

import argparse
import re
import sys


BLOCK_PATTERNS = [
    r"录取概率\s*\d+",
    r"\d+\s*%\s*(录取|上岸|能上)",
    r"保(你|证)?录取",
    r"稳录",
    r"必上",
    r"一定能上",
    r"必须报",
    r"强烈建议",
    r"别犹豫",
    r"闭眼报",
    r"冲就完了",
]


def check(text: str) -> list[str]:
    hits = []
    for pat in BLOCK_PATTERNS:
        if re.search(pat, text):
            hits.append(pat)
    return hits


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", help="待检查文本文件；缺省从 stdin 读取")
    args = parser.parse_args()
    if args.path:
        text = open(args.path, encoding="utf-8").read()
    else:
        text = sys.stdin.read()
    hits = check(text)
    if hits:
        print("发现高风险表达：")
        for hit in hits:
            print(f"- {hit}")
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()

