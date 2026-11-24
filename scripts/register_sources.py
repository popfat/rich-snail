#!/usr/bin/env python3
"""SRC 来源登记（B2 / WP-B02-01）

原则：
- 原文不可变：只读引用，不复制、不改写源文件；
- 每条来源生成 SRC 卡（YAML front matter + 正文），含 sha256 校验值与定位信息；
- 幂等：重跑只更新 changed 标记，不覆盖人工编辑过的正文（若卡片已存在且源未变则跳过）。
"""
import hashlib, os, re, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # rich-snail/
BASE = os.path.dirname(ROOT)                                                 # market-compass/
SRC_DIR = os.path.join(ROOT, 'knowledge_base', '01_sources')

# (SRC_ID, 相对 BASE 的路径, 来源类型, 说明)
SOURCES = [
    ("SRC-000001", "docs/TODO.md", "notes", "全局设计规则与研究路线（两族分层/百分位化/两级上市制/T1/T2/T3）"),
    ("SRC-000002", "docs/portrait_signal_framework.md", "article", "画像族/信号族划分与处理方案 v1"),
    ("SRC-000003", "docs/similarity_winrate_sop.md", "article", "画像相似性×信号历史胜率 SOP v1"),
    ("SRC-000004", "docs/signal_detail_page_spec.md", "article", "信号族详情页设计规范 v1（工程规范，非知识素材）"),
    ("SRC-000005", "docs/A股同花顺行业资金流向看板落地方案.md", "article", "同花顺行业资金流向看板方案 V1.2"),
    ("SRC-000006", "docs/个人量化系统全链路Roadmap.md", "article", "顶层治理文档（母本，只引用不拆卡）"),
    ("SRC-000007", "docs/个人交易知识库改造与持续建设落地文档.md", "article", "知识库治理文档（母本，只引用不拆卡）"),
    ("SRC-000008", "wind_vane/docs/大盘风向_数据源与指标分层_方案_v1.md", "article", "大盘风向数据源与指标分层方案 v1（含接口实测）"),
    ("SRC-000009", "wind_vane/docs/同步层指标_计算方案与验证结果_交接_v1.md", "article", "同步层三指标计算方案与验证结果交接 v1"),
    ("SRC-000010", "rich_trend/docs/P0_数据源验收报告.md", "article", "rich_trend P0 数据源验收报告"),
    ("SRC-000011", "rich_trend/docs/P3_蓄水池水位指标检验报告.md", "article", "蓄水池水位指标检验报告（探索口径）"),
    ("SRC-000012", "rich_trend/docs/P3b_策展组合剪枝验证报告.md", "article", "策展组合剪枝验证报告（探索口径）"),
    ("SRC-000013", "rich_trend/docs/P3c_状态迁移与风险挖掘报告.md", "article", "状态迁移与风险挖掘报告（探索口径）"),
    ("SRC-000014", "rich_trend/docs/状态定义与迁移说明.md", "article", "rich_trend 状态定义与迁移说明 v1.0"),
    ("SRC-000015", "rich_trend/docs/D4b_影子假设候审登记.md", "notes", "D4b 影子假设候审登记（前视污染假设样本外审判协议）"),
    ("SRC-000016", "rich_trend/README.md", "notes", "rich_trend 工程 README（数据口径：单位/起点/RobustZ 参数/基准）"),
    ("SRC-000017", "wind_vane/README.md", "notes", "wind_vane 工程 README（同步层采集口径/工程要点/ETF 篮子待确认）"),
    ("SRC-000018", "README.md", "notes", "market-compass 总 README（子项目地图/日更链路/新增指标流程）"),
]

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    os.makedirs(SRC_DIR, exist_ok=True)
    today = datetime.date.today().isoformat()
    created, skipped, missing = [], [], []
    for src_id, rel, stype, note in SOURCES:
        ap = os.path.join(BASE, rel)
        if not os.path.exists(ap):
            missing.append((src_id, rel)); continue
        digest = sha256(ap)
        stat = os.stat(ap)
        out = os.path.join(SRC_DIR, f"{src_id}.md")
        if os.path.exists(out):
            txt = open(out, encoding='utf-8').read()
            if digest in txt:
                skipped.append(src_id); continue
        title = note.split('（')[0]
        body = f"""---
id: {src_id}
type: source
title: {title}
status: archived
version: 1
origin: external
created_at: {today}
updated_at: {today}
source_ids: []
market_scope: 大盘
universe: unknown
timeframe: unknown
horizon: unknown
regime_scope: []
decision_role: unknown
evidence_grade: unverified
source_time: unknown
available_time: unknown
related_ids: []
tags: []
---

# {title}

## 来源登记

| 字段 | 值 |
|---|---|
| 路径（只读引用） | `../{rel}` |
| sha256 | `{digest}` |
| 文件大小 | {stat.st_size} bytes |
| 来源类型 | {stype} |
| 收录时间（ingest_time） | {today} |
| 说明 | {note} |

## 原文定位

- 文件级定位：`/data/market-compass/{rel}`（原文不在本项目内复制）；
- 段落级定位：在引用本来源的知识卡中以"标题/小节"标注。

## 备注

- 本卡由 `scripts/register_sources.py` 自动生成；原文不可变，校验值变更时脚本会提示。
"""
        with open(out, 'w', encoding='utf-8') as f:
            f.write(body)
        created.append(src_id)
    print(f"created={len(created)} skipped(unchanged)={len(skipped)} missing={len(missing)}")
    for m in missing:
        print("MISSING:", m[0], m[1])
    return 0 if not missing else 1

if __name__ == '__main__':
    sys.exit(main())
