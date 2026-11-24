# 最小运行日志（B7 / WP-B07-01 预研，S1）

> 单次运行目录 + JSONL 结构化日志；不做界面（8089 卡片页+详情页属 S2）。

## 目录约定

```
logs/
└── runs/
    └── {run_id}/              # run_id = {mode}_{YYYYMMDD_HHMMSS}（如 paperwalk_20261125_145000）
        ├── run.json           # 运行元数据（本文件 §2 schema）
        ├── events.jsonl       # 结构化事件流（每行一个 JSON）
        ├── inputs/            # 输入引用清单（快照 ID/版本，不复制数据）
        └── outputs/           # 产物引用（报告 ID、PTR ID、账本追加等）
```

重跑必须生成新 run_id，**不覆盖历史运行目录**（工程可靠性红线）。

## run.json schema

```json
{
  "run_id": "paperwalk_20261125_145000",
  "mode": "paperwalk | backtest",
  "started_at": "ISO8601",
  "ended_at": "ISO8601 | null",
  "status": "running | ok | failed | degraded | abstained",
  "failure_reason": "string | null",
  "input_versions": {"snapshots": [], "features": [], "kb_version": "", "config": {}},
  "outputs": {"report_id": "", "decision_id": "", "ptr_id": ""},
  "cost": {"api_calls": 0, "llm_tokens": 0, "wall_seconds": 0},
  "notes": ""
}
```

## events.jsonl 事件类型

`run_start / input_loaded / validation_failed / degraded / abstained / output_written / run_end / error`

每行：`{"ts": "...", "event": "...", "detail": {...}}`

## 状态语义

- `failed`：关键输入缺失/校验失败/调用失败——必须显式，禁止静默；
- `degraded`：部分输入缺失但按契约降级输出（报告中标注）；
- `abstained`：触发弃权条件（报告主体结论=证据不足）。
