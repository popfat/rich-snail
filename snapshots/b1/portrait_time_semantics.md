# 画像面板逐列时间语义核定（WP-B01-04）

> 日期：2026-11-24 ｜ 对象：`section_heat/data/portrait_daily.parquet`（4101 行 × 23 列，2010 起）
> 方法：通读 `scripts/build_portrait.py` 实现，核对各列数据源与发布特性；结论供 as_of 回放与报告引用使用。

## 逐列可见时间表

| 列 | 数据源 | event→available 语义 | 滞后/缺口特性 |
|---|---|---|---|
| pos_dd_52w / pos_ma250_dev | `index_daily`（中证全指 000985.CSI，本地缓存） | T 日收盘后，日更管线完成后可见 | **当前指数缓存最新 2026-11-17**；缓存滞后日该列产出 NaN（实测 2026-11-23/24 为 NaN） |
| vol20 | 同上（index_daily） | 同上 | 同上（同为 NaN） |
| val_pe_med / val_pb_med | MySQL `factor_rotation.daily_basic`（2010~2026-07）+ tushare 周抽样缓存补近期 | daily_basic 一般 T 日晚间可得；**近期段为周抽样，可能稀疏** | 混合来源交界（2026-07）需在引用长历史时注意 |
| act_amount | `daily` 全市场面板（vol×close 估算） | T 日收盘后 | — |
| act_turnover | `daily_basic` 换手率中位数 | T 日晚间 | — |
| lev_rzye | `margin` 沪深北三所汇总 | **T+1 稳妥**；当日三所常不齐 | 不足三所当日不落盘（≤3 自然日自愈）；>3 天用前值回填标 est=1（实例：2026-09-30 SZSE/BSE 永久缺口） |
| lev_ratio | lev_rzye ÷ circ_mv（daily_basic） | 同 lev_rzye（受 margin 约束） | circ_mv 缺失日 ffill |
| etf_flow | wind_vane `coincident_etf_flow.csv`（fund_share×fund_nav，PIT 12 只） | **T+1**（份额 T+1 发布） | 最新日常仅 2-3 只更新，`etf_n_etfs` 见覆盖数，次日自愈（实测 2026-11-23/24 etf_n_etfs 为 NaN） |
| north_flow / rate10y | — | **未启用（全列 NaN）** | 契约红线第 4 条：禁止引用 |

## 分位列（`*_pct`）

- 公式：滚动 1250 日分位，min_periods=250（`build_portrait.py pct()`）；
- 复现性：已验证同快照同公式精确复现全部 10 列（`snapshots/b1/reproduce_check_20261124.md`，G1 条件 1 证据）；
- 可见性：分位列的可见时间不早于其原始列；滚动窗口只用历史数据，无前视。

## 使用约束（写入注册表）

1. 报告引用 pos/vol 时须检查当日是否 NaN；NaN 即触发 MVP 弃权条件第 1 条（关键数据缺失→证据不足或降级）；
2. lev_*、etf_flow 在 T 日 14:50（paperwalk 时点）**不可见**，paperwalk 报告只能使用 T-1 值并标注；
3. 估值近期段为周抽样，日报中标注口径；
4. 严格 as_of 回放时，按上表逐列取 `available_time ≤ as_of` 的值。

## pkl 进程缓存处置（MS-CACHE-001 结案）

`section_heat/cache/` 约 1 万个 pkl 为**非权威加速层**永久定位：不作为 as_of 回放依据；权威输入以本核定表 + 注册表（`snapshots/registry.md`）为准；后续契约化快照如需重建，以接口重采为准而非 pkl。
