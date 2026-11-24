#!/usr/bin/env python3
"""B1/B6 / WP-B01-03：复现性检查（G1 条件 1）

验证「同一数据快照 + 同一公式/参数 → 同一指标结果」：
1. 对快照文件（portrait_daily.parquet）计算 sha256，两次读取逐值一致（输入固定）；
2. 按文档化公式（滚动 1250 日分位，min_periods=250）从原始列重算 *_pct，
   与快照中存储的 *_pct 列逐值比对（公式/参数记录可复现结果）；
3. 重算执行两遍，两遍结果必须完全一致（确定性）。

输出：snapshots/b1/reproduce_check_{date}.{json,md}
"""
import os, sys, json, hashlib, datetime
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.dirname(ROOT)
PANEL = os.path.join(BASE, 'section_heat', 'data', 'portrait_daily.parquet')
OUT_DIR = os.path.join(ROOT, 'snapshots', 'b1')
TODAY = datetime.date.today().strftime('%Y%m%d')

SLOW_WIN = 1250
COLS = ['pos_dd_52w', 'pos_ma250_dev', 'val_pe_med', 'val_pb_med',
        'lev_rzye', 'lev_ratio', 'act_amount', 'act_turnover', 'vol20', 'etf_flow']

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def pct(s, w=SLOW_WIN):
    return s.rolling(w, min_periods=250).apply(lambda x: (x < x.iloc[-1]).mean() * 100, raw=False)

def recompute(df):
    return {c: pct(df[c]) for c in COLS}

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    digest = sha256(PANEL)
    df1 = pd.read_parquet(PANEL)
    df2 = pd.read_parquet(PANEL)
    input_identical = df1.equals(df2)

    run1 = recompute(df1)
    run2 = recompute(df2)
    details, all_match, all_deterministic = {}, True, True
    for c in COLS:
        stored = df1[f'{c}_pct']
        r1, r2 = run1[c], run2[c]
        deterministic = bool(((r1 - r2).abs().fillna(0) < 1e-9).all())
        both = pd.concat([stored, r1], axis=1, keys=['stored', 'recomputed']).dropna()
        diff = (both['stored'] - both['recomputed']).abs()
        n = len(both); n_match = int((diff < 1e-6).sum())
        max_diff = float(diff.max()) if n else None
        worst = diff.sort_values(ascending=False).head(3)
        details[c] = {
            'compared': n, 'matched': n_match, 'match_rate': round(n_match / n, 4) if n else None,
            'max_abs_diff': max_diff, 'deterministic': deterministic,
            'worst_dates': [str(d.date()) for d in worst.index],
            'note': '全一致' if n_match == n else '近端日期差异通常源于源数据近端更新/缓存时滞，需标注',
        }
        all_match &= (n_match == n)
        all_deterministic &= deterministic

    result = {
        'checked_at': datetime.datetime.now().isoformat(timespec='seconds'),
        'snapshot': os.path.relpath(PANEL, BASE), 'snapshot_sha256': digest,
        'rows': len(df1), 'date_range': [str(df1.index.min().date()), str(df1.index.max().date())],
        'input_read_twice_identical': bool(input_identical),
        'recompute_deterministic': all_deterministic,
        'stored_pct_reproduced_exactly': all_match,
        'formula': 'rolling 1250d percentile, min_periods=250 (与 build_portrait.py pct() 同实现)',
        'columns': details,
    }
    with open(os.path.join(OUT_DIR, f'reproduce_check_{TODAY}.json'), 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    lines = [f"# 复现性检查（{TODAY}）", "",
             f"- 快照：`{result['snapshot']}`（{result['rows']} 行，{result['date_range'][0]} ~ {result['date_range'][1]}，sha256 `{digest[:16]}…`）",
             f"- 两次读取逐值一致：{'✅' if input_identical else '❌'}",
             f"- 两遍重算确定性一致：{'✅' if all_deterministic else '❌'}",
             f"- 存储分位可精确复现：{'✅' if all_match else '⚠️ 存在差异列'}", "",
             "| 列 | 比对数 | 一致数 | 一致率 | 最大差 | 最差日期 | 备注 |",
             "|---|---|---|---|---|---|---|"]
    for c, d in details.items():
        lines.append(f"| {c} | {d['compared']} | {d['matched']} | {d['match_rate']} | {d['max_abs_diff']} | {', '.join(d['worst_dates']) if d['match_rate'] != 1 else '—'} | {d['note']} |")
    with open(os.path.join(OUT_DIR, f'reproduce_check_{TODAY}.md'), 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps({"identical": input_identical, "deterministic": all_deterministic,
                      "reproduced": all_match}, ensure_ascii=False))
    print("written reproduce_check")

if __name__ == '__main__':
    main()
