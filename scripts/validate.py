#!/usr/bin/env python3
"""B6 四类校验器（WP-B06-02，S1 最小实现）

1. schema 校验：front matter 必备字段、枚举值合法；
2. 引用校验：source_ids 存在且目标文件 sha256 与登记一致（原文不可变）；
3. 时间校验：日期字段格式；unknown 不猜测；knowledge_updated_at >= knowledge_created_at；
4. 状态机校验：状态枚举 + 自动流程禁止直 active（本库现状检查）。

退出码：0=全部通过；1=存在问题（输出清单）。
"""
import os, re, sys, glob, hashlib, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB = (sys.argv[sys.argv.index('--dir') + 1] if '--dir' in sys.argv
      else os.path.join(ROOT, 'knowledge_base'))
BASE = os.path.dirname(ROOT)

FM_RE = re.compile(r'^---\n(.*?)\n---\n', re.S)
REQUIRED = ['id','type','title','status','version','origin','created_at','updated_at',
            'source_ids','market_scope','universe','timeframe','horizon','regime_scope',
            'decision_role','evidence_grade','source_time','available_time','related_ids','tags']
VALID_STATUS = {'draft','pending_review','pending_validation','observing','active',
                'deprecated','retired','rejected','archived'}
VALID_ROLE = {'trigger','regime','filter','risk','explain','behavior','unknown'}
VALID_GRADE = {'unverified','limited','mixed','validated'}
VALID_TYPE = {'source','concept','feature','regime','hypothesis','playbook','case','behavior','experiment','decision'}
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

def parse_fm(text):
    m = FM_RE.match(text)
    if not m: return {}, text
    data = {}
    for line in m.group(1).splitlines():
        if ':' not in line: continue
        k, v = line.split(':', 1)
        k, v = k.strip(), v.strip()
        if v.startswith('[') and v.endswith(']'):
            data[k] = [x.strip().strip('"').strip("'") for x in v[1:-1].split(',') if x.strip()]
        else:
            data[k] = v
    return data, text[m.end():]

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    problems = []
    files = sorted(glob.glob(os.path.join(KB, '**', '*.md'), recursive=True))
    metas = {}
    src_registry = {}   # SRC id -> (relpath, sha)
    for fp in files:
        text = open(fp, encoding='utf-8').read()
        meta, body = parse_fm(text)
        cid = meta.get('id', os.path.basename(fp))
        metas[cid] = (meta, fp, body)
        # --- schema ---
        for req in REQUIRED:
            if req not in meta:
                problems.append(f"[schema] {cid}: 缺字段 {req}")
        st = meta.get('status','')
        if st and st not in VALID_STATUS:
            problems.append(f"[schema] {cid}: 非法 status={st}")
        if meta.get('decision_role') and meta['decision_role'] not in VALID_ROLE:
            problems.append(f"[schema] {cid}: 非法 decision_role={meta['decision_role']}")
        if meta.get('evidence_grade') and meta['evidence_grade'] not in VALID_GRADE:
            problems.append(f"[schema] {cid}: 非法 evidence_grade={meta['evidence_grade']}")
        if meta.get('type') and meta['type'] not in VALID_TYPE:
            problems.append(f"[schema] {cid}: 非法 type={meta['type']}")
        # --- 时间 ---
        for k in ('created_at','updated_at'):
            v = meta.get(k,'')
            if v and v != 'unknown' and not DATE_RE.match(v):
                problems.append(f"[time] {cid}: {k} 格式非法: {v}")
        ca, ua = meta.get('created_at',''), meta.get('updated_at','')
        if DATE_RE.match(ca or '') and DATE_RE.match(ua or '') and ua < ca:
            problems.append(f"[time] {cid}: updated_at({ua}) < created_at({ca})")
        # --- 状态机 ---
        if st == 'active' and meta.get('origin') in ('llm','hybrid'):
            problems.append(f"[status] {cid}: 自动/混合来源不得直接 active")
        if st == 'active' and meta.get('evidence_grade') in ('unverified',):
            problems.append(f"[status] {cid}: unverified 不得 active")
        # 收集 SRC 登记
        if meta.get('type') == 'source':
            m_path = re.search(r'\|\s*`?\.\./(.+?)`?\s*\|', body)
            m_sha = re.search(r'\| sha256 \| `([0-9a-f]{64})` \|', body)
            if m_path and m_sha:
                src_registry[cid] = (m_path.group(1), m_sha.group(1))
    # --- 引用校验 ---
    for cid, (meta, fp, body) in metas.items():
        sids = meta.get('source_ids', [])
        if isinstance(sids, str): sids = [sids] if sids else []
        if meta.get('type') != 'source' and not sids and meta.get('origin') != 'human':
            problems.append(f"[ref] {cid}: 非 source 卡缺少 source_ids")
        for sid in sids:
            if sid not in src_registry:
                problems.append(f"[ref] {cid}: 引用未登记来源 {sid}")
                continue
            rel, expect = src_registry[sid]
            ap = os.path.join(BASE, rel)
            if not os.path.exists(ap):
                problems.append(f"[ref] {cid}: 来源文件不存在 {rel}")
            elif sha256(ap) != expect:
                problems.append(f"[ref] {cid}: 来源 {sid} 原文已变更（sha256 不匹配），需人工核对")
    print(f"checked_cards={len(metas)} src_registered={len(src_registry)} problems={len(problems)}")
    for p in problems:
        print("PROBLEM:", p)
    return 1 if problems else 0

if __name__ == '__main__':
    sys.exit(main())
