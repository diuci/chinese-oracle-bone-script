# 甲骨文项目完整计划（chinese-oracle-bone-script + jiagu-site）

> 本文档即第一阶段交付物（M0）：一份完整计划文档。
> 框架与质量要求**逐项对齐** `chinese-character-riddle/PLAN.md`（字谜），差异点集中在第 7 节。
> 后续步骤只按本计划执行，不再做设计决策。

## 0. 交付物与本次动作

- **本次交付**：本计划文档，落在内容仓 `chinese-oracle-bone-script/PLAN.md`。
- **后续**：按第 4 节里程碑推进。

## 1. 目标与成功标准

沿用 K12 的「单一事实源 + 分站」双仓结构，做甲骨文版：

| 部分 | 仓库 / 域名 | 角色 | 成功标准 |
|---|---|---|---|
| **第一部分：开源甲骨文内容库** | `diuci/chinese-oracle-bone-script` | **唯一事实源**：纯 Markdown 甲骨文字条 + 甲骨字形图（png）+ 内容工具 + 派生数据 + 可直接浏览的站点 | `validate.py` 十项全绿；CI「可复现闸门」绿；`data/characters.json` 可由 `characters/` 逐字节重算；用户可在 GitHub/Pages 直接浏览与搜索 |
| **第二部分：甲骨文分站** | `diuci/jiagu-site` → `jiagu.diuci.com` | **纯游戏站**（内容即游戏，见 §3）：《甲骨猜字》，看图猜今字，每日题 + 自由练习 | CI 各闸门绿；branch 模式部署成功 |

「质量优先、收录最完整」的**契约基准** = `docs/scope.md`：它列明收录哪些甲骨文字、每类目标字数，`validate.py` 第 1 项逐条比对，漏收/多收即失败（对应字谜的 scope 契约、K12 的 syllabus 契约）。

## 2. 内容仓 `chinese-oracle-bone-script`（第一部分）

### 2.1 目录结构（与 chinese-character-riddle 同构，外加图形）

```
chinese-oracle-bone-script/
├── characters/                   # 内容（唯一事实源，手写 md + 甲骨形 png）
│   ├── 自然现象/  动植物/  人体动作/  器物/  数目/  抽象/   # 主分类：按字类（§2.5 合法集）
│   │     （每字一个 md + 同名甲骨形 png）
│   └── 索引.md                    # 生成：按字类/难度/今字交叉索引（gen-index.py）
├── data/                         # 构建产物（勿手改）
│   ├── characters.json           # build.py 编译，分站与玩法的唯一数据源
│   ├── checksums.json            # md 与 png 的内容哈希
│   ├── authors.json              # 现代释义作者卒年总表（公版核验用）
│   └── known-defects.json        # 今字异读/多解登记
├── docs/                         # 契约文档
│   ├── scope.md                 # ★ 收录范围契约（「最完整」的基准）
│   ├── sources.md               # 数据来源与许可（S1–S5 代号说明）
│   ├── quality.md               # 质量门槛（收录判据，见 §2.3）
│   ├── change-process.md        # 内容冻结后的变更流程
│   └── contributing.md          # 贡献规范
├── tools/                        # 零依赖，纯 Python 标准库（+check-legal.mjs）
│   ├── gen-glyphs.py            # 笔画定义 → 甲骨形 png（无扫描图时的兜底渲染）
│   ├── build.py                 # Markdown → characters.json + checksums.json（含图哈希）
│   ├── validate.py              # 十项校验（见 §2.4），支持 --selftest
│   ├── gen-index.py             # 生成 characters/索引.md
│   ├── build-site.py            # 生成浏览站站点副本
│   ├── fm.py                    # frontmatter 解析（共用）
│   └── check-legal.mjs          # 法律护栏（绝对化表述、许可证、联系入口）
├── pending/                      # ⏸ 保护期内 / 版权未确认的现代释义
│   └── INDEX.md
├── site/                         # VitePress 浏览站（用户可直接浏览 markdown）
├── .github/workflows/verify.yml  # CI：自检 → 离线检查 → 派生产物重算 → 可复现闸门
├── PROVENANCE.md                 # 版权台账（汇总视图）
├── README.md
├── LICENSE
└── PLAN.md                       # 本文档
```

> 本仓**只管内容**：分站代码在 `jiagu-site`。注意与 zimi 的分歧：甲骨文分站是游戏站，
> 读的是**快照**而非 CI clone（同 lian/handle），见 §3。

### 2.2 条目标式（每字一个 md，frontmatter + 正文）

