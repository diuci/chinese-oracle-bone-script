# 贡献规范

## 加一个字条（L2）

1. 在 `characters/<字类>/` 下新建 `<id>.md`，字类取自合法集（自然现象 / 动植物 / 人体动作 / 器物 / 数目 / 抽象）。
2. frontmatter 必填字段一个不能少：

   ```
   id / char / char_len / type / difficulty / author / era / source / license / glyph
   ```

   - `char` 必须**单字**（`char_len: 1`）。
   - `glyph` 是甲骨形 png 相对 `characters/` 的路径（如 `自然现象/ri.png`）。
   - `source` 用 S 代号（见 `sources.md`）。
3. 正文三段：**甲骨形**（图）、**今字**、**解析**（甲骨形→部件→今字的推演链）、**出处**。
4. 生成甲骨形 png：`python tools/gen-glyphs.py`（字形定义在 `tools/gen-glyphs.py` 的 `GLYPHS`）。
   如果是 M2 起的扫描图，直接放 `characters/<字类>/<id>.png`。
5. 同步 `docs/scope.md` 的收录清单（加一行）。
6. 跑全链：

   ```
   python tools/build.py
   python tools/gen-index.py
   python tools/build-site.py
   python tools/validate.py
   node tools/check-legal.mjs
   ```

7. 确认 `git status` 干净（可复现闸门），提交。

## 解析怎么写

- 给出**甲骨形 → 部件 → 今字**的推演链，说清部件指代什么、怎么演变成今字。
- 不要写「这是 XX，所以是 XX」这种没有推演的空话。
- 不确定的字源不要编——宁可写「今字解读尚存争议」，也不要猜。

## 难度怎么标

- 1 星：直观对应，一眼可认。
- 2 星：有明显演变，需要一点字源知识。
- 3 星：差异大，需要认真看部件。
- 4–5 星：会意字、假借字、字形歧义大的字（M2 起）。

## 常见错误

- **今字写成多字词**——字库只收单字，多字词进 `pending/` 登记。
- **glyph 路径写错**——必须是相对 `characters/` 的路径，且文件存在。
- **今字重复**——同一个今字只能有一个字条；同字多解要登记 `data/known-defects.json`。
- **忘改 scope.md**——validate 第 1 项会因「多收框架外字目」而红。
