#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build-site.py — 从内容生成浏览站的站点副本

把 `characters/**/*.md` 与 `characters/**/*.png` 拷到 `site/characters/`
（VitePress 直接渲染成页面，图片随页面走），并从 `data/characters.json`
生成 `site/public/catalog.json` 与 `site/characters/索引.md`。
站点侧的页面骨架（index/guide/sources/print）是手写的，不进本脚本。

用法：
    python tools/build-site.py            # 用本仓
    python tools/build-site.py --selftest # 临时目录自检

零依赖。产物可复算（同输入同输出）。
"""

import argparse
import json
import sys
import tempfile
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build(root):
    chars_dir = root / 'characters'
    site_dir = root / 'site'
    data_json = root / 'data' / 'characters.json'
    out_chars = site_dir / 'characters'
    out_public = site_dir / 'public'

    payload = {}
    if data_json.exists():
        payload = json.loads(data_json.read_text(encoding='utf-8'))

    # 清空旧的 site/characters 与 catalog，避免残留
    if out_chars.exists():
        shutil.rmtree(out_chars)
    out_chars.mkdir(parents=True, exist_ok=True)
    out_public.mkdir(parents=True, exist_ok=True)

    copied_md = copied_png = 0
    for p in sorted(chars_dir.rglob('*.md')):
        if p.name == '索引.md':
            continue  # 索引单独生成
        rel = p.relative_to(chars_dir)
        dest = out_chars / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
        copied_md += 1
    for p in sorted(chars_dir.rglob('*.png')):
        rel = p.relative_to(chars_dir)
        dest = out_chars / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
        copied_png += 1

    # catalog.json：站点首页与筛选用
    catalog = {
        'version': payload.get('version', 1),
        'count': payload.get('count', 0),
        'types': payload.get('types', {}),
        'chars': payload.get('chars', []),
    }
    (out_public / 'catalog.json').write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    # 索引页：从 characters.json 渲染成 markdown，作为浏览入口
    index_text = render_index(payload.get('chars', []))
    (out_chars / '索引.md').write_text(index_text, encoding='utf-8')
    return copied_md, copied_png, payload.get('count', 0)


def render_index(chars):
    lines = ['# 甲骨文字形索引', '',
             '> 由 `tools/build-site.py` 从 `data/characters.json` 生成，共 %d 字。' % len(chars), '',
             '按字类分组，组内按难度排序。']
    bytype = {}
    for c in chars:
        bytype.setdefault(str(c.get('type') or '?'), []).append(c)
    for t in sorted(bytype):
        items = sorted(bytype[t], key=lambda c: (c.get('difficulty') or 0, str(c.get('id') or '')))
        lines.append('')
        lines.append('## %s（%d）' % (t, len(items)))
        lines.append('')
        for c in items:
            lines.append('- [%s](%s) → **%s**（难度 %d）' % (
                c.get('char'), c.get('path').replace('characters/', '', 1), c.get('char'), c.get('difficulty') or 0))
    return '\n'.join(lines).rstrip() + '\n'


def selftest():
    with tempfile.TemporaryDirectory() as td:
        tdr = Path(td)
        (tdr / 'characters' / '自然现象').mkdir(parents=True)
        (tdr / 'characters' / '自然现象' / '日.md').write_text(
            '---\nid: ri\nchar: 日\nchar_len: 1\ntype: 自然现象\n'
            'difficulty: 1\nauthor: 佚名\nera: 商\nsource: S1\nlicense: public-domain\n'
            'copyright: { text: public-domain, annotations: cc-by-4.0 }\nglyph: 自然现象/ri.png\n---\n\n# 日\n', encoding='utf-8')
        (tdr / 'characters' / '自然现象' / 'ri.png').write_bytes(b'\x89PNG\r\n\x1a\nfake')
        (tdr / 'data').mkdir()
        (tdr / 'data' / 'characters.json').write_text(json.dumps({
            'version': 1, 'count': 1, 'types': {'自然现象': 1},
            'chars': [{'id': 'ri', 'char': '日', 'char_len': 1,
                       'type': '自然现象', 'difficulty': 1, 'author': '佚名', 'era': '商',
                       'source': 'S1', 'license': 'public-domain',
                       'copyright': {'text': 'public-domain', 'annotations': 'cc-by-4.0'},
                       'tags': [], 'glyph': '自然现象/ri.png',
                       'path': 'characters/自然现象/日.md'}]}), encoding='utf-8')
        copied_md, copied_png, count = build(tdr)
        failures = []
        if copied_md != 1:
            failures.append('应拷贝 1 个字条 md，实 %d' % copied_md)
        if copied_png != 1:
            failures.append('应拷贝 1 个甲骨形 png，实 %d' % copied_png)
        if count != 1:
            failures.append('catalog count 错')
        if not (tdr / 'site' / 'characters' / '自然现象' / '日.md').exists():
            failures.append('字条页未生成')
        if not (tdr / 'site' / 'characters' / '自然现象' / 'ri.png').exists():
            failures.append('甲骨形 png 未生成')
        if not (tdr / 'site' / 'public' / 'catalog.json').exists():
            failures.append('catalog.json 未生成')
        if not (tdr / 'site' / 'characters' / '索引.md').exists():
            failures.append('索引页未生成')
        cat = json.loads((tdr / 'site' / 'public' / 'catalog.json').read_text(encoding='utf-8'))
        if cat.get('count') != 1 or cat.get('types', {}).get('自然现象') != 1:
            failures.append('catalog 内容错：%s' % cat)
    if failures:
        print('build-site.py selftest FAILED:')
        for f in failures:
            print('  - ' + f)
        return 1
    print('build-site.py selftest ok')
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description='生成浏览站站点副本')
    ap.add_argument('--root', default=str(ROOT))
    ap.add_argument('--selftest', action='store_true')
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    root = Path(args.root)
    copied_md, copied_png, count = build(root)
    print('built site: %d char pages + %d glyphs, catalog %d' % (copied_md, copied_png, count))
    return 0


if __name__ == '__main__':
    sys.exit(main())