```markdown
---
id: ri                          # 稳定标识（今字拼音 slug），联机/游戏引用用
char: 日                       # 今字（对应字谜的 answer；甲骨形是「谜面」）
char_len: 1                   # 今字字数，必须为 1（单字）
type: 自然现象                 # 字类（主分类，见 §2.5 合法集）
subtype: 天体                  # 可选细分类
difficulty: 1                 # 1–5
author: 佚名                  # 现代释义作者；古典匿名记「佚名」
era: 商                      # 时代（甲骨 = 商代晚期）或「当代」（现代释义）
source: S1                    # 来源台账代号（如《甲骨文合集》版号）
license: public-domain
copyright: { text: public-domain, annotations: cc-by-4.0 }
glyph: 自然现象/ri.png         # 甲骨字形图路径
tags: [太阳, 天体]
---

# 日

> 自然现象类 · 商 · 难度 ★

**甲骨形**：![](自然现象/ri.png)
**今字**：日

## 解析
甲骨文的「日」作圆形，中间一点，指日之中心，是典型的象形字。
字形从圆到方，随书写习惯演变，至楷书定为「日」。

## 出处
《甲骨文合集》第 X 版（S1）。
```

**字段说明**：`char`/`char_len` 是「谜底」等价物（单字）；`glyph` 是「谜面」等价物（图）；`type` 决定目录归属；`difficulty` 用于分站难度轴与玩法匹配；`author`/`era`+`license` 支撑公版核验；`source` 是来源台账，无来源即不收；`tags` 支撑主题轴。`data/characters.json` 完整序列化全部字段。

### 2.3 收录判据（质量门槛，「质量差的不要收入」）

`validate.py` 强制，任一不满足即失败：

1. **唯一今字**——今字解读明确、无歧义；歧义/多解剔除或登记 `known-defects.json`。
2. **解析完备**——每字必须有「解析」段（甲骨形 → 部件 → 今字的推演链），不能只给今字。
3. **来源可溯**——`source` 必填，无来源孤字不收。
4. **无重复**——今字全库唯一（同字不同解须登记，否则拒收）。
5. **无低质内容**——低俗、歧义、政治敏感、无法核实的「民间字源」一律拒收（`check-legal.mjs` 与人工审核共同把关）。
6. **难度评级**——`difficulty` 必填且在 1–5。
7. **公版安全**——甲骨卜辞本身（商代）= 公版；现代释义须署名且卒年 ≤ 当前年 − 50，或来源确证/已授权，否则进 `pending/`。
8. **字类合法**——`type` 必须取自合法集（§2.5）。
9. **图形完备**——`glyph` 路径存在、非空、哈希入 `checksums.json`（图也是唯一事实源的一部分）。
10. **单字约束**——`char` 必须单字（`char_len=1`），多字词不进字库（可进 `pending/` 登记）。

### 2.4 校验（`tools/validate.py`，十项，`--selftest` 用坏样本证明护栏真拦得住）

| # | 检查 | 失败示例 |
|---|------|---------|
| 1 | 收录范围完整性 | `scope.md` 契约要求收录却缺失 / 多收框架外来源 |
| 2 | id 唯一性 | 两字共用一个 id |
| 3 | 今字字段 | `char` 缺失 / 空 / 非单字 / 字数与 `char_len` 不符 |
| 4 | 难度合法 | `difficulty` 不在 1–5 |
| 5 | 台账完整 | 缺 `source` / `license` |
| 6 | 版权核验 | `license=cc-by-4.0` 的现代释义混入 `characters/` 却非我方原创（ours=true） |
| 7 | frontmatter | 必填字段缺失（含 `glyph`） |
| 8 | 公版证据 | 现代释义作者卒年晚于「当前年 − 50」，或缺 `author`/`era` |
| 9 | 去重 | 今字全库重复未登记 |
| 10 | 字类合法 | `type` 不在合法集 |

### 2.5 分门别类（分类轴）

- **主分类（目录，按字类）**：`自然现象` `动植物` `人体动作` `器物` `数目` `抽象`。合法集即 `validate.py` 第 10 项。
- **难度轴**：`difficulty` 1–5。
- **今字轴**：按今字索引（`gen-index.py` 生成，「某个今字的所有甲骨形/异写」）。
- **主题轴**：`tags`（天体、动物、植物、人体、器物、抽象…）。
- **时代轴**：`era`（商 / 当代）。
- `characters/索引.md` 汇总交叉索引，浏览站首页按**字类×难度×今字**三轴筛选。

### 2.6 数据来源与版权（`docs/sources.md`，S 代号台账）

