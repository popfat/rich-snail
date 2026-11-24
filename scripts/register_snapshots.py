#!/usr/bin/env python3
"""B1 / WP-B01-02：MarketSnapshot / FeatureSnapshot 注册层（S1）

原则（所有者 D8 决策）：本项目不实现指标计算，只对**既有数据产物**做契约化登记：
数据时点、来源、覆盖、口径、六时间语义（能确定的填，不能确定的标 unknown/time_risk）、质量状态。
pkl 进程缓存降级为"非权威加速层"（资产清单 R2），不作 as_of 回放依据。
幂等：重跑覆盖本注册文件（注册信息是派生物，不含人工编辑内容）。
"""
import os, hashlib, datetime, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, 'snapshots')
TODAY = datetime.date.today().isoformat()

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def finfo(rel):
    ap = os.path.join(BASE, rel)
    if not os.path.exists(ap):
        return None
    st = os.stat(ap)
    return {"sha256": sha256(ap), "bytes": st.st_size,
            "mtime": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec='seconds')}

# (id, 类型, 名称, 路径/引用, 来源接口, 覆盖, 口径, 时间语义, 质量状态, 备注)
MS = [
    ("MS-PORTRAIT-001", "市场画像日线面板", "section_heat/data/portrait_daily.parquet",
     "index_daily / MySQL factor_rotation.daily_basic + tushare / margin / daily / wind_vane etf_flow",
     "全市场/中证全指，2010 起（TODO 记载 4025 天×21 列）",
     "原始值+1250日滚动分位（_pct 列）；估值历史段经 MySQL（2010~2026-07）+ tushare 补近期=混合来源",
     {"event_time": "trade_date", "publish_time": "unknown", "available_time": "逐列已核定：见 snapshots/b1/portrait_time_semantics.md（lev/etf 为 T+1；pos/vol 受指数缓存滞后影响）", "ingest_time": "unknown"},
     "partial（逐列语义已核定；指数缓存最新 2026-11-17，滞后日 pos/vol 产出 NaN，报告须检查）",
     "占位列 north_flow/rate10y 未启用，契约禁止引用"),
    ("MS-COINCIDENT-001", "同步层合并视图", "wind_vane/data/coincident_daily.csv",
     "moneyflow / margin / fund_share+fund_nav",
     "全市场；moneyflow/margin 自 2023-10-25，etf_flow 自 2012-05-04",
     "主力净额亿元；rzye 亿元（含 est 回填标记）；ETF 净申购亿元（PIT 12 只篮子）",
     {"event_time": "trade_date", "publish_time": "unknown", "available_time": "当日收盘后（margin 不足三所当日不落盘；fund_share T+1，n_etfs 见覆盖数）", "ingest_time": "文件 mtime 见 sha 记录"},
     "ok（缺口机制已文档化）",
     "原始三表：coincident_moneyflow/margin/etf_flow.csv 同目录"),
    ("MS-CACHE-001", "section_heat pkl 进程缓存", "section_heat/cache/（约 1 万个 pkl）",
     "daily/snap/margin/index 等接口缓存",
     "不一致（逐文件）",
     "进程缓存，无契约字段",
     {"event_time": "文件内 trade_date", "publish_time": "unknown", "available_time": "unknown（time_risk=true）", "ingest_time": "文件 mtime"},
     "suspect（非权威）",
     "⚠️ 非权威加速层（2026-11-24 结案）：永久不作为 as_of 回放依据；权威输入以 portrait_time_semantics.md + 本注册表为准"),
    ("MS-RICHTREND-001", "rich_trend MySQL 数据底座", "MySQL market_history_data.rt_*（11 表）",
     "moneyflow_ind_ths / ths_daily / ths_member / daily / daily_basic",
     "881 系列 90 个同花顺行业；行业资金流原生起点 2024-09-10；广度/结构类自 2024-12-24",
     "fact 表万元、mart 表亿元；基准 000300.SH；原生口径与探索口径（当前成分回填）并存",
     {"event_time": "trade_date", "publish_time": "unknown", "available_time": "当日 ETL 完成后（etl_daily.py）", "ingest_time": "表内时间戳（待核）"},
     "ok（口径须标注）",
     "成分每日快照（ths_member 无历史）；探索口径引用须显式标注（CON-000005）"),
    ("MS-DASHBOARD-001", "dashboard 派生统计 JSON", "dashboard/data/*.json（4 文件）",
     "similar_regime_signal / regime_transition / analog_mining / midband 脚本产物",
     "派生物", "派生统计（胜率表/lookup/top10/信号）",
     {"event_time": "生成日", "publish_time": "生成日", "available_time": "生成后", "ingest_time": "文件 mtime"},
     "ok（派生物）",
     "必须可从主记录重建；引用须记录生成版本"),
]

