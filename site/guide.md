# 指南

本库是**甲骨文分站**（《甲骨猜字》游戏）的单一事实源。这里说明内容怎么组织、怎么消费。

## 目录即分类

`characters/` 下按**字类**分目录：自然现象 / 动植物 / 人体动作 / 器物 / 数目 / 抽象。
每个 `.md` 就是一个字，frontmatter 记今字、字类、难度、来源、版权、甲骨形图路径。
每个字旁边有同名的甲骨形 `.png`。

另有两个交叉轴：
- **难度**（`difficulty` 1–5）：用于分站筛选与玩法匹配。
- **标签**（`tags`）：主题轴（天体 / 动物 / 植物 / 人体…）。

[characters/索引](/characters/索引) 是交叉索引页，按字类 / 难度 / 今字 / 标签汇总。

## 怎么消费这份数据

- **分站**（[jiagu.diuci.com](https://jiagu.diuci.com)）读 `data/characters.json` 与甲骨形图，渲染《甲骨猜字》游戏，不直接读 md。
- 本浏览站直接渲染 `characters/**/*.md`（VitePress）。
- 甲骨形图由 `tools/gen-glyphs.py` 从笔画定义渲染（忠实复现通行甲骨形），M2 起部分换回原骨片扫描图。

## 质量门槛

收录判据见 [quality](/sources)（十条）。任何一条不满足，`tools/validate.py` 构建失败。
宁缺毋滥——空目录比低质字条更诚实。

## 变更流程

改内容后重算派生产物，全绿再提交。见 [change-process](/sources)。
