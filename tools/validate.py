#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""validate.py — 甲骨文内容仓十二项校验（任何一项失败即 exit 1）

沿用「文档即契约」：docs/scope.md 里的收录清单是第 1 项的可执行契约。
每个检查都是一个纯函数 `checkN(chars, ctx) -> [错误串]`，这样
`--selftest` 可以直接拿坏样本喂给单个检查，证明它真的拦得住坏例子。

十二项校验：
    1. 收录范围完整性  —— scope.md 要求收录的必须齐，框架外的不得多收
    2. id 唯一性       —— 全库 id 不重复
    3. 今字字段        —— char 非空、必须单字、char_len 与 char 字数一致
    4. 难度合法        —— difficulty 必须在 1–5
    5. 台账完整        —— 缺 source / license 的字目
    6. 版权核验        —— license=cc-by-4.0 必须是我方原创（authors.json 里 ours=true）
    7. frontmatter    —— 必填字段齐全（含 glyph，且 glyph 文件存在）
    8. 公版证据        —— license=public-domain 且 era=当代 的署名作者，卒年须 ≤ 当前年−50
    9. 去重            —— 今字全库唯一；同字多解须登记 known-defects.json
    10. 字类合法       —— type 必须取自合法集
    11. 笔画覆盖       —— 画字玩法的 strokes 闸门（PLAN-画甲骨文 §4.2）：
        GLYPHS 全覆盖、图元 6 种、坐标 512 内、共图组必须登记
    12. 拓片出处       —— OBIMD 断供三级口径闸门（docs/sources.md）：
        scan 有 → md 必须有 S6 拓片行或 S7 参考图行（互斥），scanKind 与之对应
        scan 无 → md 必须有「暂无真骨片拓片」兜底说明（不许拿形近字拓片冒充）

用法：
    python tools/validate.py             # 完整校验（第 1 项生效）
    python tools/validate.py --partial   # 增量期：跳过第 1 项「收录范围」
    python tools/validate.py --selftest  # 证明每个护栏抓得住坏样本