| 代号 | 来源 | 许可 | 用途 |
|---|---|---|---|
| S1 | 《甲骨文合集》（文物出版社 1978–1998，版号） | 公有领域（商代卜辞） | 甲骨形与版号初稿、今字解读 |
| S2 | 《甲骨文字典》开放数据 / 学术机构甲骨字典开放资源 | 公有领域 | 交叉比对、补漏 |
| S3 | 汉典（zdic）等开放收藏 | 以各自许可为准 | 交叉比对、补漏 |
| S4 | 当代高质量释义（来源确证或已授权） | CC BY 4.0 / 授权 | 现代释义文本 |
| S5 | 商业站点 | 版权 | **仅比对用字，不复制** |

**公版规则**（与 K12 / 字谜完全一致）：判定只有一条——作者卒年 ≤ 当前年 − 50。
甲骨卜辞（商代）天然公版；现代释义作者记 `author` + `authors.json` 卒年。
`validate.py` 第 8 项逐篇核验，不满足即构建失败。仍在保护期的现代释义进 `pending/`，只登记不收录。

### 2.7 内容仓 CI（`.github/workflows/verify.yml`，同字谜/K12）

1. **检查器自检**：`validate.py --selftest`、`build.py --selftest`、`gen-index.py --selftest`、`build-site.py --selftest`、`gen-glyphs.py --selftest`、`check-legal.mjs --selftest`。
2. **离线检查**：`validate.py`、`build.py` 全跑。
3. **派生产物重算与审计**：`gen-index.py`、`build-site.py`、`gen-glyphs.py`，`check-legal.mjs`。
4. **可复现闸门**：跑完 `git status` 必须干净——提交的产物（含字形 png）必须是链条跑出来的，不是手改的。

### 2.8 内容仓浏览站（`site/`，VitePress）

用户**直接浏览**的入口（对应字谜的 `site/`）：

| 页面 | 内容 |
|---|---|
| `/` | 全部字总览，按**字类 / 难度 / 今字**三轴筛选 |
| `/characters/<字类>/<slug>` | 单字页：甲骨形图 + 今字 + 解析 + 出处 |
| `/print` | A4 打印版 |
| `/sources` | 数据来源与版权 |
| `/guide` | 指南 |

本地：`python tools/build.py && python tools/gen-index.py && python tools/build-site.py && npm run dev`；内置 minisearch 中文按字切分。部署到 GitHub Pages（项目页或子域）。

## 3. 分站 `jiagu-site`（第二部分，**游戏站**）

与 `lian-site` / `handle-site` **同构**（**不是**与 zimi-site 同构——那是纯浏览站），只存放呈现层，内容全部来自 `chinese-oracle-bone-script` 的**快照**，CI 不 clone 内容仓。

```
jiagu-site/
├── src/                           # Vue 3 + Vite + UnoCSS（presetWind3，dark 走 class）
│   ├── data/corpus.json           # 【快照】sync-corpus.mjs 生成，随分站提交
│   ├── logic/daily.mjs            # 每日选字与种子（同一天所有人同字）
│   ├── logic/game.ts              # 玩法规则：生成 4 选 1 候选、判定
│   ├── logic/store.ts             # 状态
│   └── components/ …              # 游戏视图
├── tools/
│   ├── sync-corpus.mjs            # 从 CONTENT_ROOT 抽快照（--check 漂移，--selftest）
│   ├── check-puzzle.mjs           # 全量盘面生成 + 校验（--selftest）
│   ├── check-legal.mjs            # 法律护栏（--selftest）
│   ├── check-build.mjs            # 产物齐备 + 色值（--selftest）
│   ├── check-ui.mjs               # UI 闸门（--selftest）
│   └── smoke.mjs                  # 真开浏览器跑通当日题（--selftest）
├── .github/workflows/verify-deploy.yml  # branch 模式锚点校验（同 _deploy，不碰发布）
├── package.json                   # npm（非 pnpm），Node >= 20，Vitesse Lite 骨架
└── README.md
```

**玩法：《甲骨猜字》**（看图猜今字）

- **核心**：给一张甲骨字形图，提示「这是哪个现代汉字？」，**四选一**（候选含正确今字 + 三个干扰字，干扰字不与答案重复、不为空）。答完给反馈 + 字源解析（为什么长这样、部件怎么演变）。
- **每日题**：同一天所有人同字（`日期 → 词库第几字`，种子确定性）。历史冻结：已发出去的日期逐日记下是哪一字；词库勘误之后回放改用改过的，并在 `history.retexted` 留痕；消失的篇目标 `ghost`。——直接复用 `lian-site` 的快照 + 每日题历史冻结机制（`corpus.json` 带 `contentVersion`、来源 sha256、`history.days`）。
- **自由练习**：按字类 × 难度筛选，不限次数，连击计分。
- **数据流**：`jiagu-site` 只读内容仓快照（单向、按需取字段），不读其他分站。`sync-corpus.mjs` 抽 `characters.json` + 甲骨形图 → `src/data/corpus.json`（带 `contentVersion`、sha256、跳过清单）。更新快照是显式动作：`npm run sync:corpus` → 看 diff → 提交。

