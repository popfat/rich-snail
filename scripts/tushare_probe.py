#!/usr/bin/env python3
"""B1 / WP-B01-01：tushare 接口能力实测复核（S1）

- 复用母项目 scripts/tushare_client.py（不重复实现客户端，token 仅进程内读取）；
- 对 MVP 所需接口逐一做小样本探测：可用性、字段、行数、延迟；
- 输出 JSON（机器可读）+ Markdown 报告（人读）到 snapshots/b1/；
- 只探测、不采集；失败如实记录，不填 0。
"""
import os, sys, json, time, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import tushare_client as ts  # noqa: E402

OUT_DIR = os.path.join(ROOT, 'snapshots', 'b1')
TODAY = datetime.date.today().strftime('%Y%m%d')

# (接口, 探测参数, fields, 备注)
PROBES = [
    ("trade_cal", {"exchange": "SSE", "start_date": "20261101", "end_date": TODAY}, "", "交易日历"),
    ("daily", {"trade_date": "20261120"}, "ts_code,close,pct_chg,vol,amount", "全市场日线（温度/离散度/相关性输入；amount 单位千元）"),
    ("index_daily", {"ts_code": "000985.CSI", "start_date": "20261101", "end_date": TODAY}, "trade_date,close", "中证全指（画像位置/波动输入）"),
    ("index_daily", {"ts_code": "000001.SH", "start_date": "20261101", "end_date": TODAY}, "trade_date,close", "上证指数"),
    ("daily_basic", {"trade_date": "20261120"}, "ts_code,pe_ttm,pb,turnover_rate,circ_mv", "估值/换手（画像输入）"),
    ("margin", {"trade_date": "20261120"}, "", "融资融券汇总（三所；当日可能不齐）"),
    ("moneyflow", {"trade_date": "20261120"}, "ts_code,buy_lg_amount,sell_lg_amount,buy_elg_amount,sell_elg_amount,net_mf_amount", "主力资金（wind_vane 同步层）"),
    ("fund_share", {"ts_code": "510300.SH", "start_date": "20261101", "end_date": TODAY}, "", "ETF 份额（T+1）"),
    ("fund_nav", {"ts_code": "510300.SH", "start_date": "20261101", "end_date": TODAY}, "", "ETF 净值"),
    ("fund_daily", {"ts_code": "510300.SH", "start_date": "20261101", "end_date": TODAY}, "trade_date,close", "沪深300ETF 行情（账本标的）"),
    ("moneyflow_ind_ths", {"start_date": "20261119", "end_date": TODAY}, "", "同花顺行业资金流（rich_trend）"),
    ("ths_member", {"ts_code": "881121.TI"}, "", "同花顺行业成分（只有当前快照）"),
    ("stk_mins", {"ts_code": "000001.SH", "freq": "1min", "start_date": "2026-11-20 09:30:00", "end_date": "2026-11-20 10:30:00"}, "", "分钟线（盘中回退通道）"),
    ("rt_min", {"ts_code": "000001.SH"}, "", "实时分钟（历史文档记录无权限，复核）"),
]

def probe(name, params, fields, note):
    t0 = time.time()
    try:
        data = ts.call(name, fields=fields, **params)
        rs = ts.rows(data)
        return {"api": name, "ok": True, "rows": len(rs),
                "fields": data.get("fields", []), "latency_s": round(time.time() - t0, 2),
                "note": note, "sample_dates": sorted({str(r.get('trade_date','')) for r in rs if r.get('trade_date')})[-3:]}
    except Exception as e:
        return {"api": name, "ok": False, "error": str(e)[:300], "note": note,
                "latency_s": round(time.time() - t0, 2)}

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    results = []
    for name, params, fields, note in PROBES:
        r = probe(name, params, fields, note)
        r["params"] = params
        results.append(r)
        status = "OK" if r["ok"] else "FAIL"
        print(f"[{status}] {name}: rows={r.get('rows','-')} {r.get('error','')[:120]}")
        time.sleep(0.4)  # 温和限速
    out_json = os.path.join(OUT_DIR, f"tushare_probe_{TODAY}.json")
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({"probed_at": datetime.datetime.now().isoformat(timespec='seconds'),
                   "results": results}, f, ensure_ascii=False, indent=2)
    lines = ["# tushare 接口能力实测复核（S1 / WP-B01-01）",
             f"\n探测时间：{datetime.datetime.now().isoformat(timespec='seconds')}（token 仅进程内使用，未打印未落盘）\n",
             "| 接口 | 结果 | 行数 | 延迟s | 说明 |", "|---|---|---|---|---|"]
    for r in results:
        if r["ok"]:
            lines.append(f"| `{r['api']}` | ✅ | {r['rows']} | {r['latency_s']} | {r['note']} |")
        else:
            lines.append(f"| `{r['api']}` | ❌ {r['error'][:80]} | — | {r['latency_s']} | {r['note']} |")
    lines += ["", "## 备注", "",
              "- 历史文档记录（wind_vane/section_heat，as_of 2026-09~11）：moneyflow 约 130 次/分；rt_min/rt_k/realtime_quote 无权限。本表为当日实测复核。",
              "- 原始 JSON：同目录 tushare_probe_*.json。"]
    out_md = os.path.join(OUT_DIR, f"tushare_probe_{TODAY}.md")
    with open(out_md, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")
    print("written:", out_md)
    fails = [r for r in results if not r["ok"]]
    print(f"total={len(results)} fail={len(fails)}")

if __name__ == '__main__':
    main()
