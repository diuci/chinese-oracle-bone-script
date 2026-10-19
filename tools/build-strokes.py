"""把今字的笔画数挂到 characters.json 上。

为什么需要：四选一玩法的干扰项应当是「形近字」——笔画数相同、同字类，
这样孩子只能靠字形判断，不能靠「这字我见过/没见过」排除。
原实现按 id 字典序取前三个，恒定是「㐭 㛸 㜽」三个扩展区生僻字，
既不形近也不常见，孩子无从下手（实测最近 365 天里 177 天如此）。

笔画数来自 Unihan_IRGSources.txt 的 kTotalStrokes（Unicode 官方数据）。
优先读 k12 内容仓的本地缓存 Unihan.zip；读不到就留 None，
由 validate.py 报警 —— 不在这里悄悄编一个数。
"""
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UNIHAN = ROOT.parent / 'k12-chinese-poetry' / 'data' / 'unihan' / 'Unihan.zip'
SRC = 'Unihan_IRGSources.txt'


def load_stroke_counts(path: Path):
    """读 Unihan 的 kTotalStrokes，返回 {字: 笔画数}。"""
    if not path.exists():
        return None
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        name = next((n for n in names if n.endswith(SRC)), None)
        if name is None:
            return None
        raw = z.read(name).decode('utf-8')
    out = {}
    for line in raw.splitlines():
        if line.startswith('#') or not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) < 3 or parts[1] != 'kTotalStrokes':
            continue
        try:
            cp = int(parts[0][2:], 16)
            out[chr(cp)] = int(parts[2].split()[0])
        except (ValueError, IndexError):
            continue
    return out


def main():
    counts = load_stroke_counts(UNIHAN)
    data_path = ROOT / 'data' / 'characters.json'
    data = json.loads(data_path.read_text(encoding='utf-8'))

    missing = []
    if counts:
        for c in data['chars']:
            n = counts.get(c['char'])
            c['stroke_count'] = n
            if n is None:
                missing.append(c['char'])
    else:
        for c in data['chars']:
            c['stroke_count'] = None

    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    got = sum(1 for c in data['chars'] if c.get('stroke_count'))
    print(f'[build] 今字笔画数：{got}/{len(data["chars"])} 字有（来源 Unihan kTotalStrokes）')
    if counts is None:
        print('[build] ⚠ 读不到本地 Unihan 缓存，笔画数留空。干扰项会退回 id 排序')
    elif missing:
        print(f'[build] ⚠ {len(missing)} 字查不到笔画数：{missing[:10]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())