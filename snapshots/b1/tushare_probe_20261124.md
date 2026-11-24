# tushare 接口能力实测复核（S1 / WP-B01-01）

探测时间：2026-11-24T22:15:52（token 仅进程内使用，未打印未落盘）

| 接口 | 结果 | 行数 | 延迟s | 说明 |
|---|---|---|---|---|
| `trade_cal` | ✅ | 24 | 0.07 | 交易日历 |
| `daily` | ✅ | 5572 | 1.29 | 全市场日线（温度/离散度/相关性输入；amount 单位千元） |
| `index_daily` | ✅ | 17 | 0.07 | 中证全指（画像位置/波动输入） |
| `index_daily` | ✅ | 17 | 0.24 | 上证指数 |
| `daily_basic` | ✅ | 5572 | 1.3 | 估值/换手（画像输入） |
| `margin` | ✅ | 3 | 0.07 | 融资融券汇总（三所；当日可能不齐） |
| `moneyflow` | ✅ | 5580 | 1.26 | 主力资金（wind_vane 同步层） |
| `fund_share` | ✅ | 16 | 0.07 | ETF 份额（T+1） |
| `fund_nav` | ✅ | 17 | 0.08 | ETF 净值 |
| `fund_daily` | ✅ | 17 | 0.07 | 沪深300ETF 行情（账本标的） |
| `moneyflow_ind_ths` | ✅ | 360 | 0.1 | 同花顺行业资金流（rich_trend） |
| `ths_member` | ✅ | 190 | 0.07 | 同花顺行业成分（只有当前快照） |
| `stk_mins` | ✅ | 0 | 0.09 | 分钟线（盘中回退通道） |
| `rt_min` | ❌ rt_min: 您的权限不足 | — | 13.06 | 实时分钟（历史文档记录无权限，复核） |

## 备注

- 历史文档记录（wind_vane/section_heat，as_of 2026-09~11）：moneyflow 约 130 次/分；rt_min/rt_k/realtime_quote 无权限。本表为当日实测复核。
- 原始 JSON：同目录 tushare_probe_*.json。
