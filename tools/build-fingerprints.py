"""把 GLYPHS 里的图元算成指纹，挂到 characters.json 的每一字上。

为什么需要：现在 261 字里有 143 字与其他字共用同一组图元（其中「人冠」一组
就有 122 字）。四选一玩法若把同图元的字选成干扰项，玩家看到一张图却有两个
「正确答案」—— 那一道题无解。游戏站需要知道两个字是否同形，才能避开。

指纹取图元元组的 repr，不取 PNG 的字节和：PNG 可能被重新压缩而图元没变。
"""
import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_glyphs(root: Path):
    """只取 gen-glyphs.py 里的 GLYPHS 字面量，不执行它的绘制逻辑。"""
    src = (root / 'tools' / 'gen-glyphs.py').read_text(encoding='utf-8')
    m = re.search(r'^GLYPHS = \{', src, re.M)
    if not m:
        return {}
    end = src.index('\n}', m.start())
    ns: dict = {}
    exec(src[m.start():end + 2], ns)   # noqa: S102 —— 只取字面量，不碰绘图
    return ns.get('GLYPHS') or {}


def fingerprints(glyphs):
    """id -> 指纹（16 位十六进制）。没有图元的字返回 None。"""
    out = {}
    for gid, entry in glyphs.items():
        _type, prims = entry
        # repr 保证顺序与类型都参与哈希：换顺序、换图元类型 → 指纹不同
        raw = repr(list(prims))
        out[gid] = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]
    return out


def main():
    root = Path(__file__).resolve().parent.parent
    glyphs = load_glyphs(root)
    fps = fingerprints(glyphs)

    # 自检：抽两字确认同形与不同形都能分出来
    assert fps, 'GLYPHS 是空的'

    import json
    data_path = root / 'data' / 'characters.json'
    data = json.loads(data_path.read_text(encoding='utf-8'))

    missing = []
    for c in data['chars']:
        fp = fps.get(c['id'])
        if fp:
            c['glyph_fingerprint'] = fp
        else:
            c['glyph_fingerprint'] = None
            missing.append(c['id'])

    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    groups = {}
    for c in data['chars']:
        fp = c.get('glyph_fingerprint')
        if fp:
            groups.setdefault(fp, []).append(c['char'])
    dup = {k: v for k, v in groups.items() if len(v) > 1}

    print(f'[build] 字形指纹：{len(fps)} 个 id 有图元，{len(groups)} 组不同指纹')
    print(f'[build] 其中 {len(dup)} 组是多字共用（同形），共 {sum(len(v) for v in dup.values())} 字')
    if missing:
        print(f'[build] ⚠ {len(missing)} 个字在 GLYPHS 里没有图元：{missing[:10]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())