FS = [
    ("FS-PORTRAIT-V1", "市场画像六维", "FEA-000001",
     "external: scripts/build_portrait.py（母项目，未纳入版本管理——版本记录为其文件 mtime）",
     "MS-PORTRAIT-001", "ok（占位列未启用）",
     "六维分位（pos/val/lev/act/vol/etf_flow）；公式与参数以源脚本为准，本项目不复制"),
    ("FS-SIGNAL-V1", "信号族（温度/温度动量/离散度/相关性）", "FEA-000002",
     "external: section_heat/section_heat_tushare.py + scripts/intraday_temp_live.py（盘中 14:50 估计，akshare 通道，intraday_estimate 口径）",
     "MS-CACHE-001（加速层）/ 源项目 scores_*.parquet", "ok",
     "三口径 sw/ths/snap；250 日滚动分位"),
    ("FS-COINCIDENT-V1", "同步层三指标（主力流出压力/杠杆水位/ETF 净流入）", "FEA-000003/FEA-000004/FEA-000005",
     "external: wind_vane/collect_coincident.py + merge_coincident.py",
     "MS-COINCIDENT-001", "ok",
     "250 日滚动分位；阈值黄 90/红 99 为占位未校准"),
    ("FS-RICHTREND-V1", "rich_trend 指标底座与状态标注", "FEA-000006/FEA-000007",
     "external: rich_trend/scripts/build_metrics.py + build_annotations.py（规则 v1.0）",
     "MS-RICHTREND-001", "ok",
     "RobustZ 120 日中位/MAD ≥60 观测截尾±5；状态机阶梯+风险标签"),
]

def main():
    os.makedirs(OUT, exist_ok=True)
    reg = {"registered_at": datetime.datetime.now().isoformat(timespec='seconds'),
           "note": "注册信息为派生物；本项目不实现指标计算（D8）。画像面板逐列时间语义已核定（snapshots/b1/portrait_time_semantics.md）；pkl 缓存永久定位非权威加速层。",
           "market_snapshots": [], "feature_snapshots": []}
    for mid, name, rel, src, cov, cal, times, q, note in MS:
        fi = finfo(rel) if not rel.endswith('/') and '(' not in rel else None
        reg["market_snapshots"].append({
            "id": mid, "name": name, "ref": rel, "source": src, "universe": cov,
            "caliber": cal, "time_semantics": times, "quality_status": q,
            "file": fi, "note": note})
    for fid, name, card, formula, inputs, anom, note in FS:
        reg["feature_snapshots"].append({
            "id": fid, "name": name, "feature_card": card, "formula_version": formula,
            "input_snapshots": inputs, "anomaly_status": anom, "note": note})
    path = os.path.join(OUT, 'registry.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)
    lines = [f"# 快照注册表（{TODAY}）", "",
             "> 生成：scripts/register_snapshots.py（幂等，派生物）。time_risk=true 的项禁止用于严格 as_of 回放，S2 前必须核定。", ""]
    lines.append("## MarketSnapshot")
    for m in reg["market_snapshots"]:
        lines.append(f"### {m['id']} · {m['name']}")
        lines.append(f"- 引用：`{m['ref']}` ｜ 质量：{m['quality_status']}")
        lines.append(f"- 覆盖：{m['universe']}")
        lines.append(f"- 口径：{m['caliber']}")
        lines.append(f"- 时间语义：{json.dumps(m['time_semantics'], ensure_ascii=False)}")
        if m['file']:
            lines.append(f"- 文件：{m['file']['bytes']} bytes，sha256 `{m['file']['sha256'][:16]}…`，mtime {m['file']['mtime']}")
        lines.append(f"- 备注：{m['note']}")
        lines.append("")
    lines.append("## FeatureSnapshot")
    for fs_ in reg["feature_snapshots"]:
        lines.append(f"### {fs_['id']} · {fs_['name']}")
        lines.append(f"- 指标卡：{fs_['feature_card']} ｜ 输入：{fs_['input_snapshots']} ｜ 异常状态：{fs_['anomaly_status']}")
        lines.append(f"- 公式版本：{fs_['formula_version']}")
        lines.append(f"- 备注：{fs_['note']}")
        lines.append("")
    with open(os.path.join(OUT, 'registry.md'), 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print("written registry.json + registry.md")

if __name__ == '__main__':
    main()
