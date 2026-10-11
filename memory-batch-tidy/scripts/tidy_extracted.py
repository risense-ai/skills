#!/usr/bin/env python3
# tidy_extracted.py — 一次性把 rsrs「extract / 会话导入」产生的会话摘要散根收编到归档锚。
# 确定性、可逆、不依赖模型。默认 dry-run；加 --go 才写入（resort --go 会顺带复位 TIDY 计数）。
#
# 用法：
#   python tidy_extracted.py                       # 预览（不改动）
#   python tidy_extracted.py --go                  # 落库
#   python tidy_extracted.py --rsrs <路径> --client-only --backup <快照路径>
#
# 说明：把下面「配置区」改成你自己的项目关键词后再跑。
import argparse, json, os, re, shutil, subprocess, sys, tempfile

# ============ 配置区（改成你自己的项目）=====================================
# 视为“会话摘要散根”的标题前缀（脚本也会优先按 tag 识别，如 session-import）
PREFIXES = ('会话 ',)

# 归档锚挂在哪个树根下（用 rsrs 内置分类名，或节点 id / 前 8 位）
TARGET_ROOT = '编程开发'

# 归档锚规则： (key, 锚标题, [标题/正文关键词], [工作目录关键词])，最后一条作兜底
ANCHORS = [
    ('A',  '会话归档：项目A', ['项目A的独有关键词'], ['项目A路径片段']),
    ('B',  '会话归档：项目B', ['项目B的独有关键词'], ['项目B路径片段']),
    ('OT', '会话归档：其他',   [],                 []),
]

# 归档锚的正文（三段式，按 rsrs 显示规范）
ANCHOR_DESC = ('【前因】rsrs extract 自动导入的会话摘要（每会话一条、原为散根）。'
               '【行为】按规则归档于此。【后果】归档容器，子条为各会话摘要。')

# 识别散根的 tag 关键词（导入条目常带此类 tag）
EXTRACT_TAGS = ('session-import', 'extract')
# ==========================================================================

def find_rsrs(override=None):
    if override:
        return override
    home = os.path.expanduser('~')
    for c in (os.path.join(home, '.rsrs', 'bin', 'rsrs.exe'),
              os.path.join(home, '.rsrs', 'bin', 'rsrs')):
        if os.path.exists(c):
            return c
    w = shutil.which('rsrs')
    if w:
        return w
    sys.exit('找不到 rsrs，可用 --rsrs <路径> 指定')

def run(exe, base, args):
    r = subprocess.run([exe] + base + args, capture_output=True, text=True, encoding='utf-8')
    if r.returncode not in (0, 2):        # 2 = resort dry-run 的正常退出
        sys.stderr.write(r.stdout + r.stderr)
        sys.exit(1)
    return r.stdout

def workdir(content):
    m = re.search(r'工作目录\s*([^\n；]+)', content)
    w = m.group(1).strip().lower() if m else ''
    return '' if w in ('未知', 'unknown', '') else w

def is_extract_root(e):
    if e.get('parent_id'):
        return False
    tags = e.get('tags') or []
    if any(any(k in str(t) for k in EXTRACT_TAGS) for t in tags):
        return True
    return e['title'].startswith(PREFIXES)

def classify(e):
    text = (e['title'] + ' ' + e['content']).lower()
    wd = workdir(e['content'])
    for key, _title, kws, wkws in ANCHORS:
        if key == 'OT':
            continue
        if any(k.lower() in text for k in kws) or any(k.lower() in wd for k in wkws):
            return key
    return 'OT'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--go', action='store_true', help='实际写入（缺省仅预览）')
    ap.add_argument('--rsrs', help='rsrs 可执行文件路径（缺省自动探测）')
    ap.add_argument('--client-only', action='store_true', help='受限/沙盒环境加此开关')
    ap.add_argument('--backup', help='快照导出路径（缺省写到临时目录）')
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    exe = find_rsrs(args.rsrs)
    base = ['--client-only'] if args.client_only else []

    snap = args.backup or os.path.join(tempfile.gettempdir(), 'respire_snapshot.json')
    run(exe, base, ['export', snap])
    data = json.load(open(snap, encoding='utf-8'))

    roots = [e for e in data if is_extract_root(e)]
    print('总条数:', len(data), '| 散根数:', len(roots))
    if not roots:
        print('无散根，未做任何改动。')
        return

    by_title = {e['title']: e['id'] for e in data}
    aid = {}
    for key, title, _k, _w in ANCHORS:
        if title in by_title:                       # 同名锚已存在 → 复用
            aid[key] = by_title[title]
        else:
            out = run(exe, base, ['remember', ANCHOR_DESC, '--title', title,
                                  '--type', 'context', '--importance', 'important',
                                  '--parent', TARGET_ROOT, '--json'])
            aid[key] = json.loads(out)['summary']['id']

    cnt = {k: 0 for k in aid}
    ops = []
    for e in roots:
        k = classify(e)
        cnt[k] += 1
        ops.append({'id': e['id'][:8], 'parent': aid[k][:8]})
    print('分布:', cnt, '合计', sum(cnt.values()))

    spec = json.dumps({'ops': ops}, ensure_ascii=False)
    out = run(exe, base, ['resort', '--spec', spec] + (['--go'] if args.go else []) + ['--json'])
    print(json.loads(out)['summary'])
    if args.go:
        print('完成。请复验：rsrs audit --json / rsrs tree-cure / rsrs resort --status')

if __name__ == '__main__':
    main()
