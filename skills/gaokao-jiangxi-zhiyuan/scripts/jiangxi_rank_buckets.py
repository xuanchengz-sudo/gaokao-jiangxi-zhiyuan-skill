#!/usr/bin/env python3
"""江西高考志愿候选分档脚本。

输入结构化投档表，按考生位次输出冲/稳/保候选。脚本只做确定性分档，
不输出录取概率。
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


DEFAULT_THRESHOLDS = {
    # ratio = (投档单位最新最低位次 - 考生位次) / 考生位次
    # 负数表示往年最低位次高于考生位次，作为冲档信息参考。
    "冲_min": -0.20,
    "冲_max": -0.03,
    "稳_min": -0.03,
    "稳_max": 0.10,
    "保_min": 0.10,
    "保_max": 0.40,
}


def read_csv(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def to_int(value):
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).replace(",", "")))
    except ValueError:
        return None


def pick(row: dict, *names: str) -> str:
    for name in names:
        if row.get(name) not in (None, ""):
            return row.get(name)
    return ""


def classify(rank: int, base_rank: int, th: dict) -> str | None:
    ratio = (base_rank - rank) / rank
    if th["冲_min"] <= ratio < th["冲_max"]:
        return "冲"
    if th["稳_min"] <= ratio < th["稳_max"]:
        return "稳"
    if th["保_min"] <= ratio <= th["保_max"]:
        return "保"
    return None


def aggregate(rows: list[dict], category: str | None, batch: str | None, latest_year: int | None):
    filtered = []
    for row in rows:
        if category and pick(row, "科类") != category:
            continue
        if batch and pick(row, "批次") != batch:
            continue
        year = to_int(pick(row, "year", "年份"))
        min_rank = to_int(pick(row, "最低位次", "位次", "最低排名"))
        if year is None or min_rank is None:
            continue
        if latest_year and year > latest_year:
            continue
        row = dict(row)
        row["_year"] = year
        row["_min_rank"] = min_rank
        row["_min_score"] = to_int(pick(row, "最低分", "分数"))
        row["_uid"] = pick(row, "投档单位id", "投档单位ID")
        if not row["_uid"]:
            code = pick(row, "院校代码", "学校代码")
            group = pick(row, "专业组代码", "专业组")
            row["_uid"] = f"{code}-{group}" if code or group else pick(row, "院校名", "学校名称")
        filtered.append(row)

    by_uid = defaultdict(list)
    for row in filtered:
        by_uid[row["_uid"]].append(row)

    out = []
    for uid, items in by_uid.items():
        items.sort(key=lambda r: r["_year"], reverse=True)
        latest = items[0]
        ranks = [r["_min_rank"] for r in items[:3] if r["_min_rank"] is not None]
        out.append({
            "投档单位id": uid,
            "院校名": pick(latest, "院校名", "学校名称"),
            "专业组代码": pick(latest, "专业组代码", "专业组"),
            "科类": pick(latest, "科类"),
            "批次": pick(latest, "批次"),
            "基准年": latest["_year"],
            "基准最低分": latest["_min_score"],
            "基准最低位次": latest["_min_rank"],
            "近三年位次区间": [min(ranks), max(ranks)] if ranks else None,
            "样本年数": len(ranks),
            "source_url": pick(latest, "source_url", "来源URL"),
            "_latest": latest,
        })
    return out


def add_plan_hint(candidates: list[dict], plan_rows: list[dict] | None):
    if not plan_rows:
        return candidates
    by_uid = defaultdict(list)
    for row in plan_rows:
        uid = pick(row, "投档单位id", "投档单位ID")
        if not uid:
            code = pick(row, "院校代码", "学校代码")
            group = pick(row, "专业组代码", "专业组")
            uid = f"{code}-{group}" if code or group else pick(row, "院校名", "学校名称")
        year = to_int(pick(row, "year", "年份"))
        plan = to_int(pick(row, "计划数", "招生计划"))
        if uid and year and plan is not None:
            by_uid[uid].append((year, plan))

    for cand in candidates:
        plans = sorted(by_uid.get(cand["投档单位id"], []), reverse=True)
        cand["计划变化提示"] = ""
        if len(plans) >= 2 and plans[1][1] > 0:
            cur_year, cur = plans[0]
            prev_year, prev = plans[1]
            change = (cur - prev) / prev
            if abs(change) >= 0.2:
                direction = "扩招" if change > 0 else "缩招"
                effect = "位次可能下探" if change > 0 else "位次可能抬高"
                cand["计划变化提示"] = f"{cur_year}较{prev_year}{direction}{round(abs(change) * 100)}%（{prev}->{cur}），{effect}，仅作方向提示"
    return candidates


def build(rank: int, min_rank_rows: list[dict], plan_rows: list[dict] | None, args):
    th = dict(DEFAULT_THRESHOLDS)
    for key in th:
        value = getattr(args, key, None)
        if value is not None:
            th[key] = value

    units = aggregate(min_rank_rows, args.category, args.batch, args.latest_year)
    buckets = {"冲": [], "稳": [], "保": []}
    for unit in units:
        gear = classify(rank, unit["基准最低位次"], th)
        if not gear:
            continue
        unit["策略"] = gear
        unit["与考生位次差"] = unit["基准最低位次"] - rank
        buckets[gear].append(unit)

    for gear in buckets:
        buckets[gear].sort(key=lambda r: abs(r["与考生位次差"]))
        if args.per_gear:
            buckets[gear] = buckets[gear][: args.per_gear]
        add_plan_hint(buckets[gear], plan_rows)
    return {
        "考生位次": rank,
        "说明": "仅为基于历史投档位次的信息分档，不代表录取概率。",
        "阈值": th,
        "冲": buckets["冲"],
        "稳": buckets["稳"],
        "保": buckets["保"],
    }


def main():
    parser = argparse.ArgumentParser(description="江西高考志愿冲稳保候选分档，不输出概率。")
    parser.add_argument("--rank", type=int, required=True, help="考生真实位次")
    parser.add_argument("--min-ranks", required=True, help="投档单位最低位次.csv")
    parser.add_argument("--plans", default="", help="招生计划.csv，可选")
    parser.add_argument("--category", default="", help="科类，如 物理类/历史类")
    parser.add_argument("--batch", default="", help="批次，如 本科批/高职专科批")
    parser.add_argument("--latest-year", type=int, default=None, help="只使用不晚于该年的数据")
    parser.add_argument("--per-gear", type=int, default=0, help="每档最多输出多少条，0=不限")
    parser.add_argument("--out", default="", help="输出 JSON 路径；缺省打印到 stdout")
    for key, value in DEFAULT_THRESHOLDS.items():
        parser.add_argument(f"--{key}", type=float, default=None)
    args = parser.parse_args()

    plan_rows = read_csv(args.plans) if args.plans else None
    result = build(args.rank, read_csv(args.min_ranks), plan_rows, args)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()

