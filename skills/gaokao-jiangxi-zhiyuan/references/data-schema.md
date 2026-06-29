# 江西数据 schema

建议在 skill 目录下建立 `data/provinces/江西/`，把官方或已核验数据统一成 CSV/JSON。脚本只读结构化数据，不从自然语言里猜数字。

## 目录结构

```text
data/
  provinces/
    江西/
      时间线.json
      一分一段表.csv
      投档单位最低位次.csv
      招生计划.csv
      选科要求_专业组.csv
      选科要求_专业类.csv
      专业目录.csv
      数据来源审计.csv
  院校信息.csv
  employment/
    红黄绿牌专业.csv
```

## 时间线.json

```json
{
  "省份": "江西",
  "年份": 2026,
  "科类体系": "3+1+2",
  "志愿模式": "院校专业组",
  "投档单位粒度": "院校专业组",
  "可填志愿数": {
    "本科批": null,
    "高职专科批": null
  },
  "时间线": [
    {"阶段": "出分", "开始": "YYYY-MM-DD", "结束": "YYYY-MM-DD", "source_url": ""},
    {"阶段": "集中填报", "开始": "YYYY-MM-DD HH:mm", "结束": "YYYY-MM-DD HH:mm", "source_url": ""}
  ]
}
```

`null` 表示当年未核验，不要在回答中补数字。

## 一分一段表.csv

字段：

- `year`
- `科类`：`物理类`、`历史类`、艺术/体育口径另建字段或另表。
- `分数`
- `累计人数`
- `source_url`
- `source_level`
- `verification_status`
- `发布机构`
- `fetched_at`

分数换位次规则：取同年同科类该分数对应 `累计人数`。分数缺行时，取不高于该分数的最近一行，并标注保守估算。

## 投档单位最低位次.csv

字段：

- `投档单位id`：建议为 `院校代码-专业组代码`。
- `院校代码`
- `院校名`
- `专业组代码`
- `科类`
- `批次`
- `最低分`
- `最低位次`
- `year`
- `source_url`
- `公告页URL`
- `发布机构`
- `source_level`
- `official_url`
- `verification_status`
- `last_verified_at`
- `fetched_at`

江西新高考专业组可能逐年重组。分档基准优先使用最新可得年；跨年区间只作为波动参考，不要把不同年份组号机械视为同一专业集合。

## 招生计划.csv

字段：

- `投档单位id`
- `院校代码`
- `院校名`
- `专业组代码`
- `科类`
- `批次`
- `计划数`
- `year`
- `source_url`
- `source_level`
- `verification_status`

计划变化只作方向性提示。组号不稳定时，不要比较跨年组计划数。

## 选科要求_专业组.csv

若能拿到江西当年专业组级数据，优先使用此表硬过滤。

字段：

- `投档单位id`
- `院校代码`
- `院校名`
- `专业组代码`
- `首选`
- `再选必选`
- `再选可选`
- `要求原文`
- `source_url`
- `source_level`
- `verification_status`

## 选科要求_专业类.csv

若只能拿到院校×专业类数据，用于专业建议和警示，不做组级硬过滤。

字段：

- `院校代码`
- `院校名`
- `层次`
- `专业类`
- `首选`
- `再选必选`
- `再选可选`
- `含专业`
- `source_url`
- `source_level`
- `verification_status`

## 专业目录.csv

当年专业目录到位后，用于专业组内专业核验。

字段：

- `投档单位id`
- `院校代码`
- `院校名`
- `专业组代码`
- `专业代码`
- `专业名称`
- `学制`
- `学费`
- `校区`
- `外语语种`
- `单科要求`
- `体检要求`
- `备注`
- `source_url`
- `source_level`
- `verification_status`

## 院校信息.csv

字段：

- `院校代码`
- `院校名`
- `省份`
- `城市`
- `办学层次`
- `办学性质`
- `主管部门`
- `source_url`
- `source_level`
- `verification_status`

## 数据来源审计.csv

联网检索、网页爬取、第三方转载验证或使用本地缓存时写入此表。字段：

- `数据集名称`：如 `2024本科艺术类舞蹈类投档表`。
- `year`
- `批次`
- `科类`
- `source_level`：A0/A1/B/C，见 `source-verification.md`。
- `source_url`：实际取数 URL。
- `official_url`：可回溯官方 URL；没有则留空。
- `retrieved_url`：搜索命中的网页或下载 URL。
- `verification_status`：已官方核验、已交叉验证、待登录核验、不可验证。
- `verification_method`：站内检索、官方附件、院校章程、跨源比对、本地缓存等。
- `fetched_at`
- `last_verified_at`
- `cache_path`
- `sha256`
- `检索词`
- `备注`

## 输出必须保留的来源字段

候选表至少保留：

- `投档数据来源`
- `计划来源`
- `选科来源`
- `专业目录来源`
- `章程来源`
- `source_level`
- `verification_status`
- `official_url`
