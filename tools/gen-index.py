#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen-index.py — 从 data/characters.json 生成 characters/索引.md

索引是交叉视图（按字类 / 难度 / 今字 / 标签），不是内容事实源——
改字条后重新生成，不要手改。生成物入库，CI「可复现闸门」会核对它
是否等于链条跑出来的结果。

用法：
    python tools/gen-index.py            # 用 data/characters.json 生成 characters/索引.md
    python tools/gen-index.py --selftest # 临时数据自检

零依赖。
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def render(chars):
    lines = ['# 索引', '', '> 由 `tools/gen-index.py` 从 `data/characters.json` 生成，勿手改。共 %d 字。' % len(chars), '']

    # 按字类
    lines += ['## 按字类', '']
    bytype = {}
    for c in chars:
        bytype.setdefault(str(c.get('type') or '?'), []).append(c)
    for t in sorted(bytype):
        items = sorted(bytype[t], key=lambda c: (c.get('difficulty') or 0, str(c.get('id') or '')))
        lines.append('### %s（%d）' % (t, len(items)))
        for c in items:
            lines.append('- [%s](%s) → **%s**（难度 %d）' % (c.get('char'), c.get('path'), c.get('char'), c.get('difficulty') or 0))
        lines.append('')

    # 按难度
    lines += ['## 按难度', '']
    bydiff = {}
    for c in chars:
        bydiff.setdefault(int(c.get('difficulty') or 0), []).append(c)
    for d in sorted(bydiff):
        items = sorted(bydiff[d], key=lambda c: str(c.get('id') or ''))
        lines.append('### %d 星（%d）' % (d, len(items)))
        for c in items:
            lines.append('- [%s](%s) → **%s**' % (c.get('char'), c.get('path'), c.get('char')))
        lines.append('')

    # 按今字
    lines += ['## 按今字', '']
    bychar = {}
    for c in chars:
        bychar.setdefault(str(c.get('char') or '?'), []).append(c)
    for ch in sorted(bychar):
        items = sorted(bychar[ch], key=lambda c: str(c.get('id') or ''))
        lines.append('### %s（%d）' % (ch, len(items)))
        for c in items:
            lines.append('- [%s](%s)（%s，难度 %d）' % (c.get('char'), c.get('path'), c.get('type'), c.get('difficulty') or 0))
        lines.append('')

    # 按标签
    lines += ['## 按标签', '']
    bytag = {}
    for c in chars:
        for tag in (c.get('tags') or []):
            bytag.setdefault(str(tag), []).append(c)
    for tag in sorted(bytag):
        items = sorted(bytag[tag], key=lambda c: str(c.get('id') or ''))
        lines.append('### %s（%d）' % (tag, len(items)))
        for c in items:
            lines.append('- [%s](%s) → **%s**' % (c.get('char'), c.get('path'), c.get('char')))
        lines.append('')

    return '\n'.join(lines).rstrip() + '\n'


def build_index(data_json, out_md):
    payload = json.loads(Path(data_json).read_text(encoding='utf-8'))
    text = render(payload.get('chars', []))
    out_md.write_text(text, encoding='utf-8')
    return text


def main(argv=None):
    ap = argparse.ArgumentParser(description='生成 characters/索引.md')
    ap.add_argument('--root', default=str(ROOT))
    ap.add_argument('--selftest', action='store_true')
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    root = Path(args.root)
    data = root / 'data' / 'characters.json'
    if not data.exists():
        print('先跑 python tools/build.py 生成 data/characters.json')
        return 1
    out = root / 'characters' / '索引.md'
    build_index(data, out)
    print('index → %s' % out)
    return 0


def selftest():
    with tempfile.TemporaryDirectory() as td:
        tdr = Path(td)
        data = tdr / 'characters.json'
        payload = {'count': 2, 'chars': [
            {'id': 'ri', 'char': '日', 'char_len': 1, 'type': '自然现象',
             'difficulty': 1, 'author': '佚名', 'era': '商', 'source': 'S1',
             'license': 'public-domain', 'copyright': {'text': 'public-domain', 'annotations': 'cc-by-4.0'},
             'tags': ['太阳'], 'path': 'characters/自然现象/日.md'},
            {'id': 'ren', 'char': '人', 'char_len': 1, 'type': '人体动作',
             'difficulty': 1, 'author': '佚名', 'era': '商', 'source': 'S1',
             'license': 'public-domain', 'copyright': {'text': 'public-domain', 'annotations': 'cc-by-4.0'},
             'tags': ['人'], 'path': 'characters/人体动作/人.md'},
        ]}
        data.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
        out = tdr / '索引.md'
        text = build_index(data, out)
        failures = []
        for needle in ('按字类', '按难度', '按今字', '按标签', '### 自然现象（1）', '### 日（1）', '### 太阳（1）', '### 1 星（2）'):
            if needle not in text:
                failures.append('索引缺 %r' % needle)
        if out.read_text(encoding='utf-8') != text:
            failures.append('写盘与内存不一致')
    if failures:
        print('gen-index.py selftest FAILED:')
        for f in failures:
            print('  - ' + f)
        return 1
    print('gen-index.py selftest ok')
    return 0


if __name__ == '__main__':
    sys.exit(main())