**部署**：branch 模式（`git push` 即发布，K12 除外——用户偏好），自定义域 `jiagu.diuci.com`，`CNAME` + `.nojekyll`，`verify-deploy.yml` 锚点校验（同 `_deploy`）。移动端底部标签栏：首页 / 每日 / 练习 / 关于，视觉与主站 / K12 对齐（宣纸色 `--paper #f4ede0`、朱砂等语义色）。

## 4. 里程碑

| 里程碑 | 内容 | 出口标准 |
|---|---|---|
| **M0（本次）** | 完整计划文档 `PLAN.md` | 用户批准 |
| **M1** | 内容仓骨架：目录、frontmatter 格式、工具链（gen-glyphs/build/validate/gen-index/build-site/fm/check-legal）、CI 绿、种子字若干（12 字，覆盖各字类：日、月、山、水、火、马、牛、木、竹、人、手、目，每字带甲骨形图） | `validate.py` 全绿；CI 可复现闸门绿；`characters.json` 可复算 |
| **M2** | 内容扩充到「最完整」：系统性收录 S1–S4，达成 `docs/scope.md` 契约（目标 50–100 个最常见甲骨文字） | 第 1 项校验通过；`PROVENANCE.md` 台账齐全 |
| **M3** | 内容仓浏览站（VitePress）上线，可直接浏览 | 三轴筛选可用；`/print` 可打印 |
| **M4** | `jiagu-site` 分站 + 《甲骨猜字》游戏 + 部署 `jiagu.diuci.com` | 各闸门绿；branch 模式部署成功 |

> 与字谜的差异：字谜分站玩法**后置**（M5），甲骨文分站**内容即游戏**（用户明确要求「内容是相关游戏」），故 M4 直接交付游戏站，无「后置玩法」一说。

## 5. 验收标准（整体）

- `python tools/validate.py` 十项全绿；`--selftest` 证明每项护栏抓得住坏样本。
- CI「可复现闸门」绿：提交的 `data/` 与 `索引.md` 与链条重算逐字节一致（含图片哈希）。
- `data/characters.json` 是分站与后续玩法的**唯一数据源**，可由 `characters/` 完整复算。
- 内容仓浏览站与 `jiagu-site` 均可正常浏览、搜索、打印（浏览站）/ 可玩（分站）。
- 公版证据逐篇可核验，`pending/` 与 `PROVENANCE.md` 台账完整。
- 分站产物体检（空正文/法律/UI/字号）全绿，部署到 `jiagu.diuci.com` 成功。

## 6. 执行顺序（批准后）

1. 建 `chinese-oracle-bone-script/` 文件夹，写入本计划文档 `PLAN.md`（即本文件）。
2. 按 M1 初始化内容仓骨架与工具链，使 CI 可跑绿。
3. M2 扩充内容、M3 浏览站、M4 分站游戏与部署。

## 7. 与字谜的关键差异（决策记录）

1. **内容单位**：每字一条 md（甲骨形 → 今字 + 解析），不是谜目；「谜面」= 甲骨形图，「谜底」= 今字（单字）。
2. **分站点**：游戏站（同构 `lian-site`/`handle-site`），**不是** VitePress 浏览站（同构 zimi/k12）——用户要求「内容是相关游戏」。
3. **分站内容**：快照制（`sync-corpus.mjs`），**不是** CI clone 内容仓（同 lian/handle）；部署 branch 模式，`git push` 即发布（同 handle/lian/主站）。
4. **图形入事实源**：甲骨形 png 放 `characters/` 下，哈希进 `checksums.json`，CI 闸门覆盖图片字节。种子字形由 `tools/gen-glyphs.py` 从笔画定义渲染（忠实复现通行甲骨形）；M2 起部分换回原骨片扫描图（S1/S2），两路产物都进 checksums。
5. **去重判据**：今字全库唯一（按字去重，非按谜面去重）。
6. **时代轴**：商（甲骨）/ 当代（现代释义）。
7. **命名**：内容仓 `chinese-oracle-bone-script`；分站 `jiagu-site` → `jiagu.diuci.com`；游戏产品名《甲骨猜字》。
8. **字类合法集**：自然现象 / 动植物 / 人体动作 / 器物 / 数目 / 抽象（对应字谜的谜种合法集）。
