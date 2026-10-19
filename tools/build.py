#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build.py — Markdown 甲骨文字条 → data/characters.json + data/checksums.json

内容仓的「编译」步骤：把 `characters/**/*.md`（唯一事实源）编译成机读数据。
分站、玩法、索引都只读这份 `characters.json`，不直接读 md。

与字谜仓的差异：本仓的内容除了 md，还有甲骨形 png。所以 checksums.json
同时覆盖 md 与 png——字形图也是唯一事实源的一部分，改一个字节 CI 就红。

用法：
    python tools/build.py                 # 用仓库根目录，写到 data/
    python tools/build.py --root X --out Y   # 指向别的目录（自检/测试用）
    python tools/build.py --selftest        # 在临时目录跑通全流程，证明产物可复算

零依赖：纯 Python 标准库。
"""

import argparse
import ast
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fm  # noqa: E402

# 字条 frontmatter 里序列化进 characters.json 的字段（固定顺序 → 产物可复算）
FIELDS = [
    'id', 'char', 'char_len', 'type', 'subtype', 'difficulty',
    'author', 'era', 'source', 'license', 'copyright', 'glyph', 'scan', 'tags',
]

# 画字玩法（PLAN-画甲骨文 §4）的笔画数据：直接从 gen-glyphs.py 的 GLYPHS 字面量
# 提取（AST，不 import——那会连 PIL 和绘制副作用一起带上）。
# 渲染用的坐标就是判定用的坐标，两者同源（gen-glyphs.py 是字形的唯一真源）。
GLYPH_PRIMITIVES = {'line', 'dot', 'circle', 'ellipse', 'arc', 'rect'}


def load_glyph_strokes(tools_dir):
    """从 tools/gen-glyphs.py 的 GLYPHS 字面量提取 {id: [图元…]}。

    文件不存在（自检的临时目录）返回 None——调用方留空，validate check11 会报。
    """
    src = tools_dir / 'gen-glyphs.py'
    if not src.exists():
        return None
    tree = ast.parse(src.read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == 'GLYPHS' for t in node.targets
        ):
            raw = ast.literal_eval(node.value)
            out = {}
            for gid, (typ, strokes) in raw.items():
                # prims 保持 literal_eval 的原始元组形式——指纹算法（repr）对
                # 圆括号/方括号敏感，转换必须在算完指纹之后（自检实抓过一次全库漂移）
                out[gid] = {'type': typ, 'prims': strokes}
            return out
    raise ValueError('gen-glyphs.py 里没有 GLYPHS 定义')


def parse_char_file(path):
    """读一个 .md，返回 (frontmatter dict, 相对路径 str)。"""
    text = path.read_text(encoding='utf-8')
    data, _body = fm.parse_frontmatter(text)
    return data, path


def collect(chars_dir):
    """扫 characters 目录，返回按 (type, difficulty, id) 排序的字目列表。"""
    out = []
    if not chars_dir.exists():
        return out
    for p in sorted(chars_dir.rglob('*.md')):
        if p.name == '索引.md':
            continue  # 生成的索引不是内容
        data, _ = parse_char_file(p)
        rec = {}
        for f in FIELDS:
            rec[f] = data.get(f)
        rec['path'] = p.relative_to(chars_dir.parent).as_posix()
        out.append(rec)
    out.sort(key=lambda r: (str(r.get('type') or ''), r.get('difficulty') or 0, str(r.get('id') or '')))
    return out


def type_counts(chars):
    c = {}
    for r in chars:
        t = r.get('type')
        if t:
            c[t] = c.get(t, 0) + 1
    return c


def build(chars_dir, out_dir, tools_dir=None):
    chars = collect(chars_dir)
    glyphs = load_glyph_strokes(tools_dir) if tools_dir else None
    # stroke_count 是外源数据（Unihan kTotalStrokes，CI 上没有），从重算前的
    # characters.json 沿用同 id 的值——不重算、不编造，读不到就 None。
    prev_by_id = {}
    prev_path = out_dir / 'characters.json'
    if prev_path.exists():
        try:
            prev_by_id = {c.get('id'): c for c in
                          json.loads(prev_path.read_text(encoding='utf-8')).get('chars', [])}
        except (ValueError, OSError):
            prev_by_id = {}
    for rec in chars:
        prev = prev_by_id.get(rec['id']) or {}
        rec['stroke_count'] = prev.get('stroke_count')
        if glyphs is None:
            continue
        g = glyphs.get(rec['id'])
        if not g:
            rec['strokes'] = None
            rec['glyph_fingerprint'] = None
            continue
        # strokes 转成 list 便于 JSON；指纹沿用 build-fingerprints.py 的算法定义
        # （repr(list(图元元组)) 的 sha256 前 16 位）——换算法会全库改指纹，禁改。
        rec['strokes'] = [list(s) for s in g['prims']]
        rec['glyph_fingerprint'] = hashlib.sha256(
            repr(g['prims']).encode('utf-8')).hexdigest()[:16]
    payload = {
        'version': 1,
        'count': len(chars),
        'types': type_counts(chars),
        'chars': chars,
    }
    if glyphs is not None:
        payload['strokesSource'] = {
            'from': 'tools/gen-glyphs.py GLYPHS',
            'glyphs': len(glyphs),
            'covered': sum(1 for r in chars if r.get('strokes')),
        }
    json_text = json.dumps(payload, ensure_ascii=False, indent=2) + '\n'

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'characters.json').write_text(json_text, encoding='utf-8')

    # checksums：每个源 md 与甲骨形 png 的 sha256（相对路径 → 哈希），供消费端校验未被篡改
    sums = {}
    for p in sorted(chars_dir.rglob('*.md')):
        if p.name == '索引.md':
            continue
        rel = p.relative_to(chars_dir).as_posix()
        sums[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    for p in sorted(chars_dir.rglob('*.png')):
        rel = p.relative_to(chars_dir).as_posix()
        sums[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    sums_text = json.dumps(sums, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    (out_dir / 'checksums.json').write_text(sums_text, encoding='utf-8')
    return payload


def main(argv=None):
    ap = argparse.ArgumentParser(description='Markdown 甲骨文字条 → characters.json')
    ap.add_argument('--root', default=str(ROOT), help='仓库根目录（默认本仓）')
    ap.add_argument('--out', default=None, help='输出目录（默认 <root>/data）')
    ap.add_argument('--selftest', action='store_true', help='在临时目录自检')
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    root = Path(args.root)
    out_dir = Path(args.out) if args.out else root / 'data'
    payload = build(root / 'characters', out_dir, tools_dir=root / 'tools')
    print('built %d characters → %s' % (payload['count'], out_dir / 'characters.json'))
    if 'strokesSource' in payload:
        s = payload['strokesSource']
        print('strokes: GLYPHS %d 条 → 覆盖 %d 字' % (s['glyphs'], s['covered']))
    return 0


# -------------------------------------------------------- 自检
def selftest():
    """在临时目录造两个合法字目 + 字形，验证 build 与复算一致。"""
    failures = []
    with tempfile.TemporaryDirectory() as td:
        tdr = Path(td)
        cdir = tdr / 'characters' / '自然现象'
        cdir.mkdir(parents=True)
        good = (
            '---\n'
            'id: ri\n'
            'char: 日\n'
            'char_len: 1\n'
            'type: 自然现象\n'
            'difficulty: 1\n'
            'author: 佚名\n'
            'era: 商\n'
            'source: S1\n'
            'license: public-domain\n'
            'copyright: { text: public-domain, annotations: cc-by-4.0 }\n'
            'glyph: 自然现象/ri.png\n'
            'tags: [太阳]\n'
            '---\n\n# 日\n\n**今字**：日\n\n## 解析\n圆圈带点为日。\n'
        )
        (cdir / '日.md').write_text(good, encoding='utf-8')
        (cdir / 'ri.png').write_bytes(b'\x89PNG\r\n\x1a\nfake')
        out1 = tdr / 'out1'
        build(tdr / 'characters', out1)
        j1 = json.loads((out1 / 'characters.json').read_text(encoding='utf-8'))
        c1 = (out1 / 'checksums.json').read_text(encoding='utf-8')

        # 再跑一次：产物必须逐字节一致（可复算）
        out2 = tdr / 'out2'
        build(tdr / 'characters', out2)
        j2 = json.loads((out2 / 'characters.json').read_text(encoding='utf-8'))
        c2 = (out2 / 'checksums.json').read_text(encoding='utf-8')

        if j1 != j2:
            failures.append('两次构建产物不一致（不可复算）')
        if c1 != c2:
            failures.append('两次 checksums 不一致')
        if j1['count'] != 1:
            failures.append('应只有 1 个字目，实得 %s' % j1['count'])
        if j1['chars'][0]['id'] != 'ri' or j1['chars'][0]['char'] != '日':
            failures.append('字目字段解析错误：%s' % j1['chars'][0])
        if 'characters/自然现象/日.md' not in j1['chars'][0]['path']:
            failures.append('path 未记录：%s' % j1['chars'][0]['path'])
        if len(j1['types']) != 1 or j1['types'].get('自然现象') != 1:
            failures.append('types 统计错误：%s' % j1['types'])
        # checksums 必须覆盖 md 与 png
        sums = json.loads(c1)
        if not any('日.md' in k for k in sums):
            failures.append('checksums 未覆盖源 md')
        if not any('ri.png' in k for k in sums):
            failures.append('checksums 未覆盖甲骨形 png')

        # 索引.md 不应被当成内容
        (cdir / '索引.md').write_text('# 索引\n', encoding='utf-8')
        out3 = tdr / 'out3'
        build(tdr / 'characters', out3)
        j3 = json.loads((out3 / 'characters.json').read_text(encoding='utf-8'))
        if j3['count'] != 1:
            failures.append('索引.md 被当成字目收录（count=%s）' % j3['count'])

    if failures:
        print('build.py selftest FAILED:')
        for f in failures:
            print('  - ' + f)
        return 1
    print('build.py selftest ok')
    return 0


if __name__ == '__main__':
    sys.exit(main())
