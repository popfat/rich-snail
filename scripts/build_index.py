#!/usr/bin/env python3
"""知识库结构化索引构建（B3 预备 / Q6 技术栈：SQLite + FTS5）

- 解析 knowledge_base 下全部卡片（YAML front matter + 正文）；
- 写入 indexes/kb.sqlite：cards 表（元数据）+ cards_fts（FTS5 全文）+ relations 表；
- 索引是可重建派生物：删除本文件不影响知识主记录（Markdown 卡片）。
"""
import os, re, sqlite3, sys, glob, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB = os.path.join(ROOT, 'knowledge_base')
DB = os.path.join(ROOT, 'indexes', 'kb.sqlite')

FM_RE = re.compile(r'^---\n(.*?)\n---\n', re.S)
VALID_STATUS = {'draft','pending_review','pending_validation','observing','active',
                'deprecated','retired','rejected','archived'}

def parse_fm(text):
    m = FM_RE.match(text)
    if not m:
        return {}, text
    data = {}
    for line in m.group(1).splitlines():
        if ':' not in line:
            continue
        k, v = line.split(':', 1)
        k, v = k.strip(), v.strip()
        if v.startswith('[') and v.endswith(']'):
            items = [x.strip().strip('"').strip("'") for x in v[1:-1].split(',') if x.strip()]
            data[k] = items
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
    files = sorted(glob.glob(os.path.join(KB, '**', '*.md'), recursive=True))
    rows, rels, problems = [], [], []
    ids = set()
    for fp in files:
        text = open(fp, encoding='utf-8').read()
        meta, body = parse_fm(text)
        cid = meta.get('id')
        if not cid:
            problems.append(f"{fp}: 缺少 front matter id"); continue
        ids.add(cid)
        rows.append((cid, meta.get('type',''), meta.get('title',''), meta.get('status',''),
                     int(meta.get('version','1') or 1), meta.get('origin',''),
                     meta.get('created_at',''), meta.get('updated_at',''),
                     meta.get('decision_role',''), meta.get('evidence_grade',''),
                     ','.join(meta.get('source_ids',[]) if isinstance(meta.get('source_ids'),list) else []),
                     meta.get('market_scope',''), meta.get('timeframe',''),
                     os.path.relpath(fp, ROOT), sha256(fp), body[:200000]))
        for rel_key in ('source_ids','related_ids'):
            v = meta.get(rel_key, [])
            if isinstance(v, str): v = [v] if v else []
            for t in v:
                rels.append((cid, rel_key, t))
        st = meta.get('status','')
        if st and st not in VALID_STATUS:
            problems.append(f"{cid}: 非法状态 {st}")
    # 引用完整性
    for cid, rel_key, t in rels:
        if rel_key == 'source_ids' and t not in ids:
            problems.append(f"{cid}: source_ids 引用了不存在的 {t}")

    os.makedirs(os.path.dirname(DB), exist_ok=True)
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE cards(
      id TEXT PRIMARY KEY, type TEXT, title TEXT, status TEXT, version INTEGER,
      origin TEXT, created_at TEXT, updated_at TEXT, decision_role TEXT,
      evidence_grade TEXT, source_ids TEXT, market_scope TEXT, timeframe TEXT,
      path TEXT, sha256 TEXT, body TEXT);
    CREATE VIRTUAL TABLE cards_fts USING fts5(id, title, body, content='');
    CREATE TABLE relations(src_id TEXT, rel TEXT, dst_id TEXT);
    CREATE INDEX idx_cards_status ON cards(status);
    CREATE INDEX idx_cards_type ON cards(type);
    """)
    cur.executemany("INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    cur.executemany("INSERT INTO cards_fts(id, title, body) VALUES (?,?,?)",
                    [(r[0], r[2], r[15]) for r in rows])
    cur.executemany("INSERT INTO relations VALUES (?,?,?)", rels)
    con.commit()
    n = cur.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
    con.close()
    print(f"indexed={n} relations={len(rels)} problems={len(problems)}")
    for p in problems:
        print("PROBLEM:", p)
    return 1 if problems else 0

if __name__ == '__main__':
    sys.exit(main())
