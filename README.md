# 甲骨文内容库（chinese-oracle-bone-script）

开源甲骨文 Markdown 内容库，是「丢词夺理」生态的内容仓之一。
每字一条 Markdown（甲骨形图 + 今字 + 字源解析 + 出处），是分站游戏《甲骨猜字》的唯一事实源。

## 这是什么

- **单一事实源**：`characters/` 下的 Markdown + 甲骨形 png，人读机读同一份。
- **机读数据**：`data/characters.json` 由 `tools/build.py` 编译，分站与玩法只读它。
- **可执行契约**：`docs/scope.md` 是收录清单，`tools/validate.py` 第 1 项逐条比对。
- **十项校验**：`tools/validate.py` 强制质量门槛，任一不满足即构建失败。
- **可复现闸门**：CI 重算 `data/`、索引、站点副本、字形 png，与提交进去的逐字节比对。

## 快速开始

```bash
# 跑校验（10 项）
python tools/validate.py

# 重算机读数据 + 索引 + 站点副本
python tools/build.py
python tools/gen-index.py
python tools/build-site.py

# 渲染甲骨形 png（字形定义在 tools/gen-glyphs.py）
python tools/gen-glyphs.py

# 法律护栏
node tools/check-legal.mjs
```

## 目录

```
characters/    内容（唯一事实源）：每字一个 md + 同名甲骨形 png
data/          构建产物（勿手改）：characters.json / checksums.json / authors.json / known-defects.json
docs/          契约文档：scope / sources / quality / change-process / contributing
tools/         零依赖工具链：gen-glyphs / build / validate / gen-index / build-site / fm / check-legal
pending/       保护期内 / 版权未确认的字条（只登记不收录）
site/          VitePress 浏览站（可直接浏览 markdown）
```

## 许可

- 甲骨卜辞原文：公有领域（商代）。
- 现代释义 / 字源解说：见各字条 `copyright` 字段，多为 `annotations: cc-by-4.0`。
- 代码与工具：见 `LICENSE`。
- 侵权联系：hi@diuci.com。我们不做「万无一失」的担保，只把每个字的依据摆出来。

## 与字谜仓的关系

本仓与 `chinese-character-riddle`（字谜）同构，框架与质量门槛逐项对齐。
差异见 `PLAN.md` §7。本仓是分站 `jiagu-site`（《甲骨猜字》游戏）的内容来源。