"""

import datetime
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHARS_DIR = ROOT / 'characters'
SCOPE = ROOT / 'docs' / 'scope.md'
AUTHORS = ROOT / 'data' / 'authors.json'
DEFECTS = ROOT / 'data' / 'known-defects.json'
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fm  # noqa: E402

# 必填字段（第 7 项）。copyright 允许为 dict 或缺失时报错，下面单独处理。
REQUIRED = ['id', 'char', 'char_len', 'type', 'difficulty',
            'author', 'era', 'source', 'license', 'glyph']

# 字类合法集（第 10 项），与 docs/scope.md 的分类一致。
TYPES = ['自然现象', '动植物', '人体动作', '器物', '数目', '抽象']

# 我国《著作权法》：自然人作品保护期为作者终生及其死亡后第 50 年的 12 月 31 日。
COPYRIGHT_YEARS = 50

# 调色
class C:
    OK, FAIL, WARN, BOLD, DIM, END = '\033[32m', '\033[31m', '\033[33m', '\033[1m', '\033[2m', '\033[0m'
    @classmethod
    def off(cls):
        for k in ('OK', 'FAIL', 'WARN', 'BOLD', 'DIM', 'END'):
            setattr(cls, k, '')
if not sys.stdout.isatty():
    C.off()


# -------------------------------------------------- 装载
def load_chars(chars_dir):
    """返回 [(rec, relpath)]，rec 是 frontmatter dict。跳过 索引.md。"""
    out = []
    if not chars_dir.exists():
        return out
    for p in sorted(chars_dir.rglob('*.md')):
        if p.name == '索引.md':
            continue
        data, _ = fm.parse_frontmatter(p.read_text(encoding='utf-8'))
        data['__path__'] = p.relative_to(chars_dir).as_posix()
        out.append(data)
    return out


def load_authors(path):
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding='utf-8'))
    return {a.get('name'): a for a in raw.get('authors', [])}


def load_defects(path):
    if not path.exists():
        return set()
    raw = json.loads(path.read_text(encoding='utf-8'))
    return {d.get('key') for d in raw.get('defects', []) if d.get('key')}


def parse_scope(path):
    """解析 scope.md 的「收录清单（契约）」表 → {id: (type, char)}。"""
    if not path.exists():
        return {}
    text = path.read_text(encoding='utf-8')
    out = {}
    in_sec = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith('## ') and '收录清单' in s:
            in_sec = True
            continue
        if in_sec and s.startswith('## '):
            break
        if not in_sec or not s.startswith('|'):
            continue
        cells = [c.strip() for c in s.strip('|').split('|')]
        if len(cells) < 3:
            continue
        idc, typ, ch = cells[0], cells[1], cells[2]
        if idc in ('id', '') or set(idc) <= set('-: '):
            continue  # 表头 / 分隔行
        out[idc] = (typ, ch)
    return out


# -------------------------------------------------- 十一个检查（纯函数）
def check1_scope(chars, scope):
    errs = []
    have = {c.get('id'): c for c in chars}
    for sid in sorted(scope):
        if sid not in have:
            errs.append('收录清单要求收录但缺失：%s' % sid)
            continue
        typ, ch = scope[sid]
        c = have[sid]
        if typ and c.get('type') != typ:
            errs.append('%s 字类不符：清单=%s 实=%s' % (sid, typ, c.get('type')))
        if ch and str(c.get('char')) != ch:
            errs.append('%s 今字不符：清单=%s 实=%s' % (sid, ch, c.get('char')))
    for c in chars:
        if c.get('id') not in scope:
            errs.append('多收框架外字目：%s（%s）' % (c.get('id'), c.get('char')))
    return errs


def check2_id_unique(chars):
    seen, errs = {}, []
    for c in chars:
        i = c.get('id')
        if i is None:
            continue  # 第 7 项会报缺 id
        if i in seen:
            errs.append('id 重复：%s（%s 与 %s）' % (i, seen[i], c.get('__path__')))
        else:
            seen[i] = c.get('__path__')
    return errs


def check3_char(chars):
    """char 非空、必须单字、char_len 与 char 字数一致。"""
    errs = []
    for c in chars:
        ch = c.get('char')
        if ch is None or str(ch).strip() == '':
            errs.append('%s 今字为空' % c.get('id'))
            continue
        ch = str(ch)
        if len(ch) != 1:
            errs.append('%s 今字非单字：%r（字库只收单字）' % (c.get('id'), ch))
            continue
        cl = c.get('char_len')
        if cl is not None and int(cl) != len(ch):
            errs.append('%s char_len=%s 与今字字数 %d 不符' % (c.get('id'), cl, len(ch)))
    return errs


def check4_difficulty(chars):
    errs = []
    for c in chars:
        d = c.get('difficulty')
        if d is None:
            continue  # 第 7 项报缺
        try:
            d = int(d)
        except (TypeError, ValueError):
            errs.append('%s difficulty 非整数：%r' % (c.get('id'), d))
            continue
        if not (1 <= d <= 5):
            errs.append('%s difficulty=%s 超出 1–5' % (c.get('id'), d))
    return errs


def check5_ledger(chars):
    errs = []
    for c in chars:
        for f in ('source', 'license'):
            if not c.get(f):
                errs.append('%s 缺台账字段：%s' % (c.get('id'), f))
    return errs


def check6_copyright(chars, authors):
    """cc-by-4.0 的原文必须是我方原创。"""
    errs = []
    for c in chars:
        lic = c.get('license')
        if lic != 'cc-by-4.0':
            continue
        a = authors.get(c.get('author'))
        if not a or not a.get('ours'):
            errs.append('%s 原文为 cc-by-4.0 但作者 %r 非我方原创（authors.json 无 ours=true）'
                        % (c.get('id'), c.get('author')))
    return errs


def check7_frontmatter(chars, chars_dir):
    errs = []
    for c in chars:
        missing = [f for f in REQUIRED if c.get(f) in (None, '')]
        if missing:
            errs.append('%s 缺必填字段：%s' % (c.get('id'), '/'.join(missing)))
        if not isinstance(c.get('copyright'), dict):
            errs.append('%s copyright 必须是映射 {text, annotations}' % c.get('id'))
        # 图形完备：glyph 路径（相对 characters/）必须存在且非空
        glyph = c.get('glyph')
        if glyph:
            gpath = chars_dir / glyph
            if not gpath.exists():
                errs.append('%s 甲骨形缺失：%s' % (c.get('id'), glyph))
            elif gpath.stat().st_size == 0:
                errs.append('%s 甲骨形为空文件：%s' % (c.get('id'), glyph))
        # 原拓片（可选）：scan 字段若存在，文件必须在且非空（没配扫描图的字用渲染图，不卡验收）
        scan = c.get('scan')
        if scan:
            spath = chars_dir / scan
            if not spath.exists():
                errs.append('%s 原拓片缺失：%s' % (c.get('id'), scan))
            elif spath.stat().st_size == 0:
                errs.append('%s 原拓片为空文件：%s' % (c.get('id'), scan))
    return errs


def check8_publicdomain(chars, authors, year):
    """public-domain 且 era=当代 的署名作者，卒年须 ≤ 当前年−50。"""
    errs = []
    cutoff = year - COPYRIGHT_YEARS
    for c in chars:
        if c.get('license') != 'public-domain':
            continue
        if c.get('era') != '当代':
            continue  # 商代 / 匿名 → 显然公版
        author = c.get('author')
        if author in (None, '', '佚名'):
            continue
        a = authors.get(author)
        if a is None:
            errs.append('%s 当代署名作者 %r 不在 authors.json' % (c.get('id'), author))
            continue
        died = a.get('died')
        if died is None:
            errs.append('%s 当代作者 %r 缺卒年（仍在保护期）' % (c.get('id'), author))
        elif died > cutoff:
            errs.append('%s 作者 %r 卒于 %s，晚于「当前年 − 50 = %d」，仍在保护期'
                        % (c.get('id'), author, died, cutoff))
    return errs


def check9_dedup(chars, defects):
    """今字全库唯一；同字多解须登记 known-defects。"""
    errs = []
    chars_ = [(str(c.get('char')), c.get('id')) for c in chars if c.get('char')]
    for i in range(len(chars_)):
        for j in range(i + 1, len(chars_)):
            c1, id1 = chars_[i]
            c2, id2 = chars_[j]
            if c1 == c2:
                if id1 not in defects and id2 not in defects:
                    errs.append('今字重复未登记：%r(%s) 与 %r(%s)' % (c1, id1, c2, id2))
    return errs


def check10_type(chars):
    errs = []
    for c in chars:
        t = c.get('type')
        if t is None:
            continue  # 第 7 项报缺
        if t not in TYPES:
            errs.append('%s 字类非法：%r（合法集：%s）' % (c.get('id'), t, '/'.join(TYPES)))
    return errs


# 画字玩法的笔画数据（PLAN-画甲骨文 §4.2）：图元 6 种、画布 512×512
GLYPH_PRIMITIVES = {'line': 4, 'dot': 3, 'circle': 3, 'ellipse': 4, 'arc': 5, 'rect': 4}
GLYPH_CANVAS = 512


def check11_strokes(data_chars, md_ids, defects):
    """笔画覆盖（画字玩法的数据闸门）。data_chars = data/characters.json 的记录。

    - 每字必须有 strokes（GLYPHS 覆盖），缺失即报——画字玩法没数据就是死谜
    - 每个图元：类型在 6 种之内、参数个数对、坐标在 512 画布内
    - md 与 json 的 id 集必须一致（strokes 是按 id 挂的，挂错身就是另一道死谜）
    - 渲染字形共图组（指纹相同、字数 >1）必须登记 known-defects——
      「多个字渲染一模一样」是内容质量债（懒人字形定义），不许静默；
      正解是按《甲骨文字典》逐批补真实字形，登记 = 知情放行，先上后修
    """
    errs = []
    if data_chars is None:
        errs.append('读不到 data/characters.json：先跑 python tools/build.py')
        return errs
    json_ids = {c.get('id') for c in data_chars}
    for i in sorted(md_ids ^ json_ids):
        errs.append('characters.json 与 md 的 id 不一致：%s（strokes 会挂错身）' % i)
    for c in data_chars:
        cid = c.get('id')
        st = c.get('strokes')
        if not st or not isinstance(st, list):
            errs.append('%s 缺笔画数据（GLYPHS 未覆盖）' % cid)
            continue
        for i, prim in enumerate(st):
            where = '%s strokes[%d]' % (cid, i)
            if not isinstance(prim, list) or not prim or prim[0] not in GLYPH_PRIMITIVES:
                errs.append('%s 图元非法：%r' % (where, prim))
                continue
            want = GLYPH_PRIMITIVES[prim[0]]
            if len(prim) - 1 != want:
                errs.append('%s %s 参数应为 %d 个，实得 %d' % (where, prim[0], want, len(prim) - 1))
            for v in prim[1:]:
                if not isinstance(v, (int, float)) or v < 0 or v > GLYPH_CANVAS:
                    errs.append('%s 坐标越界（0–512）：%r' % (where, v))
    # 共图组：渲染字形指纹相同、字数 >1 的组必须显式登记
    from collections import defaultdict
    groups = defaultdict(list)
    for c in data_chars:
        fp = c.get('glyph_fingerprint')
        if fp:
            groups[fp].append(c.get('id'))
    dup_groups = {fp: ids for fp, ids in groups.items() if len(ids) > 1}
    registered = any(str(k).startswith('glyph-duplicate:') for k in defects)
    if dup_groups and not registered:
        worst = max(dup_groups.values(), key=len)
        errs.append('渲染字形共图 %d 组 / %d 字未登记（最大组 %d 字，如 %s）：'
                    '在 known-defects.json 登记 key 前缀 glyph-duplicate: 的条目，'
                    '或按《甲骨文字典》补真实字形'
                    % (len(dup_groups), sum(len(v) for v in dup_groups.values()),
                       len(worst), '/'.join(worst[:3])))
    return errs


# 拓片出处三级口径的规约行（与 build.py 的 SCAN_MARKS 同源同义——
# md 正文是唯一事实源，build 负责编译成 scanKind，这里负责拦住不合契约的）
SCAN_MARKS = {
    'obimd': '原拓片图：KLOBIP/OBIMD',
    'ref': '甲骨原形图：Wikimedia Commons',
}


def check12_scan_provenance(data_chars, chars_dir):
    """拓片出处三级口径（OBIMD 断供策略闸门，docs/sources.md「字形图的来源」）。

      scan 有 → md 正文必须恰好一类出处行（S6 真拓片 / S7 参考图，互斥），
                characters.json 的 scanKind 必须与之对应
      scan 无 → md 正文必须有「暂无真骨片拓片」兜底说明——「舟」的教训：
                OBIMD 里 19 处形近字拓片（立/午/卜）全部弃用，不许冒充
    """
    errs = []
    if data_chars is None:
        errs.append('读不到 data/characters.json：先跑 python tools/build.py')
        return errs
    for c in data_chars:
        cid = c.get('id')
        path = c.get('path')
        if not path:
            errs.append('%s 缺 path（characters.json 是旧产物，重跑 build）' % cid)
            continue
        md = chars_dir.parent / path
        if not md.exists():
            errs.append('%s 字条 md 缺失：%s' % (cid, path))
            continue
        body = md.read_text(encoding='utf-8')
        kinds = [k for k, mark in SCAN_MARKS.items() if mark in body]
        scan = c.get('scan')
        if scan:
            if len(kinds) > 1:
                errs.append('%s 拓片出处行既有 S6 又有 S7——两类互斥，删掉错的那个' % cid)
            elif not kinds:
                errs.append('%s 有 scan 但 md 没有出处行（S6「原拓片图：KLOBIP/OBIMD」或 '
                            'S7「甲骨原形图：Wikimedia Commons」）——出处不明，不许默认' % cid)
            elif c.get('scanKind') != kinds[0]:
                errs.append('%s scanKind=%r 与 md 出处行（%s）不符：重跑 build 刷新产物'
                            % (cid, c.get('scanKind'), kinds[0]))
        else:
            if kinds:
                errs.append('%s 无 scan 却写了拓片出处行：图都没挂，出处行是摆设' % cid)
            elif '暂无真骨片拓片' not in body:
                errs.append('%s 无 scan 也没有「暂无真骨片拓片」兜底说明——渲染图兜底必须如实声明' % cid)
            if c.get('scanKind') is not None:
                errs.append('%s 无 scan 但 scanKind=%r（应为 null）：重跑 build' % (cid, c.get('scanKind')))
    return errs


# -------------------------------------------------- 汇总
def run_checks(chars, ctx, partial=False):
    scope, authors, defects, year = ctx['scope'], ctx['authors'], ctx['defects'], ctx['year']
    groups = [
        ('收录范围完整性', check1_scope(chars, scope), partial),
        ('id 唯一性', check2_id_unique(chars), False),
        ('今字字段', check3_char(chars), False),
        ('难度合法', check4_difficulty(chars), False),
        ('台账完整', check5_ledger(chars), False),
        ('版权核验', check6_copyright(chars, authors), False),
        ('frontmatter', check7_frontmatter(chars, ctx['chars_dir']), False),
        ('公版证据', check8_publicdomain(chars, authors, year), False),
        ('去重', check9_dedup(chars, defects), False),
        ('字类合法', check10_type(chars), False),
        ('笔画覆盖', check11_strokes(ctx.get('data_chars'), {c.get('id') for c in chars}, defects), False),
        ('拓片出处', check12_scan_provenance(ctx.get('data_chars'), ctx['chars_dir']), False),
    ]
    total_err = 0
    for name, errs, skipped in groups:
        if skipped:
            print('%s [skip] %s（--partial）' % (C.DIM, name))
            continue
        if errs:
            total_err += len(errs)
            print('%s [FAIL] %s：%d 项' % (C.FAIL, name, len(errs)))
            for e in errs:
                print('         - ' + e)
        else:
            print('%s [ok] %s' % (C.OK, name))
    return total_err


def ctx_for(root):
    data_chars = None
    data_path = root / 'data' / 'characters.json'
    if data_path.exists():
        data_chars = json.loads(data_path.read_text(encoding='utf-8')).get('chars')
    return {
        'scope': parse_scope(root / 'docs' / 'scope.md'),
        'authors': load_authors(root / 'data' / 'authors.json'),
        'defects': load_defects(root / 'data' / 'known-defects.json'),
        'year': datetime.date.today().year,
        'chars_dir': root / 'characters',
        'data_chars': data_chars,
    }


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    partial = '--partial' in argv
    if '--selftest' in argv:
        return selftest()
    root = ROOT
    chars = load_chars(root / 'characters')
    ctx = ctx_for(root)
    errs = run_checks(chars, ctx, partial)
    print()
    if errs:
        print('%s十二项校验共 %d 个错误%s' % (C.FAIL, errs, C.END))
        return 1
    print('%s十二项校验全绿（%d 篇字目）%s' % (C.OK, len(chars), C.END))
    return 0


# -------------------------------------------------- 自检：每个护栏必须抓得住坏样本
def selftest():
    def rec(**kw):
        base = dict(id='x', char='日', char_len=1, type='自然现象',
                    difficulty=1, author='佚名', era='商', source='S1',
                    license='public-domain', glyph='自然现象/x.png',
                    copyright={'text': 'public-domain', 'annotations': 'cc-by-4.0'})
        base.update(kw)
        return base

    authors = {'丢词大作战': {'ours': True, 'died': None},
               '在世作者': {'ours': False, 'died': 2020}}
    # check7 会查 glyph 文件存在，selftest 里造一个临时目录放干净样本的字形
    chars_dir = Path(tempfile.mkdtemp()) / 'characters'
    (chars_dir / '自然现象').mkdir(parents=True)
    (chars_dir / '自然现象' / 'a.png').write_bytes(b'png')
    (chars_dir / '自然现象' / 'b.png').write_bytes(b'png')
    # check12 的 md 样本：无出处行 / S7 行 / 兜底行 / S6+S7 并存 / 干净 S6
    (chars_dir / '自然现象' / 'a.md').write_text('# 测试\n\n正文没有任何拓片出处行。\n', encoding='utf-8')
    (chars_dir / '自然现象' / 'ref.md').write_text('# 测试\n\n甲骨原形图：Wikimedia Commons「x-oracle.svg」（公版）。\n', encoding='utf-8')
    (chars_dir / '自然现象' / 'none.md').write_text('# 测试\n\n**本字暂无真骨片拓片**，如实说明如下：\n', encoding='utf-8')
    (chars_dir / '自然现象' / 'both.md').write_text(
        '# 测试\n\n原拓片图：KLOBIP/OBIMD 甲骨文铭文多模态数据集（S6）。\n'
        '甲骨原形图：Wikimedia Commons「x-oracle.svg」（公版）。\n', encoding='utf-8')
    (chars_dir / '自然现象' / 'ok.md').write_text(
        '# 测试\n\n原拓片图：KLOBIP/OBIMD 甲骨文铭文多模态数据集（S6，CC-BY-4.0），主字 x。\n', encoding='utf-8')
    cases = [
        ('check1 收录范围', lambda: check1_scope([rec(id='a')], {'b': ('自然现象', '日')})),
        ('check1 多收框架外', lambda: check1_scope([rec(id='a')], {})),
        ('check2 id 重复', lambda: check2_id_unique([rec(id='a'), rec(id='a', char='月')])),
        ('check3 今字为空', lambda: check3_char([rec(char=None)])),
        ('check3 非单字', lambda: check3_char([rec(char='日月')])),
        ('check4 难度越界', lambda: check4_difficulty([rec(difficulty=9)])),
        ('check5 缺台账', lambda: check5_ledger([rec(source=None)])),
        ('check6 非我方 cc-by', lambda: check6_copyright([rec(license='cc-by-4.0', author='别人')], authors)),
        ('check7 缺必填', lambda: check7_frontmatter([rec(type=None)], chars_dir)),
        ('check8 当代未过保护期', lambda: check8_publicdomain(
            [rec(license='public-domain', era='当代', author='在世作者')], authors, 2026)),
        ('check9 今字重复', lambda: check9_dedup([rec(char='日'), rec(id='y', char='日')], set())),
        ('check10 字类非法', lambda: check10_type([rec(type='乱造')])),
        # check11 坏样本：笔画数据（画字玩法）
        ('check11 缺笔画', lambda: check11_strokes([dict(id='a', strokes=None)], {'a'}, set())),
        ('check11 图元类型非法', lambda: check11_strokes([dict(id='a', strokes=[['spiral', 1, 2]])], {'a'}, set())),
        ('check11 坐标越界', lambda: check11_strokes([dict(id='a', strokes=[['line', 0, 0, 600, 256]])], {'a'}, set())),
        ('check11 参数个数不对', lambda: check11_strokes([dict(id='a', strokes=[['circle', 256]])], {'a'}, set())),
        ('check11 共图未登记', lambda: check11_strokes(
            [dict(id='a', strokes=[['line', 0, 0, 100, 100]], glyph_fingerprint='fp1'),
             dict(id='b', strokes=[['line', 0, 0, 100, 100]], glyph_fingerprint='fp1')], {'a', 'b'}, set())),
        ('check11 json 与 md 的 id 集不一致', lambda: check11_strokes(
            [dict(id='a', strokes=[['line', 0, 0, 100, 100]])], {'a', 'zz'}, set())),
        # check12 坏样本：拓片出处（OBIMD 断供三级口径）
        ('check12 有 scan 无出处行（冒充拓片）', lambda: check12_scan_provenance(
            [dict(id='a', scan='自然现象/a.png', path='characters/自然现象/a.md', scanKind='obimd')], chars_dir)),
        ('check12 scanKind 与出处行矛盾', lambda: check12_scan_provenance(
            [dict(id='a', scan='自然现象/a.png', path='characters/自然现象/ref.md', scanKind='obimd')], chars_dir)),
        ('check12 无 scan 无兜底说明', lambda: check12_scan_provenance(
            [dict(id='a', scan=None, path='characters/自然现象/a.md', scanKind=None)], chars_dir)),
        ('check12 无 scan 但 scanKind 残留', lambda: check12_scan_provenance(
            [dict(id='a', scan=None, path='characters/自然现象/none.md', scanKind='obimd')], chars_dir)),
        ('check12 S6/S7 出处行并存', lambda: check12_scan_provenance(
            [dict(id='a', scan='自然现象/a.png', path='characters/自然现象/both.md', scanKind='obimd')], chars_dir)),
    ]
    failures = []
    for name, fn in cases:
        try:
            errs = fn()
        except Exception as e:  # noqa: BLE001
            failures.append('%s 抛异常：%s' % (name, e))
            continue
        if not errs:
            failures.append('%s 没抓到坏样本（护栏是摆设）' % name)
    # 反向：干净样本必须全过（glyph 指向刚造的文件）
    clean = [rec(id='a', char='日', glyph='自然现象/a.png'),
             rec(id='b', char='月', type='自然现象', char_len=1, difficulty=2, glyph='自然现象/b.png')]
    for name, fn in [('clean-check1', lambda: check1_scope(clean,
                            {'a': ('自然现象', '日'), 'b': ('自然现象', '月')})),
                     ('clean-check2', lambda: check2_id_unique(clean)),
                     ('clean-check3', lambda: check3_char(clean)),
                     ('clean-check4', lambda: check4_difficulty(clean)),
                     ('clean-check5', lambda: check5_ledger(clean)),
                     ('clean-check6', lambda: check6_copyright(clean, authors)),
                     ('clean-check7', lambda: check7_frontmatter(clean, chars_dir)),
                     ('clean-check8', lambda: check8_publicdomain(clean, authors, 2026)),
                     ('clean-check9', lambda: check9_dedup(clean, set())),
                     ('clean-check10', lambda: check10_type(clean)),
                     ('clean-check11 合法笔画放行', lambda: check11_strokes(
                         [dict(id='a', strokes=[['circle', 256, 256, 110], ['dot', 256, 256, 12]])], {'a'}, set())),
                     ('clean-check11 共图已登记放行', lambda: check11_strokes(
                         [dict(id='a', strokes=[['line', 0, 0, 100, 100]], glyph_fingerprint='fp1'),
                          dict(id='b', strokes=[['line', 0, 0, 100, 100]], glyph_fingerprint='fp1')],
                         {'a', 'b'}, {'glyph-duplicate:rendered-shapes'})),
                     # clean-check12：三级口径的三个合法形态都要放行
                     ('clean-check12 三级口径合法形态放行', lambda: check12_scan_provenance(
                         [dict(id='a', scan='自然现象/a.png', path='characters/自然现象/ok.md', scanKind='obimd'),
                          dict(id='b', scan='自然现象/b.png', path='characters/自然现象/ref.md', scanKind='ref'),
                          dict(id='c', scan=None, path='characters/自然现象/none.md', scanKind=None)], chars_dir))]:
        try:
            errs = fn()
        except Exception as e:
            failures.append('%s 干净样本抛异常：%s' % (name, e))
            continue
        if errs:
            failures.append('%s 干净样本被误报：%s' % (name, errs))
    if failures:
        print('validate.py selftest FAILED:')
        for f in failures:
            print('  - ' + f)
        return 1
    print('validate.py selftest ok（12 个坏样本全部拦下，10 个干净样本无误报）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
