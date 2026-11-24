# 人工审核队列（2026-11-24，首批 27 张卡片）

> 规则（契约 §2.3）：自动提取卡默认 `pending_review` / `pending_validation`，晋级须人工。
> 审核方式：逐张核对「原始依据与精确定位」是否与来源一致；通过后将 front matter 的 `status` 改为 `observing`（概念/指标/状态卡）或保持 `pending_validation` 待实验（假设/实验卡），并登记审核记录。

## A. 概念卡（7）— 重点核对定义是否忠实原文

| ID | 标题 | 来源 | 当前状态 |
|---|---|---|---|
| CON-000001 | 画像族与信号族两族划分 | SRC-000002 §1/§2 | pending_review |
| CON-000002 | 全指标百分位化口径 | SRC-000001 规则2 | pending_review |
| CON-000003 | 信号两级验证制与统计口径铁律 | SRC-000001/2/3 | pending_review |
| CON-000004 | 相似检索用纯画像距离 | SRC-000002 §6 | pending_review |
| CON-000005 | 原生口径与探索口径之分 | SRC-000010/11 | pending_review |
| CON-000006 | RobustZ 口径 | SRC-000016/5（⚠️ 原文小节待核对，open_question） | pending_review |
| CON-000007 | rich_trend 状态机与证据阶梯 | SRC-000014 | pending_review |

## B. 指标卡（7）— 登记卡，核对口径与"已知/未知用途"边界

FEA-000001 画像六维｜FEA-000002 信号族温度×离散×相关｜FEA-000003 主力流出压力｜FEA-000004 杠杆水位｜FEA-000005 宽基ETF净流入｜FEA-000006 蓄水池水位｜FEA-000007 行业资金状态标注 —— 均 pending_review。

## C. 假设卡（6）— 全部 pending_validation，需指定验证计划负责人

| ID | 命题 | 证据等级 | 备注 |
|---|---|---|---|
| HYP-000001 | D4b 贴地剔除（前视污染候审） | unverified | 候审协议原文照录；开庭样本进度 open_question |
| HYP-000002 | 温度冰点端做多有效性 | limited | 原文称已三重验证，本项目未独立复核 → 须 backtest 复验 |
| HYP-000003 | 冰点迁移修复全胜/恶化全负 | limited | 样本 n=10/5 极小 |
| HYP-000004 | 相似画像胜率溢价 | limited | n=78；需防相似度前视 |
| HYP-000005 | D4 深套企稳 | limited | 探索口径，真实时点样本积累中 |
| HYP-000006 | 主力流出压力候选信号 | unverified | 仅 3 年数据，观察中 |

## D. 实验卡（6）— 2 张 rejected 为负面留档（不可删除）

EXP-000001 中间带×离散度（rejected）｜EXP-000002 ETF 高分位做多（rejected）｜EXP-000003 P3 水位（探索）｜EXP-000004 P3b 剪枝（探索）｜EXP-000005 P3c 迁移风险（探索）｜EXP-000006 检索 A/B（limited）。

## E. 状态卡（1）

REG-000001 27 格 regime（draft）：分格阈值定义待从 `regime_matrix.py` 补全后方可升 observing。

## 空缺确认（G1 条件 4）

PBP / CAS / BEH 三类目录为空，符合"无材料不补造"；BEH 后续由 paperwalk/backtest 复盘经 LLM 提取（D9）。
