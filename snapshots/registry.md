# 快照注册表（2026-11-24）

> 生成：scripts/register_snapshots.py（幂等，派生物）。time_risk=true 的项禁止用于严格 as_of 回放，S2 前必须核定。

## MarketSnapshot
### MS-PORTRAIT-001 · 市场画像日线面板
- 引用：`section_heat/data/portrait_daily.parquet` ｜ 质量：partial（逐列语义已核定；指数缓存最新 2026-11-17，滞后日 pos/vol 产出 NaN，报告须检查）
- 覆盖：全市场/中证全指，2010 起（TODO 记载 4025 天×21 列）
- 口径：原始值+1250日滚动分位（_pct 列）；估值历史段经 MySQL（2010~2026-07）+ tushare 补近期=混合来源
- 时间语义：{"event_time": "trade_date", "publish_time": "unknown", "available_time": "逐列已核定：见 snapshots/b1/portrait_time_semantics.md（lev/etf 为 T+1；pos/vol 受指数缓存滞后影响）", "ingest_time": "unknown"}
- 文件：582851 bytes，sha256 `f3fa1238127bf3c5…`，mtime 2026-11-24T17:38:27
- 备注：占位列 north_flow/rate10y 未启用，契约禁止引用

### MS-COINCIDENT-001 · 同步层合并视图
- 引用：`wind_vane/data/coincident_daily.csv` ｜ 质量：ok（缺口机制已文档化）
- 覆盖：全市场；moneyflow/margin 自 2023-10-25，etf_flow 自 2012-05-04
- 口径：主力净额亿元；rzye 亿元（含 est 回填标记）；ETF 净申购亿元（PIT 12 只篮子）
- 时间语义：{"event_time": "trade_date", "publish_time": "unknown", "available_time": "当日收盘后（margin 不足三所当日不落盘；fund_share T+1，n_etfs 见覆盖数）", "ingest_time": "文件 mtime 见 sha 记录"}
- 文件：48173 bytes，sha256 `00a14b5d6c1776ca…`，mtime 2026-11-07T14:57:02
- 备注：原始三表：coincident_moneyflow/margin/etf_flow.csv 同目录

### MS-CACHE-001 · section_heat pkl 进程缓存
- 引用：`section_heat/cache/（约 1 万个 pkl）` ｜ 质量：suspect（非权威）
- 覆盖：不一致（逐文件）
- 口径：进程缓存，无契约字段
- 时间语义：{"event_time": "文件内 trade_date", "publish_time": "unknown", "available_time": "unknown（time_risk=true）", "ingest_time": "文件 mtime"}
- 备注：⚠️ 非权威加速层（2026-11-24 结案）：永久不作为 as_of 回放依据；权威输入以 portrait_time_semantics.md + 本注册表为准

### MS-RICHTREND-001 · rich_trend MySQL 数据底座
- 引用：`MySQL market_history_data.rt_*（11 表）` ｜ 质量：ok（口径须标注）
- 覆盖：881 系列 90 个同花顺行业；行业资金流原生起点 2024-09-10；广度/结构类自 2024-12-24
- 口径：fact 表万元、mart 表亿元；基准 000300.SH；原生口径与探索口径（当前成分回填）并存
- 时间语义：{"event_time": "trade_date", "publish_time": "unknown", "available_time": "当日 ETL 完成后（etl_daily.py）", "ingest_time": "表内时间戳（待核）"}
- 备注：成分每日快照（ths_member 无历史）；探索口径引用须显式标注（CON-000005）

### MS-DASHBOARD-001 · dashboard 派生统计 JSON
- 引用：`dashboard/data/*.json（4 文件）` ｜ 质量：ok（派生物）
- 覆盖：派生物
- 口径：派生统计（胜率表/lookup/top10/信号）
- 时间语义：{"event_time": "生成日", "publish_time": "生成日", "available_time": "生成后", "ingest_time": "文件 mtime"}
- 备注：必须可从主记录重建；引用须记录生成版本

## FeatureSnapshot
### FS-PORTRAIT-V1 · 市场画像六维
- 指标卡：FEA-000001 ｜ 输入：MS-PORTRAIT-001 ｜ 异常状态：ok（占位列未启用）
- 公式版本：external: scripts/build_portrait.py（母项目，未纳入版本管理——版本记录为其文件 mtime）
- 备注：六维分位（pos/val/lev/act/vol/etf_flow）；公式与参数以源脚本为准，本项目不复制

### FS-SIGNAL-V1 · 信号族（温度/温度动量/离散度/相关性）
- 指标卡：FEA-000002 ｜ 输入：MS-CACHE-001（加速层）/ 源项目 scores_*.parquet ｜ 异常状态：ok
- 公式版本：external: section_heat/section_heat_tushare.py + scripts/intraday_temp_live.py（盘中 14:50 估计，akshare 通道，intraday_estimate 口径）
- 备注：三口径 sw/ths/snap；250 日滚动分位

### FS-COINCIDENT-V1 · 同步层三指标（主力流出压力/杠杆水位/ETF 净流入）
- 指标卡：FEA-000003/FEA-000004/FEA-000005 ｜ 输入：MS-COINCIDENT-001 ｜ 异常状态：ok
- 公式版本：external: wind_vane/collect_coincident.py + merge_coincident.py
- 备注：250 日滚动分位；阈值黄 90/红 99 为占位未校准

### FS-RICHTREND-V1 · rich_trend 指标底座与状态标注
- 指标卡：FEA-000006/FEA-000007 ｜ 输入：MS-RICHTREND-001 ｜ 异常状态：ok
- 公式版本：external: rich_trend/scripts/build_metrics.py + build_annotations.py（规则 v1.0）
- 备注：RobustZ 120 日中位/MAD ≥60 观测截尾±5；状态机阶梯+风险标签
